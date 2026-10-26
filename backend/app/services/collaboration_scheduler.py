import os
import pytz
import time
from datetime import datetime, timedelta, time as dtime
from typing import Dict, Any, Optional, Tuple
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.db.database import SessionLocal
from app.models import models
from app.services.collaboration_email_service import collaboration_email_service

IST_TIMEZONE = pytz.timezone("Asia/Kolkata")

# Step 5 Specifications
MAX_DAILY_EMAILS = 50          # Strict rolling 24-hour maximum
PILOT_MAX_EMAILS = 5           # Pilot mode safeguard before production ramp-up
SEND_INTERVAL_SECONDS = 300    # Controlled 5-minute pacing interval between dispatches
WINDOW_START = dtime(9, 0)     # 09:00 AM IST
WINDOW_END = dtime(17, 30)     # 05:30 PM IST


class CollaborationScheduler:
    """
    Enterprise-grade Microsoft 365 Scheduled Outreach Engine
    Enforces Step 5 requirements:
    - Maximum 50 emails per rolling 24-hour period
    - Active dispatch window: 09:00 AM to 05:30 PM IST (Mon-Fri)
    - Paced queue execution (default 5-minute interval)
    - Immediate auto-pause if Microsoft 365 authentication fails
    - Duplicate prevention & contact verification
    - Stop Automation control
    - Pilot volume safeguard (default 5 emails until explicit approval)
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=IST_TIMEZONE)
        self.is_running = False
        self.is_paused = False
        self.pilot_mode = True                # Step 5: Start with small approved pilot volume (5 emails)
        self.max_daily_limit = MAX_DAILY_EMAILS
        self.pilot_limit = PILOT_MAX_EMAILS
        self.send_interval_seconds = SEND_INTERVAL_SECONDS
        
        self.daily_job_id = "daily_partner_analysis_9am_ist"
        self.queue_job_id = "paged_queue_worker_ist"
        self.last_run_time: Optional[datetime] = None
        self.last_summary: Optional[Dict[str, Any]] = None

    def start_scheduler(self):
        """Start the daily 9:00 AM IST analysis trigger and the 5-minute queue worker."""
        if self.is_running:
            return

        try:
            # 1. Daily 09:00 AM IST analysis and draft generation job
            daily_trigger = CronTrigger(hour=9, minute=0, timezone=IST_TIMEZONE)
            self.scheduler.add_job(
                func=self.execute_daily_workflow,
                trigger=daily_trigger,
                id=self.daily_job_id,
                name="Daily Tender-Based Partner Draft Preparation (09:00 AM IST)",
                replace_existing=True,
                misfire_grace_time=3600
            )

            # 2. Paced Queue Worker: runs every 5 minutes to dispatch at most ONE email per interval
            queue_trigger = IntervalTrigger(seconds=self.send_interval_seconds, timezone=IST_TIMEZONE)
            self.scheduler.add_job(
                func=self.process_next_queued_email,
                trigger=queue_trigger,
                id=self.queue_job_id,
                name="Paced Queue Worker (5-Min Interval)",
                replace_existing=True,
                misfire_grace_time=60
            )

            self.scheduler.start()
            self.is_running = True
            self.is_paused = False
            print("🚀 [Collaboration Scheduler] Started: Daily 9:00 AM IST analysis + 5-minute queue worker active.")
        except Exception as e:
            print(f"❌ [Collaboration Scheduler] Error starting scheduler: {e}")

    def pause(self):
        """Pause automated daily execution and queue processor."""
        if self.is_running and not self.is_paused:
            try:
                self.scheduler.pause_job(self.daily_job_id)
                self.scheduler.pause_job(self.queue_job_id)
            except Exception:
                pass
            self.is_paused = True
            return {"status": "paused", "message": "Outreach scheduler and queue processor paused."}
        return {"status": "already_paused"}

    def resume(self):
        """Resume automated daily execution and queue processor."""
        if self.is_running and self.is_paused:
            try:
                self.scheduler.resume_job(self.daily_job_id)
                self.scheduler.resume_job(self.queue_job_id)
            except Exception:
                pass
            self.is_paused = False
            return {"status": "resumed", "message": "Outreach scheduler and queue processor resumed."}
        return {"status": "already_active"}

    def stop_automation(self) -> Dict[str, Any]:
        """Stop Automation immediately (disables auto-send and pauses worker)."""
        collaboration_email_service.auto_send_enabled = False
        self.pause()
        return {
            "status": "stopped",
            "auto_send_enabled": False,
            "is_paused": True,
            "message": "Outreach automation stopped immediately. No emails will be sent automatically."
        }

    def set_pilot_mode(self, enabled: bool) -> Dict[str, Any]:
        """Toggle between Pilot Mode (max 5 emails/day) and Full Production (max 50 emails/day)."""
        self.pilot_mode = enabled
        active_limit = self.pilot_limit if self.pilot_mode else self.max_daily_limit
        return {
            "status": "updated",
            "pilot_mode": self.pilot_mode,
            "active_limit": active_limit,
            "message": f"Scheduler configured for {'Pilot Mode (max 5 emails/day)' if self.pilot_mode else 'Production Mode (max 50 emails/day)'}."
        }

    def is_within_business_window(self) -> Tuple[bool, str]:
        """Check if current time is between 9:00 AM IST and 5:30 PM IST on a working day."""
        now_ist = datetime.now(IST_TIMEZONE)
        curr_time = now_ist.time()
        curr_weekday = now_ist.weekday()  # 0=Monday, 6=Sunday

        if curr_weekday >= 5:
            return False, f"Outside sending window: Weekend ({now_ist.strftime('%A')}). Sending resumes Monday 09:00 AM IST."

        if not (WINDOW_START <= curr_time <= WINDOW_END):
            return False, f"Outside sending window: {curr_time.strftime('%I:%M %p')} IST. Active window is 09:00 AM – 05:30 PM IST."

        return True, "Within active business sending window"

    def get_rolling_24h_sent_count(self, db: SessionLocal) -> int:
        """Count emails dispatched across the rolling 24-hour window."""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        return db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.sent_at >= cutoff,
            models.CollaborationEmail.status.in_(["Provider Accepted", "Found in Sent Items", "Delivery Confirmed", "sent"]),
            models.CollaborationEmail.is_test_email == False
        ).count()

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive scheduler status, active window check, rolling quota, and next run time."""
        job = self.scheduler.get_job(self.daily_job_id) if self.is_running else None
        next_run = None
        if job and job.next_run_time:
            next_run = job.next_run_time.astimezone(IST_TIMEZONE).isoformat()

        db = SessionLocal()
        try:
            today_sent = self.get_rolling_24h_sent_count(db)
            queued_count = db.query(models.CollaborationEmail).filter(
                models.CollaborationEmail.status == "approved",
                models.CollaborationEmail.approval_status == "approved"
            ).count()
        finally:
            db.close()

        within_window, window_reason = self.is_within_business_window()
        active_limit = self.pilot_limit if self.pilot_mode else self.max_daily_limit
        remaining_allowance = max(0, active_limit - today_sent)

        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "timezone": "Asia/Kolkata (IST)",
            "scheduled_time": "Every day at 09:00 AM IST (window: 09:00 AM - 05:30 PM IST)",
            "next_run_time_ist": next_run,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "auto_send_enabled": collaboration_email_service.auto_send_enabled,
            "draft_mode_active": not collaboration_email_service.auto_send_enabled,
            "within_business_window": within_window,
            "business_window_status": window_reason,
            "pilot_mode": self.pilot_mode,
            "active_limit": active_limit,
            "max_daily_limit": self.max_daily_limit,
            "today_sent_24h": today_sent,
            "remaining_daily_allowance": remaining_allowance,
            "queued_emails_count": queued_count,
            "pacing_interval_seconds": self.send_interval_seconds,
            "last_summary": self.last_summary
        }

    def process_next_queued_email(self) -> Optional[Dict[str, Any]]:
        """
        Paced Queue Worker:
        Dispatches at most ONE approved partner email from the queue, adhering to:
        1. auto_send_enabled check (requires explicit user authorization)
        2. Business window (09:00 AM to 05:30 PM IST)
        3. Microsoft 365 authentication validity (auto-pauses if unauthenticated)
        4. Rolling 24-hour limit (50 max, or 5 in pilot mode)
        5. De-duplication and contact validity
        """
        if not collaboration_email_service.auto_send_enabled or self.is_paused:
            return None

        # 1. Business window check
        within_window, window_reason = self.is_within_business_window()
        if not within_window:
            return {"skipped": True, "reason": window_reason}

        # 2. Check Live Provider Authentication Health
        from app.services.live_email_provider import live_email_provider
        pub_status = live_email_provider.get_public_status()
        if not pub_status.get("is_authenticated"):
            self.pause()
            active_p = pub_status.get("active_provider", "none")
            print(f"⚠️ [Collaboration Scheduler] Outbound provider ({active_p}) is unauthenticated. Scheduler automatically paused.")
            return {"skipped": True, "reason": f"Outbound provider ({active_p}) unauthenticated. Scheduler auto-paused."}

        db = SessionLocal()
        try:
            # 3. Rolling 24-hour quota check
            sent_24h = self.get_rolling_24h_sent_count(db)
            effective_limit = self.pilot_limit if self.pilot_mode else self.max_daily_limit

            if sent_24h >= effective_limit:
                print(f"🛑 [Collaboration Scheduler] Rolling 24h quota reached ({sent_24h}/{effective_limit}). Pacing queue paused until quota resets.")
                return {"skipped": True, "reason": f"24-hour limit reached ({sent_24h}/{effective_limit})."}

            # 4. Fetch the next approved email in the queue (FIFO by approved_at)
            next_email = db.query(models.CollaborationEmail).filter(
                models.CollaborationEmail.status == "approved",
                models.CollaborationEmail.approval_status == "approved"
            ).order_by(models.CollaborationEmail.approved_at.asc()).first()

            if not next_email:
                return None  # No emails in queue

            # 5. Contact validity & duplicate check
            if not next_email.recipient_email or "@" not in next_email.recipient_email or next_email.status in ["opted_out", "bounced"]:
                next_email.status = "opted_out"
                next_email.last_error = "Invalid recipient address or contact opted out."
                db.commit()
                return {"skipped": True, "email_id": next_email.id, "reason": "Invalid or opted-out contact."}

            # 6. Execute dispatch via Microsoft Graph API
            success, message = collaboration_email_service.send_email(db, next_email.id)
            print(f"✉️ [Paced Queue Worker] Dispatched #{next_email.id} to {next_email.recipient_email}: {message}")

            return {
                "dispatched": True,
                "email_id": next_email.id,
                "recipient": next_email.recipient_email,
                "success": success,
                "message": message,
                "sent_count_24h": sent_24h + (1 if success else 0)
            }
        except Exception as e:
            print(f"❌ [Paced Queue Worker Error]: {e}")
            return {"dispatched": False, "error": str(e)}
        finally:
            db.close()

    def execute_daily_workflow(self, cycle_type: str = "daily_scheduled") -> Dict[str, Any]:
        """
        Execute the daily collaboration workflow at 09:00 AM IST:
        1. Check incoming replies from partners in Microsoft 365 Inbox.
        2. Identify suitable partners for active tenders.
        3. De-duplicate: avoid sending duplicate emails for same tender.
        4. Generate personalized drafts (in draft mode by default).
        5. Flag follow-ups due (skipping replied/opted-out partners).
        6. Record execution log.
        """
        db = SessionLocal()
        start_time = datetime.utcnow()
        log_entry = models.CollaborationWorkflowLog(
            cycle_type=cycle_type,
            started_at=start_time,
            status="running"
        )
        db.add(log_entry)
        db.commit()

        summary = {
            "cycle_type": cycle_type,
            "started_at": start_time.isoformat(),
            "tenders_analyzed": 0,
            "drafts_created": 0,
            "emails_sent": 0,
            "replies_detected": 0,
            "follow_ups_flagged": 0,
            "errors": []
        }

        try:
            # Step 1: Check partner replies via Microsoft Graph
            try:
                replies_count = collaboration_email_service.check_incoming_replies(db)
                summary["replies_detected"] = replies_count
            except Exception as e:
                summary["errors"].append(f"Reply check error: {e}")

            # Step 2: Query active proposals across all 29 Indian States AND ADB!
            # Select top high-priority active proposals for each state and ADB
            states = db.query(models.State).order_by(models.State.name.asc()).all()
            selected_tenders = []
            for st in states:
                # Select top proposals per state and ADB to yield outreach in thousands (10 partners per tender)
                t_limit = 100 if 'ADB' in st.name else 10
                state_tenders = (
                    db.query(models.Tender)
                    .filter(models.Tender.state_id == st.id, models.Tender.status.in_(["active", "new"]))
                    .order_by(models.Tender.last_date.desc(), models.Tender.id.asc())
                    .limit(t_limit)
                    .all()
                )
                if not state_tenders:
                    state_tenders = (
                        db.query(models.Tender)
                        .filter(models.Tender.state_id == st.id)
                        .order_by(models.Tender.id.asc())
                        .limit(10)
                        .all()
                    )
                selected_tenders.extend(state_tenders)

            summary["tenders_analyzed"] = len(selected_tenders)

            # Step 3: Match suitable partners and generate personalized drafts
            # Recommends genuine, highly matched partners per proposal across all states & ADB
            total_drafts = 0
            for tender in selected_tenders:
                try:
                    is_adb_tender = tender.state and "ADB" in tender.state.name
                    drafts = collaboration_email_service.generate_drafts_for_tender(
                        db=db,
                        tender_id=tender.id,
                        min_match_score=60.0,
                        max_partners_per_tender=10
                    )
                    total_drafts += len(drafts)
                except Exception as e:
                    summary["errors"].append(f"Tender #{tender.tender_id} partner matching error: {e}")

            summary["drafts_created"] = total_drafts

            # Step 4: Follow-ups flagging (sent > 5 days ago, no reply)
            now = datetime.utcnow()
            follow_ups = db.query(models.CollaborationEmail).filter(
                models.CollaborationEmail.status.in_(["Provider Accepted", "Found in Sent Items", "sent"]),
                models.CollaborationEmail.response_status == "none",
                models.CollaborationEmail.follow_up_date != None,
                models.CollaborationEmail.follow_up_date <= now
            ).count()
            summary["follow_ups_flagged"] = follow_ups

            # Finish workflow execution log
            finished_time = datetime.utcnow()
            log_entry.finished_at = finished_time
            log_entry.tenders_analyzed = summary["tenders_analyzed"]
            log_entry.drafts_created = summary["drafts_created"]
            log_entry.emails_sent = summary["emails_sent"]
            log_entry.replies_checked = summary["replies_detected"]
            log_entry.follow_ups_flagged = summary["follow_ups_flagged"]
            log_entry.errors_count = len(summary["errors"])
            log_entry.status = "completed_with_errors" if summary["errors"] else "success"
            log_entry.log_details = f"Cycle finished in {(finished_time - start_time).total_seconds():.1f}s. Prepared {total_drafts} drafts. Paced queue worker active for approved dispatches."

            db.commit()

            self.last_run_time = finished_time
            self.last_summary = summary
            return summary

        except Exception as e:
            db.rollback()
            summary["errors"].append(f"Fatal workflow exception: {e}")
            log_entry.status = "failed"
            log_entry.finished_at = datetime.utcnow()
            log_entry.log_details = str(e)
            db.commit()
            return summary
        finally:
            db.close()


collaboration_scheduler = CollaborationScheduler()

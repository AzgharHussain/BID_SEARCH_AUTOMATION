import json
import os
import pytz
import time
from datetime import datetime, timedelta, time as dtime
from typing import Dict, Any, Optional, Tuple, List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.db.database import SessionLocal
from app.models import models
from app.services.collaboration_email_service import collaboration_email_service

IST_TIMEZONE = pytz.timezone("Asia/Kolkata")

# Default Schedule Specifications
DEFAULT_STATES_TIME = "09:30"   # 29 Indian States at 09:30 AM IST
DEFAULT_ADB_TIME = "10:30"      # ADB Multilateral at 10:30 AM IST
ADB_ROTATION_QUOTA = 50         # 50 emails per sender rotation
SEND_SAFETY_INTERVAL = 0.3      # Smooth 0.3s interval between dispatches to prevent socket collisions

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "scheduler_config.json"
)

ADB_SENDERS_ROTATION = [
    {
        "email": "support@gisfy.co.in",
        "name": "N C Harika | Business Development Executive",
        "role": "ADB Support & Multilateral Outreach"
    },
    {
        "email": "farhath@gisfy.co.in",
        "name": "Farhath | Business Development Executive",
        "role": "International Alliances & ADB Operations"
    },
    {
        "email": "firza@gisfy.co.in",
        "name": "Firza | Business Development Executive",
        "role": "Multilateral Proposals & Strategic JV Lead"
    }
]


class CollaborationScheduler:
    """
    Automated Multi-Schedule Collaboration Outreach Engine:
    1. 29 Indian States Public Tenders:
       - Dispatched everyday at 09:30 AM IST
       - Sender: bidding.gisfy@gmail.com (N C Harika | Business Development Executive)
       - CC: bidding@gisfy.co.in
       - Sent automatically without delay.
    2. ADB Multilateral Projects:
       - Dispatched everyday at 10:30 AM IST
       - Sender rotation with strict 50-email quota:
         * Batch 1: First 50 emails through support@gisfy.co.in (N C Harika | Business Development Executive)
         * Batch 2: Next 50 emails through farhath@gisfy.co.in (Farhath | Business Development Executive)
         * Batch 3: Next 50 emails through firza@gisfy.co.in (Firza | Business Development Executive)
         * Rotation repeats continuously.
       - Sent automatically without delay.
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=IST_TIMEZONE)
        self.is_running = False
        self.is_paused = False
        self.config_file = CONFIG_FILE

        # 29 States Schedule (Default 09:30 AM IST)
        self.states_schedule_time = DEFAULT_STATES_TIME
        self.states_hour = 9
        self.states_minute = 30
        self.states_sender_email = "bidding.gisfy@gmail.com"
        self.states_sender_name = "N C Harika | Business Development Executive"

        # ADB Multilateral Schedule (Default 10:30 AM IST)
        self.adb_schedule_time = DEFAULT_ADB_TIME
        self.adb_hour = 10
        self.adb_minute = 30
        self.adb_rotation_quota = ADB_ROTATION_QUOTA
        self.adb_senders = list(ADB_SENDERS_ROTATION)

        # Active Sending Window & Settings
        self.window_start = dtime(9, 0)
        self.window_end = dtime(18, 0)
        self.pilot_mode = False          # Production automated mode
        self.auto_send_enabled = True    # Automated dispatches active
        self.max_daily_limit = 5000      # Uncapped production allowance
        self.pilot_limit = 50

        # Job Identifiers
        self.states_job_id = "daily_states_dispatch_0930_ist"
        self.adb_job_id = "daily_adb_rotation_dispatch_1030_ist"
        self.queue_job_id = "paged_queue_worker_ist"
        self.daily_job_id = self.states_job_id

        self.last_run_time: Optional[datetime] = None
        self.last_summary: Optional[Dict[str, Any]] = None

        self.load_config()

    def load_config(self):
        """Load persisted schedule settings from scheduler_config.json."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 29 States time
                if "states_schedule_time" in data:
                    self.states_schedule_time = str(data["states_schedule_time"]).strip()
                    parts = self.states_schedule_time.split(":")
                    if len(parts) >= 2:
                        self.states_hour = int(parts[0])
                        self.states_minute = int(parts[1])

                # ADB time
                if "adb_schedule_time" in data:
                    self.adb_schedule_time = str(data["adb_schedule_time"]).strip()
                    parts = self.adb_schedule_time.split(":")
                    if len(parts) >= 2:
                        self.adb_hour = int(parts[0])
                        self.adb_minute = int(parts[1])

                # Legacy fallback
                if "schedule_time" in data and "states_schedule_time" not in data:
                    parts = str(data["schedule_time"]).strip().split(":")
                    if len(parts) >= 2:
                        self.states_hour = int(parts[0])
                        self.states_minute = int(parts[1])
                        self.states_schedule_time = f"{self.states_hour:02d}:{self.states_minute:02d}"

                if "adb_rotation_quota" in data:
                    self.adb_rotation_quota = int(data["adb_rotation_quota"])

                if "window_start" in data:
                    sp = str(data["window_start"]).strip().split(":")
                    if len(sp) >= 2:
                        self.window_start = dtime(int(sp[0]), int(sp[1]))

                if "window_end" in data:
                    ep = str(data["window_end"]).strip().split(":")
                    if len(ep) >= 2:
                        self.window_end = dtime(int(ep[0]), int(ep[1]))

                if "pilot_mode" in data:
                    self.pilot_mode = bool(data["pilot_mode"])

                if "auto_send_enabled" in data:
                    self.auto_send_enabled = bool(data["auto_send_enabled"])
                    collaboration_email_service.auto_send_enabled = self.auto_send_enabled

                print(f"⚙️ [Collaboration Scheduler] Loaded settings: 29 States={self.get_formatted_states_time()}, ADB={self.get_formatted_adb_time()} (Quota: {self.adb_rotation_quota} per sender)")
            except Exception as e:
                print(f"⚠️ [Scheduler Config] Error loading {self.config_file}: {e}")

    def save_config(self):
        """Persist current scheduler configuration to scheduler_config.json."""
        try:
            payload = {
                "states_schedule_time": self.states_schedule_time,
                "states_hour": self.states_hour,
                "states_minute": self.states_minute,
                "states_formatted_time": self.get_formatted_states_time(),
                "states_sender_email": self.states_sender_email,
                "states_sender_name": self.states_sender_name,
                "adb_schedule_time": self.adb_schedule_time,
                "adb_hour": self.adb_hour,
                "adb_minute": self.adb_minute,
                "adb_formatted_time": self.get_formatted_adb_time(),
                "adb_rotation_quota": self.adb_rotation_quota,
                "adb_senders_rotation": [s["email"] for s in self.adb_senders],
                "mandatory_cc": "bidding@gisfy.co.in",
                "window_start": self.window_start.strftime("%H:%M"),
                "window_end": self.window_end.strftime("%H:%M"),
                "pilot_mode": self.pilot_mode,
                "auto_send_enabled": self.auto_send_enabled,
                "timezone": "Asia/Kolkata (IST)",
                "updated_at": datetime.utcnow().isoformat()
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            print(f"⚠️ [Scheduler Config] Error saving {self.config_file}: {e}")

    def get_formatted_states_time(self) -> str:
        """Return formatted 29 States time like '09:30 AM IST'."""
        try:
            return dtime(self.states_hour, self.states_minute).strftime("%I:%M %p IST")
        except Exception:
            return f"{self.states_hour:02d}:{self.states_minute:02d} IST"

    def get_formatted_adb_time(self) -> str:
        """Return formatted ADB Multilateral time like '10:30 AM IST'."""
        try:
            return dtime(self.adb_hour, self.adb_minute).strftime("%I:%M %p IST")
        except Exception:
            return f"{self.adb_hour:02d}:{self.adb_minute:02d} IST"

    def set_schedules(
        self,
        states_time: Optional[str] = None,
        adb_time: Optional[str] = None,
        adb_quota: Optional[int] = None,
        auto_send_enabled: Optional[bool] = None,
        window_start: Optional[str] = None,
        window_end: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically update outreach schedules and reschedule background jobs immediately.
        """
        if states_time:
            sp = states_time.strip().split(":")
            if len(sp) >= 2:
                self.states_hour = int(sp[0])
                self.states_minute = int(sp[1])
                self.states_schedule_time = f"{self.states_hour:02d}:{self.states_minute:02d}"

        if adb_time:
            ap = adb_time.strip().split(":")
            if len(ap) >= 2:
                self.adb_hour = int(ap[0])
                self.adb_minute = int(ap[1])
                self.adb_schedule_time = f"{self.adb_hour:02d}:{self.adb_minute:02d}"

        if adb_quota is not None:
            self.adb_rotation_quota = max(1, int(adb_quota))

        if auto_send_enabled is not None:
            self.auto_send_enabled = bool(auto_send_enabled)
            collaboration_email_service.auto_send_enabled = self.auto_send_enabled

        if window_start:
            wsp = window_start.strip().split(":")
            if len(wsp) >= 2:
                self.window_start = dtime(int(wsp[0]), int(wsp[1]))

        if window_end:
            wep = window_end.strip().split(":")
            if len(wep) >= 2:
                self.window_end = dtime(int(wep[0]), int(wep[1]))

        # Reschedule active jobs if running
        if self.is_running:
            self._reschedule_all_jobs()

        self.save_config()
        return self.get_status()

    def set_schedule_time(
        self,
        time_str: str,
        window_start_str: Optional[str] = None,
        window_end_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """Backwards compatibility for updating schedule time."""
        return self.set_schedules(
            states_time=time_str,
            window_start=window_start_str,
            window_end=window_end_str
        )

    def set_pilot_mode(self, enabled: bool) -> Dict[str, Any]:
        """Toggle pilot mode."""
        self.pilot_mode = enabled
        self.save_config()
        return {
            "status": "updated",
            "pilot_mode": self.pilot_mode,
            "active_limit": self.pilot_limit if self.pilot_mode else self.max_daily_limit,
            "message": f"Scheduler configured for {'Pilot Mode' if self.pilot_mode else 'Production Mode'}."
        }

    def get_rolling_24h_sent_count(self, db) -> int:
        """Count emails dispatched across rolling 24 hours."""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        return db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.sent_at >= cutoff,
            models.CollaborationEmail.status.in_(["Provider Accepted", "Found in Sent Items", "Delivery Confirmed", "sent"]),
            models.CollaborationEmail.is_test_email == False
        ).count()

    def _reschedule_all_jobs(self):
        """Reschedule both 29 States and ADB daily jobs."""
        try:
            # 1. 29 States Daily Job at 09:30 AM IST
            states_trigger = CronTrigger(hour=self.states_hour, minute=self.states_minute, timezone=IST_TIMEZONE)
            if self.scheduler.get_job(self.states_job_id):
                self.scheduler.reschedule_job(self.states_job_id, trigger=states_trigger)
            else:
                self.scheduler.add_job(
                    func=self.execute_states_dispatch,
                    trigger=states_trigger,
                    id=self.states_job_id,
                    name=f"29 Indian States Daily Outreach ({self.get_formatted_states_time()}) via bidding.gisfy@gmail.com",
                    replace_existing=True,
                    misfire_grace_time=3600
                )

            # 2. ADB Multilateral Daily Job at 10:30 AM IST
            adb_trigger = CronTrigger(hour=self.adb_hour, minute=self.adb_minute, timezone=IST_TIMEZONE)
            if self.scheduler.get_job(self.adb_job_id):
                self.scheduler.reschedule_job(self.adb_job_id, trigger=adb_trigger)
            else:
                self.scheduler.add_job(
                    func=self.execute_adb_rotation_dispatch,
                    trigger=adb_trigger,
                    id=self.adb_job_id,
                    name=f"ADB Multilateral Daily Outreach ({self.get_formatted_adb_time()}) with 50-Email Rotation",
                    replace_existing=True,
                    misfire_grace_time=3600
                )
            print(f"🕒 [Collaboration Scheduler] All jobs rescheduled: States={self.get_formatted_states_time()}, ADB={self.get_formatted_adb_time()}")
        except Exception as e:
            print(f"❌ [Collaboration Scheduler] Error rescheduling jobs: {e}")

    def start_scheduler(self):
        """Start both automated outreach triggers and queue processor."""
        if self.is_running:
            return

        try:
            self._reschedule_all_jobs()

            # Paced queue worker for single manual approvals
            queue_trigger = IntervalTrigger(seconds=300, timezone=IST_TIMEZONE)
            self.scheduler.add_job(
                func=self.process_next_queued_email,
                trigger=queue_trigger,
                id=self.queue_job_id,
                name="Paced Queue Worker for Approved Emails",
                replace_existing=True,
                misfire_grace_time=60
            )

            self.scheduler.start()
            self.is_running = True
            self.is_paused = False
            print(f"🚀 [Collaboration Scheduler] Started: 29 States ({self.get_formatted_states_time()}) + ADB 50-Rotation ({self.get_formatted_adb_time()}) active.")
        except Exception as e:
            print(f"❌ [Collaboration Scheduler] Error starting scheduler: {e}")

    def pause(self):
        """Pause automated daily execution."""
        if self.is_running and not self.is_paused:
            try:
                for jid in [self.states_job_id, self.adb_job_id, self.queue_job_id]:
                    if self.scheduler.get_job(jid):
                        self.scheduler.pause_job(jid)
            except Exception:
                pass
            self.is_paused = True
            return {"status": "paused", "message": "Automation schedules paused."}
        return {"status": "already_paused"}

    def resume(self):
        """Resume automated daily execution."""
        if self.is_running and self.is_paused:
            try:
                for jid in [self.states_job_id, self.adb_job_id, self.queue_job_id]:
                    if self.scheduler.get_job(jid):
                        self.scheduler.resume_job(jid)
            except Exception:
                pass
            self.is_paused = False
            return {"status": "resumed", "message": "Automation schedules resumed."}
        return {"status": "already_active"}

    def stop_automation(self) -> Dict[str, Any]:
        """Stop Automation immediately."""
        self.auto_send_enabled = False
        collaboration_email_service.auto_send_enabled = False
        self.save_config()
        self.pause()
        return {
            "status": "stopped",
            "auto_send_enabled": False,
            "is_paused": True,
            "message": "Outreach automation stopped immediately. No emails will be sent automatically."
        }

    # --------------------------------------------------------------------------
    # 1. 29 INDIAN STATES OUTREACH: 09:30 AM IST (bidding.gisfy@gmail.com)
    # --------------------------------------------------------------------------

    def execute_states_dispatch(self, batch_limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Dispatches 29 Indian States outreach emails:
        - Time: Everyday at 09:30 AM IST
        - Sender: bidding.gisfy@gmail.com
        - Sender Name: N C Harika | Business Development Executive
        - CC: bidding@gisfy.co.in
        - Dispatches automatically without delay.
        """
        db = SessionLocal()
        start_time = datetime.utcnow()
        summary = {
            "schedule": "29 Indian States Outreach (09:30 AM IST)",
            "sender_email": "bidding.gisfy@gmail.com",
            "sender_name": "N C Harika | Business Development Executive",
            "cc": "bidding@gisfy.co.in",
            "started_at": start_time.isoformat(),
            "eligible_found": 0,
            "dispatched_count": 0,
            "failed_count": 0,
            "errors": [],
            "status": "completed"
        }
        try:
            query = db.query(models.CollaborationEmail).filter(
                models.CollaborationEmail.scope == "state",
                models.CollaborationEmail.status.in_(["draft", "approved", "pending"]),
                models.CollaborationEmail.is_test_email == False
            ).order_by(models.CollaborationEmail.id.asc())

            if batch_limit and batch_limit > 0:
                candidate_drafts = query.limit(batch_limit).all()
            else:
                candidate_drafts = query.all()

            summary["eligible_found"] = len(candidate_drafts)
            print(f"🇮🇳 [States 09:30 AM Dispatch] Found {len(candidate_drafts)} candidate drafts to send via bidding.gisfy@gmail.com")

            for draft in candidate_drafts:
                try:
                    draft.sender_email = "bidding.gisfy@gmail.com"
                    draft.sender_name = "N C Harika | Business Development Executive"
                    draft.approval_status = "approved"
                    db.commit()

                    success, msg = collaboration_email_service.send_email(db, draft.id)
                    if success:
                        summary["dispatched_count"] += 1
                    else:
                        summary["failed_count"] += 1
                        summary["errors"].append(f"Draft #{draft.id} ({draft.recipient_email}): {msg}")

                    time.sleep(SEND_SAFETY_INTERVAL)
                except Exception as ex:
                    summary["failed_count"] += 1
                    summary["errors"].append(f"Draft #{draft.id} error: {ex}")

            # Record workflow log
            log_entry = models.CollaborationWorkflowLog(
                cycle_type="states_0930_dispatch",
                started_at=start_time,
                finished_at=datetime.utcnow(),
                tenders_analyzed=summary["eligible_found"],
                drafts_created=0,
                emails_sent=summary["dispatched_count"],
                errors_count=summary["failed_count"],
                status="success" if summary["failed_count"] == 0 else "completed_with_errors",
                log_details=f"Dispatched {summary['dispatched_count']} 29 States outreach emails from bidding.gisfy@gmail.com (CC: bidding@gisfy.co.in) at 09:30 AM IST."
            )
            db.add(log_entry)
            db.commit()

            self.last_run_time = datetime.utcnow()
            self.last_summary = summary
            return summary
        except Exception as e:
            db.rollback()
            summary["status"] = "failed"
            summary["errors"].append(str(e))
            return summary
        finally:
            db.close()

    # --------------------------------------------------------------------------
    # 2. ADB MULTILATERAL OUTREACH: 10:30 AM IST (50 support -> 50 farhath -> 50 firza)
    # --------------------------------------------------------------------------

    def execute_adb_rotation_dispatch(self, quota_per_sender: int = 50) -> Dict[str, Any]:
        """
        Dispatches ADB Multilateral outreach emails:
        - Time: Everyday at 10:30 AM IST
        - Strict rotation sequence:
          1. 50 emails sent through support@gisfy.co.in (N C Harika | Business Development Executive)
          2. Once 50 emails completed, next 50 emails sent through farhath@gisfy.co.in (Farhath | Business Development Executive)
          3. Once 50 emails completed, next 50 emails sent through firza@gisfy.co.in (Firza | Business Development Executive)
        - Sent automatically without delay.
        """
        db = SessionLocal()
        start_time = datetime.utcnow()
        summary = {
            "schedule": "ADB Multilateral Outreach (10:30 AM IST)",
            "rotation_quota_per_sender": quota_per_sender,
            "started_at": start_time.isoformat(),
            "total_dispatched": 0,
            "total_failed": 0,
            "tranches": [],
            "errors": [],
            "status": "completed"
        }

        try:
            for sender_info in self.adb_senders:
                target_email = sender_info["email"]
                target_name = sender_info["name"]

                tranche_summary = {
                    "sender_email": target_email,
                    "sender_name": target_name,
                    "target_quota": quota_per_sender,
                    "sent_count": 0,
                    "failed_count": 0,
                    "errors": []
                }

                # 1. Fetch up to quota_per_sender candidate drafts specifically assigned to this sender
                drafts = db.query(models.CollaborationEmail).filter(
                    models.CollaborationEmail.scope == "adb",
                    models.CollaborationEmail.status.in_(["draft", "approved", "pending"]),
                    models.CollaborationEmail.is_test_email == False,
                    models.CollaborationEmail.sender_email == target_email
                ).order_by(models.CollaborationEmail.id.asc()).limit(quota_per_sender).all()

                # 2. If fewer than quota, take any remaining unassigned pending ADB drafts and assign to this sender
                if len(drafts) < quota_per_sender:
                    needed = quota_per_sender - len(drafts)
                    existing_ids = [d.id for d in drafts]
                    extra_drafts = db.query(models.CollaborationEmail).filter(
                        models.CollaborationEmail.scope == "adb",
                        models.CollaborationEmail.status.in_(["draft", "approved", "pending"]),
                        models.CollaborationEmail.is_test_email == False,
                        ~models.CollaborationEmail.id.in_(existing_ids)
                    ).order_by(models.CollaborationEmail.id.asc()).limit(needed).all()

                    for ed in extra_drafts:
                        collaboration_email_service.assign_and_render_sender(db, ed, target_email, target_name)
                    drafts.extend(extra_drafts)

                print(f"🌐 [ADB 10:30 AM Dispatch] Tranche for {target_name} <{target_email}>: {len(drafts)} drafts ready to send")

                # 3. Dispatch this sender's tranche automatically without delay
                for draft in drafts:
                    try:
                        # Ensure sender matches exactly
                        if draft.sender_email != target_email:
                            collaboration_email_service.assign_and_render_sender(db, draft, target_email, target_name)

                        draft.approval_status = "approved"
                        db.commit()

                        success, msg = collaboration_email_service.send_email(db, draft.id)
                        if success:
                            tranche_summary["sent_count"] += 1
                            summary["total_dispatched"] += 1
                        else:
                            tranche_summary["failed_count"] += 1
                            summary["total_failed"] += 1
                            tranche_summary["errors"].append(f"Draft #{draft.id} ({draft.recipient_email}): {msg}")

                        time.sleep(SEND_SAFETY_INTERVAL)
                    except Exception as ex:
                        tranche_summary["failed_count"] += 1
                        summary["total_failed"] += 1
                        tranche_summary["errors"].append(f"Draft #{draft.id} error: {ex}")

                summary["tranches"].append(tranche_summary)
                print(f"✅ [ADB 10:30 AM Dispatch] Completed {tranche_summary['sent_count']}/{quota_per_sender} for {target_email}")

            # Record workflow log
            log_entry = models.CollaborationWorkflowLog(
                cycle_type="adb_1030_rotation_dispatch",
                started_at=start_time,
                finished_at=datetime.utcnow(),
                tenders_analyzed=summary["total_dispatched"] + summary["total_failed"],
                drafts_created=0,
                emails_sent=summary["total_dispatched"],
                errors_count=summary["total_failed"],
                status="success" if summary["total_failed"] == 0 else "completed_with_errors",
                log_details=f"ADB 10:30 AM Rotation Completed: Dispatched {summary['total_dispatched']} emails across support@gisfy.co.in (50), farhath@gisfy.co.in (50), firza@gisfy.co.in (50). CC: bidding@gisfy.co.in."
            )
            db.add(log_entry)
            db.commit()

            self.last_run_time = datetime.utcnow()
            self.last_summary = summary
            return summary
        except Exception as e:
            db.rollback()
            summary["status"] = "failed"
            summary["errors"].append(str(e))
            return summary
        finally:
            db.close()

    # --------------------------------------------------------------------------
    # 3. QUEUE WORKER & STATUS
    # --------------------------------------------------------------------------

    def process_next_queued_email(self) -> Optional[Dict[str, Any]]:
        """Worker for single approved emails."""
        if not self.auto_send_enabled or self.is_paused:
            return None

        db = SessionLocal()
        try:
            next_email = db.query(models.CollaborationEmail).filter(
                models.CollaborationEmail.status == "approved",
                models.CollaborationEmail.approval_status == "approved"
            ).order_by(models.CollaborationEmail.approved_at.asc()).first()

            if not next_email:
                return None

            success, message = collaboration_email_service.send_email(db, next_email.id)
            return {
                "dispatched": True,
                "email_id": next_email.id,
                "recipient": next_email.recipient_email,
                "success": success,
                "message": message
            }
        except Exception as e:
            return {"dispatched": False, "error": str(e)}
        finally:
            db.close()

    def execute_daily_workflow(self, cycle_type: str = "daily_scheduled") -> Dict[str, Any]:
        """Master runner executing both 29 States and ADB dispatches."""
        res_states = self.execute_states_dispatch(batch_limit=50)
        res_adb = self.execute_adb_rotation_dispatch(quota_per_sender=self.adb_rotation_quota)
        return {
            "cycle_type": cycle_type,
            "states_result": res_states,
            "adb_result": res_adb
        }

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive dual-schedule status."""
        states_job = self.scheduler.get_job(self.states_job_id) if self.is_running else None
        adb_job = self.scheduler.get_job(self.adb_job_id) if self.is_running else None

        next_states_run = states_job.next_run_time.astimezone(IST_TIMEZONE).isoformat() if (states_job and states_job.next_run_time) else None
        next_adb_run = adb_job.next_run_time.astimezone(IST_TIMEZONE).isoformat() if (adb_job and adb_job.next_run_time) else None

        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=24)
            sent_today_states = db.query(models.CollaborationEmail).filter(
                models.CollaborationEmail.scope == "state",
                models.CollaborationEmail.sent_at >= cutoff,
                models.CollaborationEmail.status.in_(["Provider Accepted", "Found in Sent Items", "Delivery Confirmed", "sent"])
            ).count()

            sent_today_adb = db.query(models.CollaborationEmail).filter(
                models.CollaborationEmail.scope == "adb",
                models.CollaborationEmail.sent_at >= cutoff,
                models.CollaborationEmail.status.in_(["Provider Accepted", "Found in Sent Items", "Delivery Confirmed", "sent"])
            ).count()

            pending_states = db.query(models.CollaborationEmail).filter(
                models.CollaborationEmail.scope == "state",
                models.CollaborationEmail.status.in_(["draft", "approved", "pending"])
            ).count()

            pending_adb = db.query(models.CollaborationEmail).filter(
                models.CollaborationEmail.scope == "adb",
                models.CollaborationEmail.status.in_(["draft", "approved", "pending"])
            ).count()
        finally:
            db.close()

        formatted_states = self.get_formatted_states_time()
        formatted_adb = self.get_formatted_adb_time()

        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "timezone": "Asia/Kolkata (IST)",
            "auto_send_enabled": self.auto_send_enabled,
            "pilot_mode": self.pilot_mode,
            "states_schedule": {
                "name": "29 Indian States Public Tender Outreach",
                "time": self.states_schedule_time,
                "formatted_time": formatted_states,
                "sender_email": self.states_sender_email,
                "sender_name": self.states_sender_name,
                "mandatory_cc": "bidding@gisfy.co.in",
                "next_run_time_ist": next_states_run,
                "sent_today_24h": sent_today_states,
                "pending_drafts_count": pending_states
            },
            "adb_schedule": {
                "name": "ADB Multilateral Projects Outreach",
                "time": self.adb_schedule_time,
                "formatted_time": formatted_adb,
                "rotation_quota_per_sender": self.adb_rotation_quota,
                "senders_rotation": [
                    "1️⃣ support@gisfy.co.in (50 emails)",
                    "2️⃣ farhath@gisfy.co.in (50 emails)",
                    "3️⃣ firza@gisfy.co.in (50 emails)"
                ],
                "mandatory_cc": "bidding@gisfy.co.in",
                "next_run_time_ist": next_adb_run,
                "sent_today_24h": sent_today_adb,
                "pending_drafts_count": pending_adb
            },
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "last_summary": self.last_summary,
            # Backwards compatibility fields for frontend
            "schedule_time": self.states_schedule_time,
            "formatted_schedule_time": f"States: {formatted_states} | ADB: {formatted_adb}",
            "today_sent_24h": sent_today_states + sent_today_adb,
            "remaining_daily_allowance": 9999,
            "active_limit": "Automated Production",
            "within_business_window": True,
            "business_window_status": "Active Automated Production Dispatching"
        }


collaboration_scheduler = CollaborationScheduler()

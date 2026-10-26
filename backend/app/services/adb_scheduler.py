import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.adb_cms_connector import adb_connector

logger = logging.getLogger("adb_scheduler")

class AdbSchedulerService:
    """Manages scheduled daily synchronization and discovery of ADB CMS consulting opportunities."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.last_run_time = None
        self.next_run_time = None

    def start_scheduler(self):
        """Start the daily autonomous ADB discovery scheduler."""
        if self.is_running:
            return

        try:
            # Run daily at 06:00 AM IST (00:30 UTC)
            self.scheduler.add_job(
                self._run_daily_sync,
                trigger="interval",
                hours=24,
                id="adb_daily_sync",
                replace_existing=True
            )
            self.scheduler.start()
            self.is_running = True
            logger.info("ADB CMS Daily Synchronization Scheduler started successfully.")
        except Exception as e:
            logger.error(f"Failed to start ADB scheduler: {e}")

    async def _run_daily_sync(self):
        """Execute scheduled synchronization."""
        logger.info("Executing scheduled daily ADB CMS opportunity synchronization...")
        self.last_run_time = datetime.utcnow()
        try:
            result = await adb_connector.sync_opportunities(max_count=10, sync_type="scheduled")
            logger.info(f"Scheduled ADB sync completed: {result.get('opportunities_added', 0)} added, {result.get('documents_downloaded', 0)} docs.")
        except Exception as e:
            logger.error(f"Scheduled ADB sync failed: {e}")

    def get_status(self):
        """Retrieve scheduler operational status."""
        job = self.scheduler.get_job("adb_daily_sync") if self.is_running else None
        return {
            "is_running": self.is_running,
            "last_run": self.last_run_time.isoformat() if self.last_run_time else None,
            "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None
        }


adb_scheduler = AdbSchedulerService()

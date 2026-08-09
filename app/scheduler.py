import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.reporting import send_daily_report

logger = logging.getLogger("sogo.scheduler")

scheduler = AsyncIOScheduler(timezone=settings.app_timezone)


async def _scheduled_job():
    logger.info("Running scheduled 08:00 report job")
    try:
        summary = await send_daily_report()
        logger.info("Scheduled report result: %s", summary)
    except Exception:
        logger.exception("Scheduled report job failed")


def start_scheduler():
    scheduler.add_job(
        _scheduled_job,
        trigger=CronTrigger(hour=settings.daily_report_hour, minute=settings.daily_report_minute),
        id="daily_report",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info(
        "Scheduler started - daily report at %02d:%02d %s",
        settings.daily_report_hour, settings.daily_report_minute, settings.app_timezone,
    )

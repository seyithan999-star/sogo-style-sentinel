import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.reporting import send_daily_report
from app.ingestion import run_full_scan

logger = logging.getLogger("sogo.scheduler")
scheduler = AsyncIOScheduler(timezone=settings.app_timezone)


async def _continuous_scan_job():
    logger.info("Continuous source scan started")
    try:
        runs = await run_full_scan()
        logger.info("Continuous scan finished: %s sources", len(runs))
    except Exception:
        logger.exception("Continuous scan failed")


async def _scheduled_report_job():
    logger.info("Running scheduled 08:00 report job")
    try:
        summary = await send_daily_report(scan_before_report=False)
        logger.info("Scheduled report result: %s", summary)
    except Exception:
        logger.exception("Scheduled report job failed")


def start_scheduler():
    if scheduler.running:
        return
    scheduler.add_job(
        _continuous_scan_job,
        trigger=IntervalTrigger(minutes=max(5, settings.scan_interval_minutes)),
        id="continuous_scan",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=900,
        next_run_time=None,
    )
    scheduler.add_job(
        _scheduled_report_job,
        trigger=CronTrigger(hour=settings.daily_report_hour, minute=settings.daily_report_minute),
        id="daily_report",
        replace_existing=True,
        misfire_grace_time=3600,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    # fire a scan shortly after startup without blocking web server startup
    scheduler.add_job(_continuous_scan_job, "date", id="startup_scan", replace_existing=True)
    logger.info(
        "Scheduler started - scan every %d min; daily report at %02d:%02d %s",
        settings.scan_interval_minutes, settings.daily_report_hour, settings.daily_report_minute, settings.app_timezone,
    )

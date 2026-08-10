"""
Şartname Bölüm 17/18: Europe/Istanbul 08:00 otomatik raporu.
Idempotency: daily_reports.report_date UNIQUE constraint'i ile aynı gün iki kez rapor
gönderilmesi DB seviyesinde engellenir (distributed lock yerine basit ve güvenilir yöntem;
tek worker process varsayımı - birden fazla worker instance'ı için Postgres advisory lock
kullanılabilir, bkz. README "Ölçeklendirme" bölümü).
"""
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.database import async_session
from app.models import Product, DailyReport
from app.ingestion import run_full_scan
from app.bot.instance import bot
from app.bot.product_card import send_product_card

logger = logging.getLogger("sogo.reporting")


async def send_daily_report(chat_id: str | None = None, triggered_manually: bool = False, scan_before_report: bool = True) -> dict:
    tz = ZoneInfo(settings.app_timezone)
    today_str = datetime.now(tz).strftime("%Y-%m-%d")
    target_chat = chat_id or settings.telegram_report_chat_id

    async with async_session() as session:
        if not triggered_manually:
            # idempotency: bugün için zaten rapor varsa tekrar gönderme
            existing = await session.execute(select(DailyReport).where(DailyReport.report_date == today_str))
            if existing.scalar_one_or_none():
                logger.info("Daily report for %s already sent, skipping", today_str)
                return {"skipped": True, "reason": "already_sent_today"}

    # 1) Manual report can scan first; scheduled report uses products accumulated by continuous scans.
    runs = await run_full_scan() if scan_before_report else []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max(1, settings.report_lookback_hours))

    # 2) En iyi ürünleri seç ve gönder
    async with async_session() as session:
        result = await session.execute(
            select(Product)
            .where(
                Product.delivered.is_(False),
                Product.is_suppressed.is_(False),
                Product.score_sogo_fit >= settings.min_sogo_score,
                Product.discovered_at >= cutoff,
            )
            .order_by(desc(Product.score_sogo_fit), desc(Product.score_trend), desc(Product.discovered_at))
            .limit(settings.daily_target_max)
        )
        candidates = result.scalars().all()

        sent = 0
        failed = 0
        for product in candidates[: settings.daily_target_max]:
            ok = await send_product_card(bot, session, target_chat, product)
            if ok:
                sent += 1
            else:
                failed += 1
            if sent >= settings.daily_target_max:
                break

        summary = {
            "date": today_str,
            "sources_scanned": len(runs),
            "sources_healthy": sum(1 for r in runs if r.status == "healthy"),
            "sources_degraded": sum(1 for r in runs if r.status == "degraded"),
            "sources_disabled": sum(1 for r in runs if r.status == "disabled"),
            "sources_blocked": sum(1 for r in runs if r.status == "blocked"),
            "lookback_hours": settings.report_lookback_hours,
            "candidates_found": len(candidates),
            "sent": sent,
            "failed": failed,
        }

        if not triggered_manually:
            try:
                session.add(DailyReport(report_date=today_str, summary=summary))
                await session.commit()
            except IntegrityError:
                await session.rollback()  # aynı anda başka bir process yazdıysa sessizce geç

    # 3) Özet mesajı ayrıca gönder
    summary_text = (
        f"📈 <b>Günlük Özet - {today_str}</b>\n\n"
        f"Rapor aralığı: son {summary['lookback_hours']} saat\n"
        f"Rapor öncesi taranan kaynak: {summary['sources_scanned']}\n"
        f"Sağlıklı: {summary['sources_healthy']} | Degraded: {summary['sources_degraded']} | "
        f"Devre dışı: {summary['sources_disabled']} | Engelli: {summary['sources_blocked']}\n\n"
        f"Uygun aday ürün: {summary['candidates_found']}\n"
        f"Gönderilen: {summary['sent']} | Hata: {summary['failed']}"
    )
    try:
        await bot.send_message(chat_id=target_chat, text=summary_text, parse_mode="HTML")
    except Exception:
        logger.exception("Failed to send summary message")

    return summary

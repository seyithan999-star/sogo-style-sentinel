import logging
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, func, desc

from app.config import settings
from app.database import async_session
from app.models import Product, SourceRun, Feedback, TelegramDelivery
from app.learning import apply_feedback
from app.bot.product_card import send_product_card

logger = logging.getLogger("sogo.bot.handlers")
router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids if settings.admin_ids else True  # admin listesi boşsa herkes (ilk kurulum kolaylığı)


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 <b>SOGO Style Sentinel</b> aktif.\n\n"
        "Gün boyunca kaynakları takip eder; her sabah 08:00'de (Europe/Istanbul) biriken yeni ve SOGO'ya uygun kadın giyim ürünlerini raporlar.\n\n"
        "Komutlar:\n"
        "/status - sistem durumu\n"
        "/report - manuel rapor / dry-run başlat\n"
        "/favorites - favori ürünlerin\n"
        "/search kelime - kayıtlı ürünlerde arama\n"
        "/sources - takip kapsamı ve bağlantı durumu\n",
        parse_mode="HTML",
    )


@router.message(Command("status"))
async def cmd_status(message: Message):
    async with async_session() as session:
        last_runs = await session.execute(
            select(SourceRun).order_by(desc(SourceRun.started_at)).limit(10)
        )
        runs = last_runs.scalars().all()
        total_products = (await session.execute(select(func.count(Product.id)))).scalar_one()
        total_delivered = (await session.execute(
            select(func.count(TelegramDelivery.id)).where(TelegramDelivery.status == "sent")
        )).scalar_one()

    lines = ["📊 <b>Sistem Durumu</b>\n"]
    lines.append(f"Toplam kayıtlı ürün: {total_products}")
    lines.append(f"Toplam gönderilen: {total_delivered}\n")
    lines.append("<b>Son kaynak taramaları:</b>")
    if not runs:
        lines.append("Henüz tarama çalıştırılmadı.")
    for r in runs:
        lines.append(f"• {r.source_name}: {r.status} (bulunan {r.items_found}, yeni {r.items_new})")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("sources"))
async def cmd_sources(message: Message):
    from app.source_catalog import RETAIL_SOURCES, SOCIAL_RESEARCH_SOURCES, PREMIUM_BRANDS, INSTAGRAM_ACCOUNTS
    provider = "BAĞLI" if settings.search_provider_url and settings.search_provider_key else "AYAR BEKLİYOR"
    text = (
        "🛰 <b>Takip Kapsamı</b>\n\n"
        f"Lisanslı arama sağlayıcısı: <b>{provider}</b>\n"
        f"Perakende/market kaynakları: {len(RETAIL_SOURCES)}\n"
        f"Sosyal araştırma kaynakları: {len(SOCIAL_RESEARCH_SOURCES)}\n"
        f"Premium marka havuzu: {len(PREMIUM_BRANDS)}\n"
        f"Instagram hedef hesabı: {len(INSTAGRAM_ACCOUNTS)}\n"
        f"Tarama aralığı: {settings.scan_interval_minutes} dakika\n\n"
        "Not: API/partner izni gerektiren kaynaklar izin verilene kadar disabled görünür; bot sahte başarı üretmez."
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("report"))
async def cmd_report(message: Message):
    from app.reporting import send_daily_report  # local import: circular import önleme
    await message.answer("⏳ Rapor hazırlanıyor, bu birkaç dakika sürebilir...")
    try:
        summary = await send_daily_report(chat_id=str(message.chat.id), triggered_manually=True)
        await message.answer(f"✅ Rapor tamamlandı. Gönderilen ürün: {summary.get('sent', 0)}")
    except Exception as e:
        logger.exception("Manual report failed")
        await message.answer(f"❌ Rapor başarısız: {str(e)[:300]}")


@router.message(Command("favorites"))
async def cmd_favorites(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Product)
            .join(Feedback, Feedback.product_id == Product.id)
            .where(Feedback.action == "favorite")
            .order_by(desc(Product.discovered_at))
            .limit(10)
        )
        products = result.scalars().unique().all()

    if not products:
        await message.answer("Henüz favori işaretlenmiş ürün yok.")
        return

    lines = ["⭐ <b>Favorilerin:</b>\n"]
    for p in products:
        lines.append(f"• {p.brand} - {p.title}\n  {p.canonical_url}")
    await message.answer("\n\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


@router.message(Command("search"))
async def cmd_search(message: Message, command: CommandObject):
    query = (command.args or "").strip()
    if not query:
        await message.answer("Kullanım: /search kelime veya marka adı")
        return

    async with async_session() as session:
        result = await session.execute(
            select(Product)
            .where(Product.title.ilike(f"%{query}%") | Product.brand.ilike(f"%{query}%"))
            .order_by(desc(Product.score_sogo_fit))
            .limit(10)
        )
        products = result.scalars().all()

    if not products:
        await message.answer(f"'{query}' için sonuç bulunamadı.")
        return

    for p in products:
        async with async_session() as session:
            p = await session.get(Product, p.id)
            await send_product_card(message.bot, session, str(message.chat.id), p)


@router.callback_query(F.data.startswith("fb:"))
async def on_feedback(callback: CallbackQuery):
    try:
        _, action, product_id = callback.data.split(":", 2)
    except ValueError:
        await callback.answer("Geçersiz veri", show_alert=False)
        return

    async with async_session() as session:
        product = await session.get(Product, product_id)
        if not product:
            await callback.answer("Ürün bulunamadı", show_alert=False)
            return

        session.add(Feedback(
            product_id=product_id,
            telegram_user_id=str(callback.from_user.id),
            action=action,
        ))
        await session.commit()
        await apply_feedback(session, product, action)

    action_labels = {
        "love": "❤️ Çok beğendin", "like": "👍 Beğendin", "favorite": "⭐ Favorilere eklendi",
        "dislike": "👎 Beğenmedin", "hide": "🚫 Bir daha gösterilmeyecek", "save": "💾 Kaydedildi",
    }
    await callback.answer(action_labels.get(action, "Kaydedildi"), show_alert=False)

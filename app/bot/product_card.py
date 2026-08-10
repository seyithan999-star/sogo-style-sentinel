import logging
from html import escape
from aiogram import Bot
from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import feedback_keyboard
from app.models import Product, TelegramDelivery

logger = logging.getLogger("sogo.bot.card")


def build_caption(product: Product) -> str:
    price_line = f"{product.price} {product.currency}" if product.price and product.currency else "Fiyat bilgisi yok"
    published = product.published_at.strftime("%d.%m.%Y") if product.published_at else "Tespit tarihi kullanıldı"
    brand = escape(product.brand or "")
    title = escape(product.title or "")
    source = escape(product.source_name or "")
    attrs = product.attributes or {}
    attr_text = ", ".join(sorted({v for values in attrs.values() for v in (values if isinstance(values, list) else [])}))
    attr_line = f"\n🧩 {escape(attr_text[:240])}" if attr_text else ""

    return (
        f"<b>{brand}</b>\n"
        f"{title}\n\n"
        f"💰 {escape(price_line)}\n"
        f"📅 {escape(published)}\n"
        f"🌐 Kaynak: {source}\n\n"
        f"📊 Ticari: {product.score_commercial}/10 | Orijinallik: {product.score_originality}/10 | "
        f"Premium: {product.score_premium}/10 | Trend: {product.score_trend}/10\n"
        f"🎯 SOGO Uyum: {product.score_sogo_fit}/100"
        f"{attr_line}"
    )


async def _send_link_and_feedback(bot: Bot, chat_id: str, product: Product, reply_to_message_id: int | None = None):
    safe_url = escape(product.canonical_url, quote=True)
    await bot.send_message(
        chat_id=chat_id,
        text=f"🔗 <b>Ürün linki</b>\n<a href=\"{safe_url}\">{safe_url}</a>",
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_to_message_id=reply_to_message_id,
        reply_markup=feedback_keyboard(product.id),
    )


async def send_product_card(bot: Bot, session: AsyncSession, chat_id: str, product: Product) -> bool:
    """Send up to 3 distinct product images; keep the product link in its own message."""
    delivery = TelegramDelivery(product_id=product.id, chat_id=str(chat_id), status="pending")
    session.add(delivery)
    await session.flush()

    images = sorted(product.images, key=lambda i: i.order_index)[:3]
    caption = build_caption(product)

    try:
        reply_to = None
        if len(images) >= 2:
            media = [InputMediaPhoto(media=img.url) for img in images]
            media[0].caption = caption
            media[0].parse_mode = "HTML"
            sent_messages = await bot.send_media_group(chat_id=chat_id, media=media)
            reply_to = sent_messages[-1].message_id
        elif len(images) == 1:
            msg = await bot.send_photo(chat_id=chat_id, photo=images[0].url, caption=caption, parse_mode="HTML")
            reply_to = msg.message_id
        else:
            msg = await bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML")
            reply_to = msg.message_id

        await _send_link_and_feedback(bot, chat_id, product, reply_to)
        delivery.status = "sent"
        product.delivered = True
        await session.commit()
        return True
    except Exception as e:
        logger.exception("Delivery failed for product %s", product.id)
        delivery.status = "failed"
        delivery.error_message = str(e)[:500]
        await session.commit()
        return False

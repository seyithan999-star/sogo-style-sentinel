import logging
from aiogram import Bot
from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import feedback_keyboard
from app.models import Product, TelegramDelivery

logger = logging.getLogger("sogo.bot.card")


def build_caption(product: Product) -> str:
    price_line = f"{product.price} {product.currency}" if product.price and product.currency else "Fiyat bilgisi yok"
    published = product.published_at.strftime("%d.%m.%Y") if product.published_at else "Tespit tarihi kullanıldı"

    note = (
        f"Bu ürün {product.brand} kaynaklı, SOGO'nun aradığı premium/spor-şık DNA'sına "
        f"uyum skoru {product.score_sogo_fit}/100. Ticari potansiyeli ve orijinal detayları "
        f"nedeniyle öne çıkarıldı."
    )

    return (
        f"<b>{product.brand}</b>\n"
        f"{product.title}\n\n"
        f"💰 {price_line}\n"
        f"📅 {published}\n"
        f"🔗 <a href='{product.canonical_url}'>Ürüne git</a>\n\n"
        f"📊 Ticari: {product.score_commercial}/10 | Orijinallik: {product.score_originality}/10 | "
        f"Premium: {product.score_premium}/10\n"
        f"🎯 SOGO Uyum: {product.score_sogo_fit}/100\n\n"
        f"📝 {note}"
    )


async def send_product_card(bot: Bot, session: AsyncSession, chat_id: str, product: Product) -> bool:
    """Ürünü 3 görsel + caption + feedback butonları ile gönderir. Başarısızsa DB'ye 'failed' yazar."""
    delivery = TelegramDelivery(product_id=product.id, chat_id=str(chat_id), status="pending")
    session.add(delivery)
    await session.flush()

    images = sorted(product.images, key=lambda i: i.order_index)[:3]
    caption = build_caption(product)

    try:
        if len(images) >= 2:
            media = [InputMediaPhoto(media=img.url) for img in images]
            media[-1].caption = caption
            media[-1].parse_mode = "HTML"
            sent_messages = await bot.send_media_group(chat_id=chat_id, media=media)
            # Feedback butonlarını albümün altına ayrı mesaj olarak ekle (Telegram media_group'a inline keyboard eklemez)
            await bot.send_message(
                chat_id=chat_id, text="Bu ürünü nasıl buldun?",
                reply_to_message_id=sent_messages[-1].message_id,
                reply_markup=feedback_keyboard(product.id),
            )
        elif len(images) == 1:
            await bot.send_photo(
                chat_id=chat_id, photo=images[0].url, caption=caption, parse_mode="HTML",
                reply_markup=feedback_keyboard(product.id),
            )
        else:
            await bot.send_message(
                chat_id=chat_id, text=caption, parse_mode="HTML",
                reply_markup=feedback_keyboard(product.id),
            )

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

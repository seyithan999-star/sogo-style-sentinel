"""
Şartname Bölüm 16: Feedback/Öğrenen Sistem.
Marka seviyesinde kalmaz; ürün tipi, renk, kumaş, yaka, kol, siluet, nakış/baskı,
panel/şerit, fiyat bandı ve kaynak sinyalleri ayrı ayrı güncellenir.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, StyleSignal
from app.scoring import PREMIUM_KEYWORDS, TARGET_COLORS
from app.attribute_extraction import extract_attributes

ACTION_DELTA = {
    "love": 6.0,
    "like": 3.0,
    "favorite": 5.0,
    "save": 1.5,
    "dislike": -4.0,
    "hide": -8.0,
}


def _extract_signal_values(product: Product) -> dict[str, list[str]]:
    text = f"{product.title} {product.category or ''} {product.raw_metadata}".lower()
    signals: dict[str, list[str]] = {"source": [product.source_name], "brand": [product.brand.lower()]}
    attrs = product.attributes or extract_attributes(text)
    for group, values in attrs.items():
        signals[group] = list(values)
    for k in PREMIUM_KEYWORDS:
        if k in text:
            signals.setdefault("fabric_or_detail", []).append(k)
    return signals


async def apply_feedback(session: AsyncSession, product: Product, action: str) -> None:
    delta = ACTION_DELTA.get(action, 0.0)
    if delta == 0.0:
        return

    signals = _extract_signal_values(product)
    for signal_type, values in signals.items():
        for value in values:
            result = await session.execute(
                select(StyleSignal).where(
                    StyleSignal.signal_type == signal_type, StyleSignal.signal_value == value
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                row = StyleSignal(signal_type=signal_type, signal_value=value, weight=0.0)
                session.add(row)
            row.weight = max(-100.0, min(100.0, row.weight + delta))

    if action == "hide":
        product.is_suppressed = True

    await session.commit()

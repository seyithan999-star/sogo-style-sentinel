"""
Ana ingestion pipeline: kaynak tara -> filtre -> duplicate kontrolü -> puanla -> DB'ye yaz.
Bir kaynak hata verirse diğerleri etkilenmeden devam eder (bölüm 2 / 22 / 26).
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import BaseSourceAdapter
from app.adapters.registry import get_all_sources
from app.database import async_session
from app.dedup import canonical_url_hash, compute_perceptual_hash, hash_distance
from app.filters import is_excluded_brand, is_excluded_category, passes_basic_quality
from app.models import Product, ProductImage, SourceRun, StyleSignal
from app.scoring import score_product
from app.attribute_extraction import extract_attributes
from app.image_ranker import rank_image_urls

logger = logging.getLogger("sogo.ingestion")

IMAGE_ROLES = ["main", "detail", "back_or_angle"]


async def _load_style_weights(session: AsyncSession) -> dict[str, float]:
    result = await session.execute(select(StyleSignal))
    weights = {}
    for row in result.scalars():
        weights[f"{row.signal_type}:{row.signal_value}"] = row.weight
    return weights


async def run_source(adapter: BaseSourceAdapter, session: AsyncSession, style_weights: dict[str, float]) -> SourceRun:
    run = SourceRun(source_name=adapter.source_name, status="disabled")
    session.add(run)
    await session.flush()

    health = await adapter.health_check()
    run.status = health.status
    if health.status in ("disabled", "blocked"):
        run.error_message = health.detail
        run.finished_at = datetime.now(timezone.utc)
        await session.commit()
        return run

    try:
        raw_products = await adapter.fetch_new_products(limit=100)
        run.items_found = len(raw_products)

        new_count = 0
        for raw in raw_products:
            combined_text = f"{raw.title} {raw.category or ''}"
            if is_excluded_brand(raw.brand):
                continue
            if is_excluded_category(combined_text):
                continue
            ok, _reason = passes_basic_quality(raw.title, raw.canonical_url, raw.image_urls)
            if not ok:
                continue

            url_hash = canonical_url_hash(raw.canonical_url)
            existing = await session.execute(select(Product).where(Product.canonical_url_hash == url_hash))
            if existing.scalar_one_or_none():
                continue  # zaten var, tekrar gönderilmeyecek

            scores = score_product(raw, style_weights)
            product = Product(
                source_name=raw.source_name,
                brand=raw.brand,
                title=raw.title,
                canonical_url=raw.canonical_url,
                canonical_url_hash=url_hash,
                category=raw.category,
                price=raw.price,
                currency=raw.currency,
                published_at=raw.published_at,
                score_commercial=scores["commercial"],
                score_originality=scores["originality"],
                score_premium=scores["premium"],
                score_sogo_fit=scores["sogo_fit"],
                score_trend=scores["trend"],
                attributes=extract_attributes(f"{raw.title} {raw.category or ''} {raw.raw_metadata}"),
                raw_metadata=raw.raw_metadata,
            )
            session.add(product)
            await session.flush()

            seen_hashes: list[str] = []
            selected_count = 0
            ranked_images = rank_image_urls(raw.image_urls)
            for img_url in ranked_images[:8]:
                if selected_count >= 3:
                    break
                phash = await compute_perceptual_hash(img_url)
                if phash and any(hash_distance(phash, h) <= 2 for h in seen_hashes):
                    continue  # bu üründe zaten çok benzer görsel var, tekrar ekleme
                if phash:
                    seen_hashes.append(phash)
                session.add(ProductImage(
                    product_id=product.id,
                    url=img_url,
                    role=IMAGE_ROLES[selected_count],
                    order_index=selected_count,
                    perceptual_hash=phash,
                ))
                selected_count += 1
            new_count += 1

        run.items_new = new_count
        run.status = "healthy"
    except Exception as e:
        logger.exception("Source %s failed", adapter.source_name)
        run.status = "degraded"
        run.error_message = str(e)[:500]
    finally:
        run.finished_at = datetime.now(timezone.utc)
        await session.commit()

    return run


async def run_full_scan() -> list[SourceRun]:
    """Tüm kaynakları tarar. Bir kaynağın çökmesi diğerlerini durdurmaz."""
    runs = []
    async with async_session() as session:
        style_weights = await _load_style_weights(session)
        for adapter in get_all_sources():
            run = await run_source(adapter, session, style_weights)
            runs.append(run)
    return runs

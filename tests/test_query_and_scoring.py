from datetime import datetime, timezone, timedelta

from app.attribute_extraction import extract_attributes
from app.image_ranker import rank_image_urls
from app.query_planner import build_queries
from app.schemas import RawProduct
from app.trend_engine import trend_score


def test_query_planner_has_all_languages():
    rows = build_queries(per_language_limit=2, include_brands=False)
    assert {r["language"] for r in rows} == {"tr", "en", "ru", "zh", "it"}


def test_multilingual_attributes():
    attrs = extract_attributes("женский велюровый костюм полумолния вышивка бордо")
    assert "velour" in attrs["fabric"]
    assert "half_zip" in attrs["collar"]
    assert "embroidery" in attrs["detail"]
    assert "burgundy" in attrs["color"]


def test_trend_score_rewards_recency():
    recent = RawProduct(
        source_name="x", brand="b", title="new arrivals women set", canonical_url="https://x.test/p/1",
        image_urls=["https://x.test/a.jpg"], published_at=datetime.now(timezone.utc) - timedelta(hours=3),
        source_confidence=0.8,
    )
    old = recent.model_copy(update={"published_at": datetime.now(timezone.utc) - timedelta(days=60), "title": "women set"})
    assert trend_score(recent) > trend_score(old)


def test_image_ranker_demotes_thumbnails():
    urls = ["https://x.test/thumb.jpg", "https://x.test/product-main.jpg", "https://x.test/detail.webp"]
    ranked = rank_image_urls(urls)
    assert ranked[-1].endswith("thumb.jpg")

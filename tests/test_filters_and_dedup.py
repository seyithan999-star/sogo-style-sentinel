from app.filters import is_excluded_brand, is_excluded_category, passes_basic_quality
from app.dedup import normalize_url, canonical_url_hash, normalize_title_brand, hash_distance
from app.scoring import score_product
from app.schemas import RawProduct


def test_excluded_brand_detected():
    assert is_excluded_brand("Zara") is True
    assert is_excluded_brand("H&M") is True
    assert is_excluded_brand("Anine Bing") is False


def test_excluded_category_detected():
    assert is_excluded_category("Women's Denim Jeans") is True
    assert is_excluded_category("Kids Bikini Swimwear") is True
    assert is_excluded_category("Premium Velour Set") is False


def test_quality_filter_rejects_category_page():
    ok, reason = passes_basic_quality(
        "All Products", "https://store.com/collections/all", ["https://x.com/a.jpg"]
    )
    assert ok is False
    assert reason == "category_page_link"


def test_quality_filter_accepts_valid_product():
    ok, reason = passes_basic_quality(
        "Premium Velour Set", "https://store.com/products/velour-set-123", ["https://x.com/a.jpg"]
    )
    assert ok is True
    assert reason is None


def test_url_normalization_strips_tracking_params():
    a = canonical_url_hash("https://store.com/products/item?utm_source=ig&color=black")
    b = canonical_url_hash("https://store.com/products/item?color=black")
    assert a == b


def test_url_normalization_different_products_differ():
    a = canonical_url_hash("https://store.com/products/item-a")
    b = canonical_url_hash("https://store.com/products/item-b")
    assert a != b


def test_scoring_produces_bounded_values():
    raw = RawProduct(
        source_name="test",
        brand="Toteme",
        title="Embroidered Half Zip Premium Velour Matching Set",
        canonical_url="https://store.com/products/x",
        image_urls=["https://x.com/a.jpg"],
        category="sweatshirt",
    )
    scores = score_product(raw)
    assert 0 <= scores["sogo_fit"] <= 100
    assert 0 <= scores["commercial"] <= 10
    assert 0 <= scores["premium"] <= 10

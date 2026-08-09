"""
Şartname Bölüm 4/5: kalıcı olarak hariç tutulacak markalar, kategoriler ve kalite filtresi.
Bu listeler dashboard/DB üzerinden genişletilebilir olacak şekilde tasarlanmıştır
(EXCLUDED_BRANDS ve EXCLUDED_KEYWORDS başlangıç değeridir, BotSetting tablosunda override edilebilir).
"""

EXCLUDED_BRANDS_DEFAULT = {
    "zara", "mango", "h&m", "hm", "shein", "primark", "forever21", "forever 21",
    "topshop", "gap",
}

EXCLUDED_CATEGORY_KEYWORDS = {
    # iç çamaşırı / lingerie / mayo
    "lingerie", "bra", "iç çamaşırı", "ic camasiri", "underwear", "bikini", "swimwear", "mayo",
    # denim
    "jean", "jeans", "denim", "kot",
    # cinsiyet/yaş
    "men's", "mens", "erkek", "boys", "kids", "children", "toddler", "baby", "bebek", "çocuk", "cocuk",
    # aksesuar/diğer
    "shoe", "shoes", "ayakkabı", "ayakkabi", "bag", "çanta", "canta", "wallet", "cüzdan", "cuzdan",
    "belt", "kemer", "jewelry", "jewellery", "takı", "taki", "sunglasses", "gözlük", "gozluk",
    "perfume", "parfüm", "parfum", "cosmetic", "kozmetik", "home decor", "ev ürünü", "food", "beverage",
}

MIN_TITLE_LENGTH = 6


def is_excluded_brand(brand: str, extra_excluded: set[str] | None = None) -> bool:
    b = (brand or "").strip().lower()
    excluded = EXCLUDED_BRANDS_DEFAULT | (extra_excluded or set())
    return any(x in b for x in excluded)


def is_excluded_category(text: str) -> bool:
    """title + category birleşik metninde hariç tutulan kategori sinyali var mı kontrol eder."""
    t = (text or "").strip().lower()
    return any(kw in t for kw in EXCLUDED_CATEGORY_KEYWORDS)


def passes_basic_quality(title: str, canonical_url: str, image_urls: list[str]) -> tuple[bool, str | None]:
    """Bozuk görsel / kategori sayfası linki / alakasız sonuç filtresi (temel seviye)."""
    if not title or len(title.strip()) < MIN_TITLE_LENGTH:
        return False, "title_too_short"
    if not canonical_url or not canonical_url.startswith("http"):
        return False, "invalid_url"
    # Kategori sayfası linki heuristiği: /collections/, /category/, /c/ gibi genel sayfalar ürün değildir
    lowered = canonical_url.lower()
    category_page_markers = ["/collections/all", "/category/", "/categories/", "/search?", "/c/"]
    if any(m in lowered for m in category_page_markers) and "/products/" not in lowered and "/product/" not in lowered:
        return False, "category_page_link"
    if not image_urls:
        return False, "no_images"
    return True, None

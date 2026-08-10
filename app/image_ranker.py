"""Ranks candidate product images before perceptual-dedup selection."""
from urllib.parse import urlparse

BAD_MARKERS = ["thumb", "thumbnail", "swatch", "logo", "icon", "placeholder", "sprite"]
GOOD_MARKERS = ["front", "main", "hero", "product", "detail", "back", "side", "zoom"]


def image_url_score(url: str, index: int = 0) -> float:
    u = (url or "").lower()
    score = max(0.0, 5.0 - index * 0.15)
    score += sum(0.7 for x in GOOD_MARKERS if x in u)
    score -= sum(2.0 for x in BAD_MARKERS if x in u)
    path = urlparse(u).path
    if any(path.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
        score += 0.5
    return score


def rank_image_urls(urls: list[str]) -> list[str]:
    unique = []
    seen = set()
    for url in urls:
        if not url or url in seen:
            continue
        seen.add(url)
        unique.append(url)
    return [u for _, u in sorted(((image_url_score(u, i), u) for i, u in enumerate(unique)), reverse=True)]

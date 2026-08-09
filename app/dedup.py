"""
Şartname Bölüm 13: Duplicate/tekrar ürün koruması.
Canonical URL hash + normalize brand/title + image perceptual hash birlikte kullanılır.
Kalıcılık veritabanı seviyesindeki UNIQUE constraint'lerle garanti edilir (bkz. models.py).
"""
import hashlib
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

import httpx
import imagehash
from PIL import Image
from io import BytesIO


def normalize_url(url: str) -> str:
    """Tracking parametrelerini temizler, protokol/host'u normalize eder."""
    parts = urlsplit(url.strip())
    # utm_*, ref, fbclid gibi tracking query paramlarını at
    query = [
        (k, v) for k, v in parse_qsl(parts.query)
        if not k.lower().startswith(("utm_", "fbclid", "gclid", "ref", "src"))
    ]
    clean = parts._replace(
        scheme=parts.scheme.lower(),
        netloc=parts.netloc.lower(),
        path=parts.path.rstrip("/"),
        query=urlencode(sorted(query)),
        fragment="",
    )
    return urlunsplit(clean)


def canonical_url_hash(url: str) -> str:
    return hashlib.sha256(normalize_url(url).encode("utf-8")).hexdigest()


def normalize_title_brand(brand: str, title: str) -> str:
    text = f"{brand} {title}".lower()
    text = re.sub(r"[^a-z0-9ğüşıöç\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def compute_perceptual_hash(image_url: str, timeout: float = 10.0) -> str | None:
    """Görseli indirir ve perceptual hash (pHash) hesaplar. Ağ hatasında None döner, sistem çökmez."""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(image_url)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content)).convert("RGB")
            return str(imagehash.phash(img))
    except Exception:
        return None


def hash_distance(hash_a: str, hash_b: str) -> int:
    try:
        return imagehash.hex_to_hash(hash_a) - imagehash.hex_to_hash(hash_b)
    except Exception:
        return 999

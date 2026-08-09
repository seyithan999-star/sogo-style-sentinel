"""
Kaynak Adaptör Standardı (şartname bölüm 22).
Her adapter bu modele normalize edilmiş ürünler üretmek zorundadır.
"""
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field


class RawProductImage(BaseModel):
    url: str
    role_hint: str | None = None  # main/detail/back_or_angle tahmini, opsiyonel


class RawProduct(BaseModel):
    source_name: str
    brand: str
    title: str
    canonical_url: str
    image_urls: list[str] = Field(default_factory=list)
    category: str | None = None
    price: float | None = None
    currency: str | None = None
    published_at: datetime | None = None
    raw_metadata: dict = Field(default_factory=dict)
    source_confidence: float = 0.7  # 0-1, adapter kendi güven skorunu verir


class SourceHealthResult(BaseModel):
    source_name: str
    status: str  # healthy | degraded | blocked | disabled
    detail: str | None = None

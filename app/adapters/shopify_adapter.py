"""
GERÇEK ÇALIŞAN ADAPTER.
Çoğu bağımsız/premium marka mağazası Shopify altyapısı kullanır ve halka açık
`{domain}/products.json?limit=..&order=created_at desc` endpoint'ini sunar - resmi bir
scraping-bypass değildir, mağazanın kendi herkese açık storefront API'sidir.

Kullanım: her marka için bir ShopifyAdapter("marka-adi", "https://marka-magazasi.com") oluşturulur.
Bu liste dashboard/BotSetting üzerinden yönetilecek şekilde genişletilebilir (bkz. README).
"""
import httpx
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.adapters.base import BaseSourceAdapter
from app.schemas import RawProduct, SourceHealthResult


class ShopifyAdapter(BaseSourceAdapter):
    def __init__(self, brand_name: str, store_domain: str):
        # store_domain örn: "https://www.example-boutique.com"
        self.brand_name = brand_name
        self.store_domain = store_domain.rstrip("/")
        self.source_name = f"shopify:{brand_name.lower().replace(' ', '_')}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True,
    )
    async def _get(self, client: httpx.AsyncClient, url: str, params: dict | None = None) -> httpx.Response:
        resp = await client.get(url, params=params, timeout=15.0)
        return resp

    async def health_check(self) -> SourceHealthResult:
        url = f"{self.store_domain}/products.json"
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await self._get(client, url, params={"limit": 1})
            if resp.status_code == 200 and "products" in resp.json():
                return SourceHealthResult(source_name=self.source_name, status="healthy")
            if resp.status_code == 429:
                return SourceHealthResult(source_name=self.source_name, status="degraded", detail="rate_limited_429")
            if resp.status_code == 403:
                return SourceHealthResult(source_name=self.source_name, status="blocked", detail="forbidden_403")
            return SourceHealthResult(
                source_name=self.source_name, status="degraded", detail=f"unexpected_status_{resp.status_code}"
            )
        except Exception as e:
            return SourceHealthResult(source_name=self.source_name, status="blocked", detail=str(e)[:200])

    async def fetch_new_products(self, limit: int = 100) -> list[RawProduct]:
        url = f"{self.store_domain}/products.json"
        results: list[RawProduct] = []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await self._get(client, url, params={"limit": min(limit, 250), "order": "created_at desc"})
            resp.raise_for_status()
            data = resp.json()

        for p in data.get("products", []):
            images = [img.get("src") for img in p.get("images", []) if img.get("src")]
            if not images:
                continue
            variant = (p.get("variants") or [{}])[0]
            price = None
            try:
                price = float(variant.get("price")) if variant.get("price") else None
            except (TypeError, ValueError):
                price = None

            created_at = None
            if p.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(p["created_at"].replace("Z", "+00:00"))
                except ValueError:
                    created_at = None

            handle = p.get("handle", "")
            product_url = f"{self.store_domain}/products/{handle}" if handle else self.store_domain

            results.append(RawProduct(
                source_name=self.source_name,
                brand=p.get("vendor") or self.brand_name,
                title=p.get("title", ""),
                canonical_url=product_url,
                image_urls=images[:3],
                category=p.get("product_type"),
                price=price,
                currency=None,  # Shopify storefront JSON currency vermez; checkout/locale'e bağlıdır
                published_at=created_at,
                raw_metadata={"tags": p.get("tags", ""), "shopify_id": p.get("id")},
                source_confidence=0.85,
            ))
        return results

"""Configurable, licensed web-search provider adapter.

This does not bypass websites. It calls a user-configured JSON search endpoint and converts
organic/product search results into RawProduct objects. This lets one authorized provider cover
retail, Russian/Chinese sources, Pinterest/Instagram indexed pages, and brand searches.

Expected response can be Serper-like (organic/items/results arrays); unknown shapes degrade cleanly.
"""
import httpx
from urllib.parse import urlparse
from app.adapters.base import BaseSourceAdapter
from app.schemas import RawProduct, SourceHealthResult
from app.query_planner import build_queries
from app.source_catalog import ALL_RESEARCH_DOMAINS


class SearchProviderAdapter(BaseSourceAdapter):
    source_name = "licensed_search_provider"

    def __init__(self, endpoint: str, api_key: str, max_queries: int = 30, domains: list[str] | None = None, auth_header: str = "X-API-KEY"):
        self.endpoint = (endpoint or "").strip()
        self.api_key = (api_key or "").strip()
        self.max_queries = max(1, max_queries)
        self.domains = domains or ALL_RESEARCH_DOMAINS
        self.auth_header = (auth_header or "X-API-KEY").strip()
        self.requires_manual_access_setup = not bool(self.endpoint and self.api_key)

    async def health_check(self) -> SourceHealthResult:
        if not self.endpoint or not self.api_key:
            return SourceHealthResult(source_name=self.source_name, status="disabled", detail="SEARCH_PROVIDER_URL/KEY not configured")
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                rows = await self._search(client, "women sweatshirt new arrivals", 1)
            return SourceHealthResult(source_name=self.source_name, status="healthy", detail=f"provider reachable; probe results={len(rows)}")
        except Exception as e:
            return SourceHealthResult(source_name=self.source_name, status="degraded", detail=f"provider probe failed: {str(e)[:160]}")

    def _headers(self) -> dict[str, str]:
        return {self.auth_header: self.api_key, "Content-Type": "application/json"}

    @staticmethod
    def _rows(data: dict) -> list[dict]:
        for key in ("organic", "items", "results", "products"):
            rows = data.get(key)
            if isinstance(rows, list):
                return [r for r in rows if isinstance(r, dict)]
        return []

    async def _search(self, client: httpx.AsyncClient, query: str, limit: int) -> list[dict]:
        payload = {"q": query, "num": min(limit, 20)}
        resp = await client.post(self.endpoint, json=payload, headers=self._headers(), timeout=25.0)
        resp.raise_for_status()
        return self._rows(resp.json())

    async def fetch_new_products(self, limit: int = 100) -> list[RawProduct]:
        queries = build_queries(per_language_limit=6)
        results: list[RawProduct] = []
        seen_urls: set[str] = set()
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for query_index, item in enumerate(queries[: self.max_queries]):
                if len(results) >= limit:
                    break
                query = item["query"]
                # rotate domain constraints so Russian/Chinese/global sources all receive coverage
                domain = self.domains[query_index % len(self.domains)] if self.domains else None
                full_query = f"site:{domain} {query}" if domain else query
                try:
                    rows = await self._search(client, full_query, min(10, limit - len(results)))
                except Exception:
                    continue
                for row in rows:
                    url = row.get("link") or row.get("url")
                    title = row.get("title") or row.get("name") or ""
                    image = row.get("imageUrl") or row.get("image") or row.get("thumbnail")
                    images = row.get("images") if isinstance(row.get("images"), list) else []
                    if image:
                        images = [image] + images
                    if not url or url in seen_urls or not images:
                        continue
                    seen_urls.add(url)
                    host = urlparse(url).netloc.replace("www.", "")
                    brand = row.get("brand") or host.split(".")[0].replace("-", " ").title()
                    results.append(RawProduct(
                        source_name=f"search:{host}", brand=brand, title=title, canonical_url=url,
                        image_urls=images[:8], category=row.get("category"),
                        price=row.get("price") if isinstance(row.get("price"), (int, float)) else None,
                        currency=row.get("currency"), raw_metadata={"query": full_query, "language": item["language"], "search_provider": True},
                        source_confidence=0.72,
                    ))
                    if len(results) >= limit:
                        break
        return results

"""Source registry.

The registry exposes direct adapters plus authorization-aware research adapters. Sources that
require credentials remain explicitly disabled rather than silently returning zero products.
"""
from app.adapters.shopify_adapter import ShopifyAdapter
from app.adapters.manual_access_adapter import ManualAccessAdapter
from app.adapters.search_provider_adapter import SearchProviderAdapter
from app.adapters.base import BaseSourceAdapter
from app.config import settings

# Verified Shopify storefronts can be added here. Keep domains verified before enabling.
SHOPIFY_SOURCES: list[BaseSourceAdapter] = []

SEARCH_SOURCES: list[BaseSourceAdapter] = [
    SearchProviderAdapter(
        settings.search_provider_url,
        settings.search_provider_key,
        max_queries=settings.search_provider_max_queries,
        auth_header=settings.search_provider_auth_header,
    )
]

MANUAL_ACCESS_SOURCES: list[BaseSourceAdapter] = [
    ManualAccessAdapter("instagram", "Use Meta/authorized discovery or the licensed search provider; direct scraping is not enabled"),
    ManualAccessAdapter("pinterest", "Use Pinterest/authorized access or the licensed search provider"),
    ManualAccessAdapter("xiaohongshu_red", "Use licensed/authorized provider access"),
    ManualAccessAdapter("douyin", "Use licensed/authorized provider access"),
    ManualAccessAdapter("weibo", "Use official/authorized access"),
    ManualAccessAdapter("wildberries", "Direct adapter not enabled; coverage available through configured search provider"),
    ManualAccessAdapter("ozon", "Direct adapter not enabled; coverage available through configured search provider"),
    ManualAccessAdapter("lamoda", "Direct adapter not enabled; coverage available through configured search provider"),
    ManualAccessAdapter("farfetch", "Partner/direct adapter not enabled; coverage available through configured search provider"),
    ManualAccessAdapter("yoox_net_a_porter", "Partner/direct adapter not enabled; coverage available through configured search provider"),
    ManualAccessAdapter("pantone", "Use official/public trend pages or MANUAL_COLOR_PALETTE; proprietary swatch scraping is not enabled"),
]


def get_all_sources() -> list[BaseSourceAdapter]:
    return SHOPIFY_SOURCES + SEARCH_SOURCES + MANUAL_ACCESS_SOURCES

"""Curated research universe for SOGO Style Sentinel.

This module intentionally separates *what to monitor* from *how to access it*.
Some platforms require an official API, partner access, or a licensed search provider.
The bot never pretends an unavailable source is healthy.
"""

PREMIUM_BRANDS = [
    "Valentino", "Prada", "Miu Miu", "Loewe", "Celine", "Bottega Veneta",
    "Saint Laurent", "Givenchy", "Balmain", "Alexander McQueen", "Chloe",
    "Stella McCartney", "Lanvin", "Oscar de la Renta", "Jacquemus",
    "JW Anderson", "Off-White", "Brunello Cucinelli", "Loro Piana",
    "Moncler", "Max Mara", "Sportmax", "Weekend Max Mara", "Peserico",
    "Fabiana Filippi", "Eleventy", "Moorer", "Herno", "Pinko", "Patrizia Pepe",
    "Twinset", "Vicolo", "Imperial", "Souvenir", "Molecola", "Sporty & Rich",
    "Alo Yoga", "Varley", "Lululemon", "Oysho", "Bogner", "Khaite",
    "Toteme", "The Row", "Ami Paris", "Acne Studios", "Ganni", "Marni",
    "Maison Kitsune", "Kenzo", "Diesel", "Michael Kors", "Coach", "Theory",
]

INSTAGRAM_ACCOUNTS = [
    "farfetch", "yoox", "luisaviaroma", "modes", "vitkac", "giglio.com",
    "julianfashion", "bernardellistores", "netaporter", "mytheresa",
    "ssense", "matchesfashion", "brownsfashion", "harrods", "selfridges",
    "tsum_moscow", "lamoda_ru", "wildberriesru", "ozonfashion",
]

RETAIL_SOURCES = [
    {"name": "Farfetch", "domain": "farfetch.com", "region": "global"},
    {"name": "YOOX", "domain": "yoox.com", "region": "global"},
    {"name": "LuisaViaRoma", "domain": "luisaviaroma.com", "region": "italy"},
    {"name": "MODES", "domain": "modes.com", "region": "italy"},
    {"name": "VITKAC", "domain": "vitkac.com", "region": "europe"},
    {"name": "Giglio", "domain": "giglio.com", "region": "italy"},
    {"name": "Julian Fashion", "domain": "julian-fashion.com", "region": "italy"},
    {"name": "Bernardelli", "domain": "bernardellistores.com", "region": "italy"},
    {"name": "Mytheresa", "domain": "mytheresa.com", "region": "global"},
    {"name": "NET-A-PORTER", "domain": "net-a-porter.com", "region": "global"},
    {"name": "SSENSE", "domain": "ssense.com", "region": "global"},
    {"name": "TSUM", "domain": "tsum.ru", "region": "russia"},
    {"name": "Lamoda", "domain": "lamoda.ru", "region": "russia"},
    {"name": "Wildberries", "domain": "wildberries.ru", "region": "russia"},
    {"name": "Ozon Fashion", "domain": "ozon.ru", "region": "russia"},
    {"name": "Tmall", "domain": "tmall.com", "region": "china"},
    {"name": "Taobao", "domain": "taobao.com", "region": "china"},
    {"name": "JD", "domain": "jd.com", "region": "china"},
    {"name": "1688", "domain": "1688.com", "region": "china"},
]

SOCIAL_RESEARCH_SOURCES = [
    {"name": "Instagram", "domain": "instagram.com", "access": "official_or_licensed"},
    {"name": "Pinterest", "domain": "pinterest.com", "access": "official_or_licensed"},
    {"name": "Xiaohongshu RED", "domain": "xiaohongshu.com", "access": "licensed_provider"},
    {"name": "Douyin", "domain": "douyin.com", "access": "licensed_provider"},
    {"name": "Weibo", "domain": "weibo.com", "access": "official_or_licensed"},
]

COLOR_RESEARCH_SOURCES = [
    {"name": "Pantone", "domain": "pantone.com", "note": "Use official/public trend pages or a manually curated palette; do not scrape proprietary swatch data."},
    {"name": "Pinterest Color", "domain": "pinterest.com", "note": "Use official/authorized access or licensed search results."},
]

ALL_RESEARCH_DOMAINS = [x["domain"] for x in RETAIL_SOURCES + SOCIAL_RESEARCH_SOURCES + COLOR_RESEARCH_SOURCES]

"""Multilingual search-plan generator for SOGO's target product universe."""
from itertools import product
from app.source_catalog import PREMIUM_BRANDS

CATEGORY_TERMS = {
    "tr": ["kadın sweatshirt", "kadın takım", "kadife takım", "yarım fermuarlı takım", "büyük beden takım"],
    "en": ["women sweatshirt", "women matching set", "velour tracksuit women", "half zip set women", "plus size tracksuit women"],
    "ru": ["женский свитшот", "женский костюм", "женский велюровый костюм", "женский костюм с молнией до половины", "женский костюм больших размеров"],
    "zh": ["女式卫衣", "女式套装", "女式天鹅绒套装", "女式半拉链套装", "大码女装套装"],
    "it": ["felpa donna", "completo donna", "tuta donna in velluto", "completo donna mezza zip", "tuta donna taglie forti"],
}

DETAIL_TERMS = {
    "tr": ["garni", "şerit detay", "nakış", "premium", "spor şık", "yandan kesik", "fitilli", "taş detay"],
    "en": ["contrast trim", "stripe detail", "embroidered", "premium", "sports luxe", "side panel", "ribbed texture", "crystal detail"],
    "ru": ["контрастная отделка", "полосы", "вышивка", "премиум", "спорт шик", "боковая вставка", "фактурный", "стразы"],
    "zh": ["撞色饰边", "条纹细节", "刺绣", "高级感", "运动时尚", "侧拼接", "纹理", "水钻"],
    "it": ["profilo a contrasto", "dettaglio a righe", "ricamo", "premium", "sport chic", "pannello laterale", "texture", "cristalli"],
}

FRESHNESS_TERMS = {
    "tr": ["yeni sezon", "yeni koleksiyon"],
    "en": ["new arrivals", "new collection"],
    "ru": ["новинки", "новая коллекция"],
    "zh": ["新品", "新款"],
    "it": ["nuovi arrivi", "nuova collezione"],
}


def build_queries(per_language_limit: int = 18, include_brands: bool = True) -> list[dict]:
    rows: list[dict] = []
    for lang, categories in CATEGORY_TERMS.items():
        details = DETAIL_TERMS[lang]
        fresh = FRESHNESS_TERMS[lang]
        combos = []
        for category, detail, freshness in product(categories, details[:4], fresh):
            combos.append(f"{category} {detail} {freshness}")
        for q in combos[:per_language_limit]:
            rows.append({"language": lang, "query": q, "kind": "category"})

    if include_brands:
        for brand in PREMIUM_BRANDS:
            rows.append({"language": "en", "query": f'"{brand}" women new arrivals sweatshirt set', "kind": "brand"})
    return rows


def compact_hashtags() -> dict[str, list[str]]:
    return {
        "en": ["#womensweatshirt", "#womenset", "#velourset", "#halfzip", "#sportsluxe", "#newarrivals"],
        "ru": ["#женскийсвитшот", "#женскийкостюм", "#велюровыйкостюм", "#спортшик", "#новинки"],
        "zh": ["#女式卫衣", "#女式套装", "#天鹅绒套装", "#半拉链", "#新品女装"],
        "it": ["#felpadonna", "#completodonna", "#tutadonna", "#mezzazip", "#nuoviarrivi"],
    }

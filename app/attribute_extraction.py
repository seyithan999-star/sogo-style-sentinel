"""Lightweight multilingual attribute extraction used by scoring and feedback learning."""

ATTRIBUTE_TERMS = {
    "fabric": {
        "velour": ["velour", "velvet", "kadife", "велюр", "бархат", "天鹅绒", "velluto"],
        "knit": ["knit", "triko", "трикотаж", "针织", "maglia"],
    },
    "collar": {
        "half_zip": ["half zip", "half-zip", "yarım fermuar", "полумолния", "半拉链", "mezza zip"],
        "crewneck": ["crewneck", "bisiklet yaka", "круглый вырез", "圆领", "girocollo"],
    },
    "detail": {
        "embroidery": ["embroidered", "embroidery", "nakış", "вышив", "刺绣", "ricamo"],
        "stripe": ["stripe", "şerit", "полос", "条纹", "riga"],
        "contrast_panel": ["contrast panel", "garni", "контраст", "撞色", "contrasto"],
        "crystal": ["crystal", "rhinestone", "taş", "страз", "水钻", "cristall"],
    },
    "silhouette": {
        "matching_set": ["matching set", "two piece", "takım", "костюм", "套装", "completo"],
        "sweatshirt": ["sweatshirt", "sweat", "свитшот", "卫衣", "felpa"],
        "plus_size": ["plus size", "büyük beden", "больших размеров", "大码", "taglie forti"],
    },
    "style": {
        "sports_luxe": ["sports luxe", "sport chic", "spor şık", "спорт шик", "运动时尚"],
        "premium": ["premium", "luxury", "quiet luxury", "премиум", "高级感", "lusso"],
    },
    "color": {
        "black": ["black", "siyah", "черн", "黑色", "nero"],
        "ecru": ["ecru", "ekru", "экрю", "米白", "ecru"],
        "stone": ["stone", "taş", "камен", "石色", "pietra"],
        "mink": ["mink", "vizon", "норк", "貂色", "visone"],
        "chocolate": ["chocolate", "kahve", "шоколад", "巧克力", "cioccolato"],
        "anthracite": ["anthracite", "antrasit", "антрацит", "炭灰", "antracite"],
        "burgundy": ["burgundy", "bordo", "бордо", "酒红", "bordeaux"],
    },
}


def extract_attributes(text: str) -> dict[str, list[str]]:
    t = (text or "").lower()
    out: dict[str, list[str]] = {}
    for group, mapping in ATTRIBUTE_TERMS.items():
        hits = [canonical for canonical, variants in mapping.items() if any(v.lower() in t for v in variants)]
        if hits:
            out[group] = hits
    return out

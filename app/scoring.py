"""
Şartname Bölüm 14: Puanlama Motoru.
İlk sürüm: kurallı puanlama (anahtar kelime + öğrenilen style_signals ağırlıkları).
İleride: seçili ürünlerde AI vision/LLM destekli detay analizi eklenebilir (bkz. score_with_llm_stub).
"""
from app.schemas import RawProduct
from app.trend_engine import trend_score
from app.attribute_extraction import extract_attributes

PREMIUM_KEYWORDS = [
    "embroidered", "nakış", "velour", "kadife", "half zip", "yarım fermuar", "half-zip",
    "contrast panel", "garni", "şerit", "knit set", "triko", "cashmere", "silk", "italian",
    "quiet luxury", "sports luxe", "athleisure", "designer", "premium", "luxury",
]

COMMERCIAL_KEYWORDS = [
    "matching set", "two piece", "set", "takım", "tracksuit", "eşofman", "sweatshirt", "crewneck",
    "loungewear",
]

TARGET_COLORS = [
    "black", "siyah", "ecru", "ekru", "taş", "stone", "vizon", "mink", "chocolate", "kahve",
    "anthracite", "antrasit", "grey", "gray", "gri", "khaki", "haki", "burgundy", "bordo", "indigo",
]


def _keyword_score(text: str, keywords: list[str], max_score: float = 10.0) -> float:
    t = text.lower()
    hits = sum(1 for k in keywords if k in t)
    return min(max_score, hits * (max_score / 4))  # 4+ eşleşme tam puan


def score_product(raw: RawProduct, style_weights: dict[str, float] | None = None) -> dict:
    """
    Döner: {commercial, originality, premium, sogo_fit(0-100), trend}
    style_weights: {"color:ekru": 8.2, "fabric:velour": 5.0, ...} gibi öğrenilen ağırlıklar (opsiyonel).
    """
    text = f"{raw.title} {raw.category or ''} {' '.join(str(v) for v in raw.raw_metadata.values())}"
    attrs = extract_attributes(text)

    commercial = _keyword_score(text, COMMERCIAL_KEYWORDS)
    premium = _keyword_score(text, PREMIUM_KEYWORDS)

    # Orijinallik: premium detay yoğunluğu + marka güveni (adapter source_confidence)
    originality = min(10.0, premium * 0.6 + raw.source_confidence * 4)

    # Renk sinyali
    color_hit = any(c in text.lower() for c in TARGET_COLORS)

    base_fit = (commercial * 3 + premium * 4 + originality * 3)  # 0-100 aralığına yakın taban
    if color_hit:
        base_fit += 8

    # Öğrenilen style_signals ağırlıklarını uygula (pozitif/negatif geri bildirimden gelir)
    learned_bonus = 0.0
    if style_weights:
        for key, weight in style_weights.items():
            _, _, value = key.partition(":")
            if value and value.lower() in text.lower():
                learned_bonus += weight

    sogo_fit = max(0.0, min(100.0, base_fit + learned_bonus))

    return {
        "commercial": round(commercial, 1),
        "originality": round(originality, 1),
        "premium": round(premium, 1),
        "sogo_fit": round(sogo_fit, 1),
        "trend": trend_score(raw),
    }


def score_with_llm_stub(raw: RawProduct) -> dict | None:
    """
    Faz 2 yer tutucusu: seçili yüksek potansiyelli ürünlerde görsel + metin analiz için
    Anthropic API (claude-sonnet) çağrısı buraya eklenebilir. Şu an bilinçli olarak
    devre dışı - sahte/placeholder skor üretmemek için None döner.
    """
    return None

"""Transparent trend score based on recency, source confidence and freshness signals."""
from datetime import datetime, timezone
from app.schemas import RawProduct

FRESH_WORDS = ["new", "new arrival", "new collection", "yeni", "новин", "新品", "nuovi arrivi"]


def trend_score(raw: RawProduct) -> float:
    score = 0.0
    if raw.published_at:
        dt = raw.published_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_h = max(0.0, (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 3600)
        if age_h <= 24:
            score += 7.0
        elif age_h <= 72:
            score += 5.0
        elif age_h <= 168:
            score += 3.0
        elif age_h <= 720:
            score += 1.0
    text = f"{raw.title} {raw.category or ''}".lower()
    if any(w in text for w in FRESH_WORDS):
        score += 1.5
    score += max(0.0, min(1.0, raw.source_confidence)) * 1.5
    return round(min(10.0, score), 1)

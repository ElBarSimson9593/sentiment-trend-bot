from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AlertLog, Mention


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def count_recent_negatives(db: Session, brand: str, window_minutes: int) -> tuple[int, float]:
    since = _utcnow() - timedelta(minutes=window_minutes)
    rows = (
        db.query(Mention.sentiment_score, Mention.created_at)
        .filter(Mention.brand == brand, Mention.label == "negative")
        .all()
    )
    rows = [(score, created_at) for score, created_at in rows if _aware(created_at) >= since]
    if not rows:
        return 0, 0.0
    scores = [score for score, _ in rows]
    return len(scores), sum(scores) / len(scores)


def should_alert(db: Session, brand: str) -> tuple[bool, int, float, str]:
    count, avg_score = count_recent_negatives(
        db, brand, settings.alert_window_minutes
    )
    if count < settings.alert_negative_threshold:
        return False, count, avg_score, ""

    message = (
        f"Posible crisis reputacional para '{brand}': "
        f"{count} menciones negativas en los últimos "
        f"{settings.alert_window_minutes} min (promedio {avg_score:.2f})."
    )
    return True, count, avg_score, message


async def dispatch_webhook(payload: dict) -> bool:
    if not settings.webhook_url:
        return False

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(settings.webhook_url, json=payload)
        response.raise_for_status()
    return True


async def evaluate_and_alert(db: Session, brand: str) -> bool:
    triggered, count, avg_score, message = should_alert(db, brand)
    if not triggered:
        return False

    window_start = _utcnow() - timedelta(minutes=settings.alert_window_minutes)
    recent_alert = next(
        (
            alert
            for alert in db.query(AlertLog).filter(AlertLog.brand == brand).all()
            if _aware(alert.created_at) >= window_start
        ),
        None,
    )
    if recent_alert:
        return False

    log = AlertLog(
        brand=brand,
        negative_count=count,
        avg_score=avg_score,
        message=message,
    )
    db.add(log)
    db.commit()

    await dispatch_webhook(
        {
            "event": "reputation_alert",
            "brand": brand,
            "negative_count": count,
            "avg_sentiment": round(avg_score, 3),
            "window_minutes": settings.alert_window_minutes,
            "message": message,
        }
    )
    return True

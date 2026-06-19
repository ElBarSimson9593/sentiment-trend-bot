from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.demo_seed import ensure_demo_data
from app.models import AlertLog, Mention
from app.schemas import AlertOut, DashboardMetrics, TimelineOut, TimelinePoint

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _since(hours: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=hours)


def _normalize_brand(brand: str) -> str:
    return brand.strip().lower()


def _mentions_for_brand(db: Session, brand: str, since: datetime | None = None) -> list[Mention]:
    rows = db.query(Mention).filter(Mention.brand == brand).order_by(Mention.created_at.asc()).all()
    if since is None:
        return rows
    return [m for m in rows if _aware(m.created_at) >= since]


def _refresh_demo_if_needed(db: Session) -> None:
    if settings.auto_seed_demo:
        ensure_demo_data(db, auto_seed=True)


@router.get("/brands")
def list_brands(db: Session = Depends(get_db)):
    _refresh_demo_if_needed(db)
    rows = db.query(Mention.brand).distinct().order_by(Mention.brand).all()
    return {"brands": [r[0] for r in rows]}


@router.get("/{brand}/metrics", response_model=DashboardMetrics)
def get_metrics(
    brand: str,
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    _refresh_demo_if_needed(db)
    brand = _normalize_brand(brand)
    since = _since(hours)
    mentions = _mentions_for_brand(db, brand, since)

    positive = sum(1 for m in mentions if m.label == "positive")
    neutral = sum(1 for m in mentions if m.label == "neutral")
    negative = sum(1 for m in mentions if m.label == "negative")
    total = len(mentions)
    avg = sum(m.sentiment_score for m in mentions) / total if total else 0.0

    midpoint = since + timedelta(hours=hours / 2)
    first_half = [m for m in mentions if _aware(m.created_at) < midpoint]
    second_half = [m for m in mentions if _aware(m.created_at) >= midpoint]
    first_avg = (
        sum(m.sentiment_score for m in first_half) / len(first_half)
        if first_half
        else 0.0
    )
    second_avg = (
        sum(m.sentiment_score for m in second_half) / len(second_half)
        if second_half
        else 0.0
    )

    if second_avg - first_avg > 0.1:
        trend = "improving"
    elif second_avg - first_avg < -0.1:
        trend = "declining"
    else:
        trend = "stable"

    alert_rows = db.query(AlertLog).filter(AlertLog.brand == brand).all()
    recent_alerts = sum(1 for alert in alert_rows if _aware(alert.created_at) >= since)

    return DashboardMetrics(
        brand=brand,
        hours=hours,
        total_mentions=total,
        positive=positive,
        neutral=neutral,
        negative=negative,
        avg_sentiment=round(avg, 3),
        trend=trend,
        recent_alerts=recent_alerts,
    )


@router.get("/{brand}/timeline", response_model=TimelineOut)
def get_timeline(
    brand: str,
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    _refresh_demo_if_needed(db)
    brand = _normalize_brand(brand)
    since = _since(hours)
    mentions = _mentions_for_brand(db, brand, since)

    bucket_count = 12
    bucket_size = hours / bucket_count
    points: list[TimelinePoint] = []
    for i in range(bucket_count):
        start = since + timedelta(hours=i * bucket_size)
        end = since + timedelta(hours=(i + 1) * bucket_size)
        bucket_rows = [
            m for m in mentions if start <= _aware(m.created_at) < end
        ]
        avg = (
            round(sum(m.sentiment_score for m in bucket_rows) / len(bucket_rows), 3)
            if bucket_rows
            else None
        )
        points.append(
            TimelinePoint(
                bucket=start.strftime("%d/%m %H:%M"),
                avg_score=avg,
                count=len(bucket_rows),
            )
        )

    return TimelineOut(brand=brand, hours=hours, points=points)


@router.get("/{brand}/alerts", response_model=list[AlertOut])
def get_alerts(
    brand: str,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    _refresh_demo_if_needed(db)
    brand = _normalize_brand(brand)
    rows = (
        db.query(AlertLog)
        .filter(AlertLog.brand == brand)
        .order_by(AlertLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [AlertOut.model_validate(row) for row in rows]

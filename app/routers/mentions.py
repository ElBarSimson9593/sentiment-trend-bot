from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.alerts import evaluate_and_alert
from app.database import get_db
from app.models import Mention
from app.schemas import MentionCreate, MentionOut
from app.sentiment import analyze_text

router = APIRouter(prefix="/api/mentions", tags=["mentions"])


@router.post("", response_model=MentionOut, status_code=201)
async def create_mention(payload: MentionCreate, db: Session = Depends(get_db)):
    score, label = analyze_text(payload.text)
    mention = Mention(
        brand=payload.brand.strip().lower(),
        text=payload.text,
        source=payload.source,
        sentiment_score=score,
        label=label,
    )
    db.add(mention)
    db.commit()
    db.refresh(mention)

    alert_triggered = await evaluate_and_alert(db, mention.brand)
    result = MentionOut.model_validate(mention)
    return result.model_copy(update={"alert_triggered": alert_triggered})


@router.get("", response_model=list[MentionOut])
def list_mentions(
    brand: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Mention)
        .filter(Mention.brand == brand.strip().lower())
        .order_by(Mention.created_at.desc())
        .limit(limit)
        .all()
    )
    return [MentionOut.model_validate(row) for row in rows]

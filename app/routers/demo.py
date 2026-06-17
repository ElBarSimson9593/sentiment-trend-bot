from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.alerts import _utcnow, evaluate_and_alert
from app.database import get_db
from app.models import Mention
from app.schemas import CrisisSimulationOut
from app.sentiment import analyze_text

router = APIRouter(prefix="/api/demo", tags=["demo"])

CRISIS_MENTIONS: list[tuple[str, int]] = [
    ("Pésima atención, nunca más vuelvo.", 48),
    ("Me cobraron cosas que no estaban claras en el contrato.", 32),
    ("Estafa total, cuidado con esta empresa.", 16),
]


@router.post("/simulate-crisis", response_model=CrisisSimulationOut)
async def simulate_crisis(
    brand: str = "novahome",
    db: Session = Depends(get_db),
):
    brand = brand.strip().lower()
    now = _utcnow()
    created_ids: list[int] = []

    for text, minutes_ago in CRISIS_MENTIONS:
        score, label = analyze_text(text)
        mention = Mention(
            brand=brand,
            text=text,
            source="demo_crisis",
            sentiment_score=score,
            label=label,
            created_at=now - timedelta(minutes=minutes_ago),
        )
        db.add(mention)
        db.flush()
        created_ids.append(mention.id)

    db.commit()
    alert_triggered = await evaluate_and_alert(db, brand, force=True)

    return CrisisSimulationOut(
        brand=brand,
        mentions_created=len(created_ids),
        mention_ids=created_ids,
        alert_triggered=alert_triggered,
    )

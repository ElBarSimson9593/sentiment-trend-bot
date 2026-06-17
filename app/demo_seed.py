"""Datos de demo repartidos en 24 h para gráficos, KPIs y alertas."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import AlertLog, Mention
from app.sentiment import analyze_text

logger = logging.getLogger(__name__)

# Marca ficticia — no usar empresas reales en portafolio.
DEMO_MENTIONS: list[tuple[str, str, str, int]] = [
    ("novahome", "Excelente atención, muy profesionales.", "google_reviews", 23 * 60),
    ("novahome", "Respondieron rápido y cerraron la venta sin problemas.", "whatsapp", 20 * 60),
    ("novahome", "Buena experiencia en general, recomendable.", "portal_inmobiliario", 18 * 60),
    ("novahome", "El proceso fue normal, sin sorpresas.", "facebook", 14 * 60),
    ("novahome", "Demoraron mucho en responder mis consultas.", "twitter", 10 * 60),
    ("novahome", "El corredor fue amable pero el proceso fue lento.", "instagram", 8 * 60),
    # Tres negativas en la última hora → alerta de crisis reputacional
    ("novahome", "Pésima atención, nunca más vuelvo.", "google_reviews", 45),
    ("novahome", "Me cobraron cosas que no estaban claras en el contrato.", "facebook", 30),
    ("novahome", "Estafa total, cuidado con esta empresa.", "twitter", 15),
    ("urbacorp", "Producto decente por el precio.", "demo", 16 * 60),
    ("urbacorp", "No cumplieron lo prometido.", "demo", 6 * 60),
]


def should_seed_demo(db: Session, *, force_reset: bool = False) -> bool:
    if force_reset:
        return True

    count = db.query(Mention).count()
    if count == 0:
        return True

    # Reemplaza datos de prueba manuales que quedaron todos neutros (VADER en español).
    if count < 20:
        rows = db.query(Mention).all()
        if rows and all(r.label == "neutral" and r.sentiment_score == 0.0 for r in rows):
            return True

    return False


def run_demo_seed(db: Session, *, reset: bool = False) -> int:
    if reset:
        db.query(AlertLog).delete()
        db.query(Mention).delete()
        db.commit()

    now = datetime.now(timezone.utc)
    novahome_negatives: list[float] = []

    for brand, text, source, minutes_ago in DEMO_MENTIONS:
        score, label = analyze_text(text)
        if brand == "novahome" and label == "negative" and minutes_ago <= 60:
            novahome_negatives.append(score)
        db.add(
            Mention(
                brand=brand,
                text=text,
                source=source,
                sentiment_score=score,
                label=label,
                created_at=now - timedelta(minutes=minutes_ago),
            )
        )

    if len(novahome_negatives) >= 3:
        avg = sum(novahome_negatives) / len(novahome_negatives)
        db.add(
            AlertLog(
                brand="novahome",
                negative_count=len(novahome_negatives),
                avg_score=avg,
                message=(
                    f"Posible crisis reputacional para 'novahome': "
                    f"{len(novahome_negatives)} menciones negativas en los últimos "
                    f"60 min (promedio {avg:.2f})."
                ),
                created_at=now - timedelta(minutes=10),
            )
        )

    db.commit()
    return len(DEMO_MENTIONS)


def ensure_demo_data(db: Session, *, auto_seed: bool, force_reset: bool = False) -> None:
    if not auto_seed and not force_reset:
        return

    if not should_seed_demo(db, force_reset=force_reset):
        return

    count = run_demo_seed(db, reset=True)
    logger.info("Demo seed cargado: %s menciones repartidas en 24 h.", count)

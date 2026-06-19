"""Datos de demo repartidos en 24 h para gráficos, KPIs y alertas."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import AlertLog, Mention
from app.sentiment import analyze_text

logger = logging.getLogger(__name__)

DEMO_TEXTS = {
    "Excelente atención, muy profesionales.",
    "Respondieron rápido y cerraron la venta sin problemas.",
    "Buena experiencia en general, recomendable.",
    "El proceso fue normal, sin sorpresas.",
    "Demoraron mucho en responder mis consultas.",
    "El corredor fue amable pero el proceso fue lento.",
    "Pésima atención, nunca más vuelvo.",
    "Me cobraron cosas que no estaban claras en el contrato.",
    "Estafa total, cuidado con esta empresa.",
    "Producto decente por el precio.",
    "No cumplieron lo prometido.",
}

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

_MIN_TIMELINE_SPAN = timedelta(hours=3)
_DEMO_STALE_AFTER = timedelta(hours=20)
_DEMO_WINDOW = timedelta(hours=23)
_DEMO_BRANDS = ("novahome", "urbacorp")


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _mention_time_span(rows: list[Mention]) -> timedelta:
    if len(rows) < 2:
        return timedelta(0)
    timestamps = [_aware(row.created_at) for row in rows]
    return max(timestamps) - min(timestamps)


def _demo_data_stale(db: Session) -> bool:
    """Demo usa ventana de 24 h; sin re-seed el dashboard queda vacío para reclutadores."""
    now = datetime.now(timezone.utc)
    rows = db.query(Mention).filter(Mention.brand.in_(_DEMO_BRANDS)).all()
    if not rows:
        return False

    newest = max(_aware(row.created_at) for row in rows)
    if now - newest > _DEMO_STALE_AFTER:
        return True

    since = now - _DEMO_WINDOW
    novahome_recent = [
        row
        for row in rows
        if row.brand == "novahome" and _aware(row.created_at) >= since
    ]
    return len(novahome_recent) < 5


def should_seed_demo(db: Session, *, force_reset: bool = False) -> bool:
    if force_reset:
        return True

    count = db.query(Mention).count()
    if count == 0:
        return True

    rows = db.query(Mention).all()

    if count < 20 and all(r.label == "neutral" and r.sentiment_score == 0.0 for r in rows):
        return True

    # Pruebas manuales / mini-crisis en pocos minutos → gráfico temporal plano.
    if _mention_time_span(rows) < _MIN_TIMELINE_SPAN:
        return True

    # Dataset distinto al de demo (p. ej. textos "bien", "muy bien" de prueba).
    known_demo_rows = sum(1 for row in rows if row.text in DEMO_TEXTS)
    if known_demo_rows < 3:
        return True

    if _demo_data_stale(db):
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


def refresh_stale_demo_if_needed(db: Session, *, auto_seed: bool) -> None:
    """Solo refresca timestamps del dataset demo; no borra marcas de prueba ajenas."""
    if not auto_seed or not _demo_data_stale(db):
        return

    count = run_demo_seed(db, reset=True)
    logger.info("Demo seed refrescado: %s menciones repartidas en 24 h.", count)

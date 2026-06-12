"""Carga menciones de demo para probar el dashboard y las alertas."""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import Base, SessionLocal, engine
from app.models import AlertLog, Mention
from app.sentiment import analyze_text

# Marca ficticia — no usar empresas reales donde postulas.
# minutes_ago reparte menciones en el tiempo (gráfico temporal + alertas recientes).
DEMO_MENTIONS = [
    ("novahome", "Excelente atención, muy profesionales.", "google_reviews", 23 * 60),
    ("novahome", "Respondieron rápido y cerraron la venta sin problemas.", "whatsapp", 20 * 60),
    ("novahome", "Buena experiencia en general, recomendable.", "portal_inmobiliario", 18 * 60),
    ("novahome", "El proceso fue normal, sin sorpresas.", "facebook", 14 * 60),
    ("novahome", "Demoraron mucho en responder mis consultas.", "twitter", 10 * 60),
    ("novahome", "El corredor fue amable pero el proceso fue lento.", "instagram", 8 * 60),
    # Tres negativos en la última hora → disparan la alerta de demo
    ("novahome", "Pésima atención, nunca más vuelvo.", "google_reviews", 45),
    ("novahome", "Me cobraron cosas que no estaban claras en el contrato.", "facebook", 30),
    ("novahome", "Estafa total, cuidado con esta empresa.", "twitter", 15),
    ("urbacorp", "Producto decente por el precio.", "demo", 16 * 60),
    ("urbacorp", "No cumplieron lo prometido.", "demo", 6 * 60),
]


def main():
    parser = argparse.ArgumentParser(description="Seed de datos demo")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Borra menciones y alertas existentes antes de cargar",
    )
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(Mention).count()
        if existing and not args.reset:
            print(f"Ya hay {existing} menciones. Usa --reset para recargar con fechas repartidas.")
            return

        if args.reset:
            db.query(AlertLog).delete()
            db.query(Mention).delete()
            db.commit()
            print("Datos anteriores eliminados.")

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
        print(f"Seed completado: {len(DEMO_MENTIONS)} menciones repartidas en 24 h.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

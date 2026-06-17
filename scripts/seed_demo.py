"""Carga menciones de demo para probar el dashboard y las alertas."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import Base, SessionLocal, engine
from app.demo_seed import ensure_demo_data, run_demo_seed, should_seed_demo
from app.models import Mention


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
        if args.reset:
            count = run_demo_seed(db, reset=True)
            print(f"Seed completado: {count} menciones repartidas en 24 h.")
            return

        if should_seed_demo(db):
            count = run_demo_seed(db, reset=True)
            print(f"Seed completado: {count} menciones repartidas en 24 h.")
            return

        existing = db.query(Mention).count()
        print(f"Ya hay {existing} menciones. Usa --reset para recargar con fechas repartidas.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

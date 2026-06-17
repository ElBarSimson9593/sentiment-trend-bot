from datetime import datetime, timezone

from app.demo_seed import DEMO_MENTIONS, ensure_demo_data, run_demo_seed, should_seed_demo
from app.models import Mention


def test_should_seed_when_empty(db_session):
    assert should_seed_demo(db_session) is True


def test_should_seed_when_all_neutral_junk(db_session):
    for i in range(5):
        db_session.add(
            Mention(
                brand="novahome",
                text=f"texto {i}",
                source="demo",
                sentiment_score=0.0,
                label="neutral",
                created_at=datetime.now(timezone.utc),
            )
        )
    db_session.commit()
    assert should_seed_demo(db_session) is True


def test_run_demo_seed_populates_timeline(db_session):
    count = run_demo_seed(db_session, reset=True)
    assert count == len(DEMO_MENTIONS)
    rows = db_session.query(Mention).filter(Mention.brand == "novahome").all()
    assert len(rows) == 9
    labels = {r.label for r in rows}
    assert "positive" in labels
    assert "negative" in labels


def test_ensure_demo_data_skips_when_disabled(db_session):
    ensure_demo_data(db_session, auto_seed=False)
    assert db_session.query(Mention).count() == 0


def test_ensure_demo_data_seeds_when_empty(db_session):
    ensure_demo_data(db_session, auto_seed=True)
    assert db_session.query(Mention).count() == len(DEMO_MENTIONS)

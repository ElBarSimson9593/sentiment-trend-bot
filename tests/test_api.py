def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_list_mention(client):
    payload = {
        "brand": "novahome",
        "text": "Muy mala experiencia, no recomiendo",
        "source": "demo",
    }
    created = client.post("/api/mentions", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["label"] == "negative"
    assert body["brand"] == "novahome"

    listed = client.get("/api/mentions", params={"brand": "novahome"})
    assert listed.status_code == 200
    assert len(listed.json()) >= 1


def test_dashboard_metrics(client):
    client.post(
        "/api/mentions",
        json={"brand": "acme", "text": "Gran servicio", "source": "demo"},
    )
    response = client.get("/api/dashboard/acme/metrics?hours=24")
    assert response.status_code == 200
    data = response.json()
    assert data["total_mentions"] >= 1
    assert "avg_sentiment" in data


def test_simulate_crisis_creates_alert(client):
    response = client.post("/api/demo/simulate-crisis?brand=novahome")
    assert response.status_code == 200
    body = response.json()
    assert body["mentions_created"] == 3
    assert body["alert_triggered"] is True

    alerts = client.get("/api/dashboard/novahome/alerts?limit=5")
    assert alerts.status_code == 200
    assert len(alerts.json()) >= 1


def test_simulate_crisis_can_repeat_alert(client):
    first = client.post("/api/demo/simulate-crisis?brand=demobrand")
    second = client.post("/api/demo/simulate-crisis?brand=demobrand")
    assert first.json()["alert_triggered"] is True
    assert second.json()["alert_triggered"] is True

    alerts = client.get("/api/dashboard/demobrand/alerts?limit=5")
    assert len(alerts.json()) >= 2

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

# SentimentTrend Bot

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

API de monitoreo de reputación con **análisis de sentimiento**, **alertas automáticas por webhook** y **mini-dashboard** con métricas en tiempo real.

**Repositorio:** [github.com/ElBarSimson9593/sentiment-trend-bot](https://github.com/ElBarSimson9593/sentiment-trend-bot)

> Proyecto de portafolio — FastAPI · PostgreSQL · VADER Sentiment · Chart.js  
> Marca de demo ficticia: `novahome` (sector inmobiliario simulado)

---

## Qué hace

1. Ingesta menciones públicas simuladas (comentarios, reseñas).
2. Clasifica sentimiento: `positive` / `neutral` / `negative`.
3. Si hay un pico de negatividad, registra alerta y dispara webhook (Discord/Slack).
4. Muestra KPIs, distribución, evolución temporal y historial de alertas en un dashboard.

---

## Capturas

### Dashboard — KPIs y gráficos

![Dashboard overview](docs/screenshots/dashboard-overview.png)

### Evolución temporal y alertas

![Dashboard timeline y alertas](docs/screenshots/dashboard-timeline-alertas.png)

### API documentada (Swagger)

![Swagger UI](docs/screenshots/api-docs.png)

---

## Demo rápida

```bash
docker compose up --build
```

En otra terminal:

```bash
pip install -r requirements.txt
python scripts/seed_demo.py --reset
```

| Recurso | URL |
|---------|-----|
| Dashboard | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

> Postgres expone el puerto **5433** en host (5432 suele estar ocupado localmente).

---

## Stack

| Capa | Tecnología |
|------|------------|
| API | FastAPI, Pydantic, SQLAlchemy |
| Base de datos | PostgreSQL 16 |
| Sentimiento | VADER + refuerzo léxico en español |
| Frontend dashboard | Jinja2, Chart.js |
| Infra | Docker Compose |
| Tests | pytest |

---

## Variables de entorno

Copia `.env.example` a `.env`:

| Variable | Descripción |
|----------|-------------|
| `DATABASE_URL` | Conexión PostgreSQL |
| `WEBHOOK_URL` | URL Discord/Slack (opcional) |
| `ALERT_NEGATIVE_THRESHOLD` | Negativos para alertar (default: 3) |
| `ALERT_WINDOW_MINUTES` | Ventana en minutos (default: 60) |

---

## API principal

```http
POST /api/mentions
{"brand": "novahome", "text": "Pésima atención", "source": "twitter"}

GET  /api/mentions?brand=novahome
GET  /api/dashboard/novahome/metrics?hours=24
GET  /api/dashboard/novahome/timeline?hours=24
GET  /api/dashboard/novahome/alerts
```

---

## Tests

```bash
pip install -r requirements.txt
pytest
```

---

## Arquitectura

```mermaid
flowchart LR
  A[Menciones] --> B[FastAPI]
  B --> C[VADER Sentiment]
  B --> D[(PostgreSQL)]
  B --> E[Webhook Alert]
  D --> F[Dashboard Chart.js]
```

Documento de requisitos: [docs/PRD.md](docs/PRD.md)

---

## Autor

**Osvaldo Andrés Díaz Guzmán**  
Estudiante Ing. en Informática · INACAP Antofagasta · Chile  
Enfoque: desarrollo backend e IA aplicada

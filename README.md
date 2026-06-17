# SentimentTrend Bot

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)](https://www.postgresql.org/)
[![Tests](https://github.com/ElBarSimson9593/sentiment-trend-bot/actions/workflows/test.yml/badge.svg)](https://github.com/ElBarSimson9593/sentiment-trend-bot/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

API de monitoreo de reputación con **análisis de sentimiento**, **alertas automáticas por webhook** y **mini-dashboard** con métricas en tiempo real.

**Demo en vivo:** [sentiment-trend-bot.onrender.com](https://sentiment-trend-bot.onrender.com)  
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

### Vista general

![Dashboard SentimentTrend Bot](docs/screenshots/dashboard.png)

### KPIs en tiempo real

![Menciones, sentimiento promedio, tendencia y alertas](docs/screenshots/kpis.png)

### Distribución de sentimiento

![Gráfico de dona — positivo, neutro y negativo](docs/screenshots/distribucion.png)

### Evolución temporal

![Línea de sentimiento y volumen de menciones por franja horaria](docs/screenshots/timeline.png)

### Alertas de crisis reputacional

![Historial de alertas automáticas](docs/screenshots/alertas-lista.png)

### Simular mención y mini-crisis

![Formulario de prueba y botón de simulación de crisis](docs/screenshots/simular-mencion.png)

### API documentada (Swagger)

![Swagger UI](docs/screenshots/api.png)

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

## Deploy en Render + Neon (free tier)

**Base de datos (Neon, gratis y persistente):**

1. [neon.tech](https://neon.tech) → proyecto nuevo → copia la connection string.
2. Convierte a SQLAlchemy: `postgresql+psycopg://usuario:pass@host/db?sslmode=require`

**API (Render):**

1. [render.com](https://render.com) → **New** → **Blueprint** → repo `sentiment-trend-bot`.
2. Pega `DATABASE_URL` cuando lo pida (`WEBHOOK_URL` opcional).
3. Prueba `https://TU-SERVICIO.onrender.com/health` y el dashboard en `/`.

> No uses Postgres de Render free (caduca ~30 días). Neon + Render web service = $0 sin tarjeta obligatoria en Neon.

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

CI configurado en [`.github/workflows/test.yml`](.github/workflows/test.yml) (GitHub Actions).

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

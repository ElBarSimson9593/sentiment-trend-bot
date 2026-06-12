# SentimentTrend Bot — PRD (MVP v0.1)

## Problema

Las marcas reciben comentarios dispersos en redes y portales. Detectar manualmente un pico de sentimiento negativo es lento y reactivo.

## Solución

API que ingesta menciones, calcula sentimiento, persiste historial y dispara alertas por webhook cuando se supera un umbral de negatividad. Incluye mini-dashboard con métricas y gráficos.

## Usuario objetivo

Analista de marketing / operaciones que monitorea reputación de una marca (ej. inmobiliaria).

## Alcance MVP

### Incluido

- `POST /api/mentions` — ingesta y análisis
- `GET /api/mentions?brand=` — historial
- `GET /api/dashboard/{brand}/metrics` — KPIs
- `GET /api/dashboard/{brand}/timeline` — serie temporal
- `GET /api/dashboard/{brand}/alerts` — alertas registradas
- `GET /` — dashboard con Chart.js
- Webhook configurable (`WEBHOOK_URL`)
- PostgreSQL + Docker Compose

### Fuera de alcance (v1)

- Streaming real de redes sociales
- Autenticación multi-tenant
- Entrenamiento de modelos propios

## Stack

- FastAPI, SQLAlchemy, PostgreSQL
- VADER Sentiment
- Chart.js (dashboard)
- Docker

## Criterios de aceptación

1. Crear mención retorna score, label y flag de alerta.
2. Dashboard muestra distribución, tendencia y timeline.
3. Tras N negativos en ventana temporal, se registra alerta y se llama webhook si está configurado.
4. Tests básicos pasan con `pytest`.

## Demo portfolio

1. `docker compose up --build`
2. `python scripts/seed_demo.py`
3. Abrir `http://localhost:8000`
4. Capturar pantalla de gráficos + alerta para README/CV

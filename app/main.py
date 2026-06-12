import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import Base, engine
from app.routers import dashboard, mentions


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not os.getenv("TESTING"):
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SentimentTrend Bot",
    description="API de monitoreo de reputación con análisis de sentimiento y alertas automáticas.",
    version="0.1.0",
    lifespan=lifespan,
)

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(mentions.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "SentimentTrend Dashboard"},
    )

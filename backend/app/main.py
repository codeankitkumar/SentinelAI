"""SentinelAI FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .api import (
    alerts,
    assistant,
    auth,
    dashboard,
    events,
    incidents,
    ml,
    monitor,
    threatintel,
)
from .config import settings
from .seed import init_db, run_seed_if_needed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("sentinel")

# Public API surface served under /api.
api_router = APIRouter(prefix="/api")
for router in (
    auth.router,
    events.router,
    alerts.router,
    incidents.router,
    dashboard.router,
    assistant.router,
    threatintel.router,
    ml.router,
    monitor.router,
):
    api_router.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (%s)", settings.app_name, settings.environment)
    init_db()
    run_seed_if_needed()
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title="SentinelAI API",
    description="AI-powered cyber threat detection & SOC platform API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
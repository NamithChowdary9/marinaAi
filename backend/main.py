"""
MarineAI — Main FastAPI Application Entry Point
Agentic Maritime Intelligence Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

from config.settings import settings
from api.routes import ships, weather, agents, chat, alerts, routes_api, analytics
from database.connection import init_db, close_db
from services.ais.ais_stream import AISStreamService
from services.weather.weather_service import WeatherService


# ─── Lifespan (startup / shutdown) ──────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all services on startup, clean up on shutdown."""
    logger.info("🌊 MarineAI starting up...")

    # Initialize database (optional — skipped if PostgreSQL is not running)
    app.state.database_connected = False
    try:
        await init_db()
        app.state.database_connected = True
        logger.info("✅ Database connected")
    except Exception as e:
        logger.warning(f"⚠  Database unavailable (running without DB): {e}")

    # Start background AIS streaming (mock mode if no API key)
    ais_service = None
    try:
        ais_service = AISStreamService()
        app.state.ais_service = ais_service
        await ais_service.start()
        logger.info("✅ AIS stream started")
    except Exception as e:
        logger.warning(f"⚠  AIS stream unavailable: {e}")

    # Pre-warm weather cache
    weather_service = WeatherService()
    app.state.weather_service = weather_service
    logger.info("✅ Weather service initialized")

    logger.info("🚀 MarineAI is live!")
    yield

    # Shutdown
    logger.info("🌊 MarineAI shutting down...")
    if ais_service:
        await ais_service.stop()
    if app.state.database_connected:
        await close_db()
    logger.info("✅ Shutdown complete")


# ─── App Instance ────────────────────────────────────────────────────────────

app = FastAPI(
    title="MarineAI — Agentic Maritime Intelligence Platform",
    description=(
        "Real-time ship tracking, ocean wave prediction, weather analysis, "
        "and AI-powered maritime decision support."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


# ─── Middleware ──────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Authorization", "Content-Type", "Origin", "X-Requested-With"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ─── Routers ─────────────────────────────────────────────────────────────────

app.include_router(ships.router,       prefix="/api/ships",     tags=["Ships"])
app.include_router(weather.router,     prefix="/api/weather",   tags=["Weather"])
app.include_router(agents.router,      prefix="/api/agents",    tags=["AI Agents"])
app.include_router(chat.router,        prefix="/api/chat",      tags=["Maritime Chat"])
app.include_router(alerts.router,      prefix="/api/alerts",    tags=["Alerts"])
app.include_router(routes_api.router,  prefix="/api/routes",    tags=["Route Optimization"])
app.include_router(analytics.router,   prefix="/api/analytics", tags=["Analytics"])


# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "app": "MarineAI",
        "status": "operational",
        "version": "1.0.0",
        "message": "Agentic Maritime Intelligence Platform is running 🌊"
    }


@app.get("/health", tags=["Health"])
async def health():
    database_connected = getattr(app.state, "database_connected", False)
    return {
        "status": "healthy" if database_connected else "degraded",
        "database": "connected" if database_connected else "unavailable",
        "agents": "active",
    }


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_level="info",
    )

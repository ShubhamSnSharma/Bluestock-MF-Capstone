"""
Sprint 6 — Day 38: FastAPI application scaffold for N100 Financial Intelligence Platform.

Sets up:
  - FastAPI app with metadata
  - CORS middleware (allow all origins for dev)
  - Request logging middleware
  - SQLite read-only database dependency
  - All eight router modules under /api/v1
"""

from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware


# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Database path ────────────────────────────────────────────────────────────

DB_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "Sprint-01-Data-Foundation"
    / "nifty100.db"
)


# ── Database dependency ──────────────────────────────────────────────────────


def get_db():
    """Yield a read-only SQLite connection; close after request."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_db_row_counts() -> Dict[str, int]:
    """Return row counts for all user tables in the database."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    counts = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
        counts[table] = cursor.fetchone()[0]
    conn.close()
    return counts


# ── Application ──────────────────────────────────────────────────────────────

APP_VERSION = "0.1.0"
APP_TITLE = "N100 Financial Intelligence Platform"

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="REST API for Nifty 100 financial analysis, screening, and clustering.",
)


# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ───────────────────────────────────────────────


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log HTTP method, path, status code, and response time for every request."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s %s %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


# ── Routers ──────────────────────────────────────────────────────────────────

from src.api.routers.companies import router as companies_router
from src.api.routers.documents import router as documents_router
from src.api.routers.health import router as health_router
from src.api.routers.peers import router as peers_router
from src.api.routers.portfolio import router as portfolio_router
from src.api.routers.screener import router as screener_router
from src.api.routers.sectors import router as sectors_router
from src.api.routers.valuation import router as valuation_router

app.include_router(health_router)
app.include_router(companies_router)
app.include_router(screener_router)
app.include_router(sectors_router)
app.include_router(peers_router)
app.include_router(valuation_router)
app.include_router(portfolio_router)
app.include_router(documents_router)

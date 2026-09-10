"""Health check router — Day 38 scaffold."""

from __future__ import annotations

import time

from fastapi import APIRouter

from src.api.main import APP_VERSION, get_db_row_counts

router = APIRouter(prefix="/api/v1", tags=["health"])

_start_time = time.time()


@router.get("/health")
def health_check():
    """Return service status, uptime, version, and database row counts."""
    return {
        "status": "ok",
        "version": APP_VERSION,
        "uptime_seconds": round(time.time() - _start_time, 1),
        "db_row_counts": get_db_row_counts(),
    }

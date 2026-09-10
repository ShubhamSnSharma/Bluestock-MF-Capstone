"""
Sprint 6 — Day 40: Sectors endpoints.

Endpoints:
  GET /api/v1/sectors                      — List all sectors with company counts
  GET /api/v1/sectors/{sector}/companies   — List companies in a sector
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.api.main import get_db

router = APIRouter(prefix="/api/v1/sectors", tags=["sectors"])


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return {k: row[k] for k in row.keys()}


class SectorSummary(BaseModel):
    """Sector summary with company count."""

    broad_sector: str
    company_count: int


class SectorCompany(BaseModel):
    """Company within a sector."""

    company_id: str
    company_name: str
    sub_sector: Optional[str] = None
    market_cap_category: Optional[str] = None


@router.get("/", response_model=List[SectorSummary])
def list_sectors(db: sqlite3.Connection = Depends(get_db)):
    """List all broad sectors with company counts."""
    rows = db.execute(
        """
        SELECT broad_sector, COUNT(*) AS company_count
        FROM sectors
        GROUP BY broad_sector
        ORDER BY broad_sector
        """
    ).fetchall()
    return [SectorSummary(**_row_to_dict(r)) for r in rows]


@router.get("/{sector}/companies", response_model=List[SectorCompany])
def get_sector_companies(
    sector: str,
    market_cap_category: Optional[str] = Query(
        None, description="Filter by market cap category"
    ),
    db: sqlite3.Connection = Depends(get_db),
):
    """List all companies in a specific broad sector."""
    # Verify sector exists
    check = db.execute(
        "SELECT 1 FROM sectors WHERE broad_sector = ? LIMIT 1", (sector,)
    ).fetchone()
    if check is None:
        raise HTTPException(status_code=404, detail=f"Sector not found: {sector!r}")

    sql = """
        SELECT s.company_id, c.company_name, s.sub_sector, s.market_cap_category
        FROM sectors s
        JOIN companies c ON s.company_id = c.id
        WHERE s.broad_sector = ?
    """
    params: list = [sector]

    if market_cap_category:
        sql += " AND s.market_cap_category = ?"
        params.append(market_cap_category)

    sql += " ORDER BY s.company_id"
    rows = db.execute(sql, params).fetchall()
    return [SectorCompany(**_row_to_dict(r)) for r in rows]

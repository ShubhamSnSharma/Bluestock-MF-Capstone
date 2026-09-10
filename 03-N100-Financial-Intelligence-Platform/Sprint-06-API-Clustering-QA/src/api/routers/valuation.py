"""
Sprint 6 — Day 40: Market-cap and valuation endpoints.

Endpoints:
  GET /api/v1/market-cap   — Market cap data with optional filters
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from src.api.main import get_db

router = APIRouter(prefix="/api/v1/market-cap", tags=["market-cap"])


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return {k: row[k] for k in row.keys()}


class MarketCapItem(BaseModel):
    """Market cap record for a company."""

    company_id: str
    company_name: Optional[str] = None
    broad_sector: Optional[str] = None
    market_cap_category: Optional[str] = None
    year: str
    market_cap_crore: Optional[float] = None
    enterprise_value_crore: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    dividend_yield_pct: Optional[float] = None


@router.get("/", response_model=List[MarketCapItem])
def list_market_cap(
    year: Optional[str] = Query(None, description="Filter by year (YYYY)"),
    sector: Optional[str] = Query(None, description="Filter by broad sector"),
    market_cap_category: Optional[str] = Query(
        None, description="Filter by market cap category"
    ),
    db: sqlite3.Connection = Depends(get_db),
):
    """Return market cap data with optional year, sector, and category filters."""
    sql = """
        SELECT mc.company_id, c.company_name, s.broad_sector, s.market_cap_category,
               mc.year, mc.market_cap_crore, mc.enterprise_value_crore,
               mc.pe_ratio, mc.pb_ratio, mc.ev_ebitda, mc.dividend_yield_pct
        FROM market_cap mc
        JOIN companies c ON mc.company_id = c.id
        JOIN sectors s ON mc.company_id = s.company_id
        WHERE 1=1
    """
    params: list = []

    if year:
        sql += " AND mc.year = ?"
        params.append(year)
    if sector:
        sql += " AND s.broad_sector = ?"
        params.append(sector)
    if market_cap_category:
        sql += " AND s.market_cap_category = ?"
        params.append(market_cap_category)

    sql += " ORDER BY mc.market_cap_crore DESC, mc.company_id"
    rows = db.execute(sql, params).fetchall()
    return [MarketCapItem(**_row_to_dict(r)) for r in rows]

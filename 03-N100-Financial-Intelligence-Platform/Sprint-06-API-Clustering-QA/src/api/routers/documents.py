"""
Sprint 6 — Day 40: Documents endpoints.

Endpoints:
  GET /api/v1/documents/{ticker}   — Company annual report documents
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.api.main import get_db

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def _resolve_ticker(ticker: str, conn: sqlite3.Connection) -> str:
    """Resolve a ticker to its canonical uppercase form; raise 404 if not found."""
    canonical = ticker.upper()
    row = conn.execute("SELECT id FROM companies WHERE id = ?", (canonical,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Company not found: {ticker!r}")
    return canonical


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return {k: row[k] for k in row.keys()}


class DocumentItem(BaseModel):
    """Annual report document entry."""

    company_id: str
    year: str
    annual_report: Optional[str] = None


@router.get("/{ticker}", response_model=List[DocumentItem])
def get_documents(
    ticker: str,
    year: Optional[str] = Query(None, description="Filter by specific year (YYYY)"),
    db: sqlite3.Connection = Depends(get_db),
):
    """Return annual report documents for a company."""
    cid = _resolve_ticker(ticker, db)

    sql = "SELECT company_id, year, annual_report FROM documents WHERE company_id = ?"
    params: list = [cid]

    if year:
        if not year.isdigit() or len(year) != 4:
            raise HTTPException(
                status_code=400, detail=f"Invalid year format: {year!r}. Use YYYY."
            )
        sql += " AND year = ?"
        params.append(year)

    sql += " ORDER BY year DESC"
    rows = db.execute(sql, params).fetchall()
    return [DocumentItem(**_row_to_dict(r)) for r in rows]

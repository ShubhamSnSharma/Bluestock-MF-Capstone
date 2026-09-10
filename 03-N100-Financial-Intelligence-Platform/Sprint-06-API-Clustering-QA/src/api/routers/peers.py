"""
Sprint 6 — Day 40: Peers endpoints.

Endpoints:
  GET /api/v1/peers/{ticker}           — Get peer group membership for a company
  GET /api/v1/peers/{ticker}/compare   — Compare company against its peers
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.api.main import get_db

router = APIRouter(prefix="/api/v1/peers", tags=["peers"])


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


class PeerMember(BaseModel):
    """A member of a peer group."""

    company_id: str
    company_name: Optional[str] = None
    is_benchmark: bool = False


class PeerMetric(BaseModel):
    """A single metric comparison row."""

    company_id: str
    company_name: Optional[str] = None
    metric: str
    value: Optional[float] = None
    percentile_rank: Optional[float] = None


@router.get("/{ticker}")
def get_peer_group(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    """Return peer group membership for a company."""
    cid = _resolve_ticker(ticker, db)

    # Find which peer groups this company belongs to
    groups = db.execute(
        """
        SELECT DISTINCT peer_group_name
        FROM peer_groups
        WHERE company_id = ?
        ORDER BY peer_group_name
        """,
        (cid,),
    ).fetchall()

    if not groups:
        raise HTTPException(
            status_code=404,
            detail=f"No peer group found for {cid}.",
        )

    result = {}
    for g in groups:
        gname = g["peer_group_name"]
        members = db.execute(
            """
            SELECT pg.company_id, c.company_name, pg.is_benchmark
            FROM peer_groups pg
            JOIN companies c ON pg.company_id = c.id
            WHERE pg.peer_group_name = ?
            ORDER BY pg.company_id
            """,
            (gname,),
        ).fetchall()
        result[gname] = [
            PeerMember(
                company_id=m["company_id"],
                company_name=m["company_name"],
                is_benchmark=bool(m["is_benchmark"]),
            ).model_dump()
            for m in members
        ]

    return {"company_id": cid, "peer_groups": result}


@router.get("/{ticker}/compare")
def compare_peers(
    ticker: str,
    year: Optional[str] = Query(None, description="Year for comparison (YYYY)"),
    db: sqlite3.Connection = Depends(get_db),
):
    """Compare a company against its peers on percentile-ranked metrics."""
    cid = _resolve_ticker(ticker, db)

    # Find peer group
    group_row = db.execute(
        "SELECT peer_group_name FROM peer_groups WHERE company_id = ? LIMIT 1",
        (cid,),
    ).fetchone()
    if group_row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No peer group found for {cid}.",
        )
    gname = group_row["peer_group_name"]

    # Determine year
    if year:
        if not year.isdigit() or len(year) != 4:
            raise HTTPException(
                status_code=400, detail=f"Invalid year format: {year!r}. Use YYYY."
            )
        target_year = year
    else:
        # Use most recent year available
        latest = db.execute(
            "SELECT MAX(year) AS y FROM peer_percentiles WHERE peer_group_name = ?",
            (gname,),
        ).fetchone()
        target_year = latest["y"] if latest and latest["y"] else "2024"

    # Get all peers' percentile data
    rows = db.execute(
        """
        SELECT pp.company_id, c.company_name, pp.metric, pp.value, pp.percentile_rank
        FROM peer_percentiles pp
        JOIN companies c ON pp.company_id = c.id
        WHERE pp.peer_group_name = ? AND pp.year = ?
        ORDER BY pp.company_id, pp.metric
        """,
        (gname, target_year),
    ).fetchall()

    if not rows:
        return {
            "company_id": cid,
            "peer_group_name": gname,
            "year": target_year,
            "comparisons": [],
        }

    comparisons = []
    for r in rows:
        comparisons.append(
            PeerMetric(
                company_id=r["company_id"],
                company_name=r["company_name"],
                metric=r["metric"],
                value=r["value"],
                percentile_rank=r["percentile_rank"],
            ).model_dump()
        )

    return {
        "company_id": cid,
        "peer_group_name": gname,
        "year": target_year,
        "comparisons": comparisons,
    }

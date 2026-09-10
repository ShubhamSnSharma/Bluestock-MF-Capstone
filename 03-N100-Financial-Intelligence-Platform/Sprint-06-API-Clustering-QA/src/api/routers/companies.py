"""
Sprint 6 — Day 39: Company data endpoints.

Endpoints:
  GET /api/v1/companies                 — List all companies with optional filters
  GET /api/v1/companies/{ticker}        — Full company profile
  GET /api/v1/companies/{ticker}/pl     — P&L history
  GET /api/v1/companies/{ticker}/bs     — Balance sheet history
  GET /api/v1/companies/{ticker}/cashflow — Cashflow history
  GET /api/v1/companies/{ticker}/ratios — Financial KPI ratios
  GET /api/v1/companies/{ticker}/tearsheet — Pre-generated tearsheet PDF
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.api.main import get_db

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])

TEARSHEET_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "Sprint-05-Intelligence-NLP-PDF-Reports"
    / "reports"
    / "tearsheets"
)

_YEAR_RE = re.compile(r"^\d{4}$")


# ── Helpers ──────────────────────────────────────────────────────────────────


def _validate_year(value: str, label: str) -> str:
    """Validate a year string is YYYY or TTM; raise 400 otherwise."""
    if value == "TTM":
        return value
    if not _YEAR_RE.match(value):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {label} format: {value!r}. Use YYYY or TTM.",
        )
    return value


def _validate_year_range(from_year: Optional[str], to_year: Optional[str]) -> None:
    """Validate from_year <= to_year when both are numeric."""
    if from_year and to_year and from_year != "TTM" and to_year != "TTM":
        if int(from_year) > int(to_year):
            raise HTTPException(
                status_code=400,
                detail=f"from_year ({from_year}) must not be greater than to_year ({to_year}).",
            )


def _resolve_ticker(ticker: str, conn: sqlite3.Connection) -> str:
    """Resolve a ticker to its canonical uppercase form; raise 404 if not found."""
    canonical = ticker.upper()
    row = conn.execute("SELECT id FROM companies WHERE id = ?", (canonical,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Company not found: {ticker!r}")
    return canonical


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict, converting NULL to None."""
    return {k: row[k] for k in row.keys()}


# ── Response models ──────────────────────────────────────────────────────────


class CompanyListItem(BaseModel):
    company_id: str
    company_name: str
    broad_sector: Optional[str] = None
    sub_sector: Optional[str] = None
    roe_pct: Optional[float] = None
    roce_pct: Optional[float] = None
    market_cap_category: Optional[str] = None


class CompanyDetail(BaseModel):
    company_id: str
    company_name: str
    broad_sector: Optional[str] = None
    sub_sector: Optional[str] = None
    market_cap_category: Optional[str] = None
    face_value: Optional[float] = None
    book_value: Optional[float] = None
    roe_pct: Optional[float] = None
    roce_pct: Optional[float] = None
    about_company: Optional[str] = None
    website: Optional[str] = None
    company_logo: Optional[str] = None
    chart_link: Optional[str] = None
    nse_profile: Optional[str] = None
    bse_profile: Optional[str] = None
    latest_ratios: Optional[dict] = None


# ── 1. GET /api/v1/companies ────────────────────────────────────────────────


@router.get("/", response_model=List[CompanyListItem])
def list_companies(
    sector: Optional[str] = Query(None, description="Filter by broad sector"),
    market_cap_category: Optional[str] = Query(
        None, description="Filter by market cap category"
    ),
    search: Optional[str] = Query(None, description="Search company name or ticker"),
    db: sqlite3.Connection = Depends(get_db),
):
    """List all 92 companies with optional sector, market-cap, and search filters."""
    sql = """
        SELECT c.id AS company_id,
               c.company_name,
               s.broad_sector,
               s.sub_sector,
               c.roe_percentage AS roe_pct,
               c.roce_percentage AS roce_pct,
               s.market_cap_category
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        WHERE 1=1
    """
    params: list = []

    if sector:
        sql += " AND s.broad_sector = ?"
        params.append(sector)
    if market_cap_category:
        sql += " AND s.market_cap_category = ?"
        params.append(market_cap_category)
    if search:
        sql += " AND (c.id LIKE ? OR c.company_name LIKE ?)"
        pattern = f"%{search}%"
        params.extend([pattern, pattern])

    sql += " ORDER BY c.id"
    rows = db.execute(sql, params).fetchall()
    return [CompanyListItem(**_row_to_dict(r)) for r in rows]


# ── 2. GET /api/v1/companies/{ticker} ───────────────────────────────────────


@router.get("/{ticker}", response_model=CompanyDetail)
def get_company(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    """Return full company profile including latest-year KPIs."""
    cid = _resolve_ticker(ticker, db)

    row = db.execute(
        """
        SELECT c.*, s.broad_sector, s.sub_sector, s.market_cap_category
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        WHERE c.id = ?
        """,
        (cid,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Company not found: {ticker!r}")

    d = _row_to_dict(row)

    # Latest ratios (year=2024 or most recent)
    ratio_row = db.execute(
        "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1",
        (cid,),
    ).fetchone()

    return CompanyDetail(
        company_id=cid,
        company_name=d["company_name"],
        broad_sector=d.get("broad_sector"),
        sub_sector=d.get("sub_sector"),
        market_cap_category=d.get("market_cap_category"),
        face_value=d.get("face_value"),
        book_value=d.get("book_value"),
        roe_pct=d.get("roe_percentage"),
        roce_pct=d.get("roce_percentage"),
        about_company=d.get("about_company"),
        website=d.get("website"),
        company_logo=d.get("company_logo"),
        chart_link=d.get("chart_link"),
        nse_profile=d.get("nse_profile"),
        bse_profile=d.get("bse_profile"),
        latest_ratios=_row_to_dict(ratio_row) if ratio_row else None,
    )


# ── 3. GET /api/v1/companies/{ticker}/pl ────────────────────────────────────


@router.get("/{ticker}/pl")
def get_pl(
    ticker: str,
    from_year: Optional[str] = Query(
        None, description="Lower bound year (YYYY or TTM)"
    ),
    to_year: Optional[str] = Query(None, description="Upper bound year (YYYY or TTM)"),
    db: sqlite3.Connection = Depends(get_db),
):
    """Return P&L history array with optional year range filtering."""
    cid = _resolve_ticker(ticker, db)

    if from_year:
        _validate_year(from_year, "from_year")
    if to_year:
        _validate_year(to_year, "to_year")
    _validate_year_range(from_year, to_year)

    sql = "SELECT * FROM profitandloss WHERE company_id = ?"
    params: list = [cid]

    if from_year:
        sql += " AND year >= ?"
        params.append(from_year)
    if to_year:
        sql += " AND year <= ?"
        params.append(to_year)

    sql += " ORDER BY year"
    rows = db.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


# ── 4. GET /api/v1/companies/{ticker}/bs ────────────────────────────────────


@router.get("/{ticker}/bs")
def get_bs(
    ticker: str,
    from_year: Optional[str] = Query(
        None, description="Lower bound year (YYYY or TTM)"
    ),
    to_year: Optional[str] = Query(None, description="Upper bound year (YYYY or TTM)"),
    db: sqlite3.Connection = Depends(get_db),
):
    """Return balance sheet history array with optional year range filtering."""
    cid = _resolve_ticker(ticker, db)

    if from_year:
        _validate_year(from_year, "from_year")
    if to_year:
        _validate_year(to_year, "to_year")
    _validate_year_range(from_year, to_year)

    sql = "SELECT * FROM balancesheet WHERE company_id = ?"
    params: list = [cid]

    if from_year:
        sql += " AND year >= ?"
        params.append(from_year)
    if to_year:
        sql += " AND year <= ?"
        params.append(to_year)

    sql += " ORDER BY year"
    rows = db.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


# ── 5. GET /api/v1/companies/{ticker}/cashflow ──────────────────────────────


@router.get("/{ticker}/cashflow")
def get_cashflow(
    ticker: str,
    from_year: Optional[str] = Query(
        None, description="Lower bound year (YYYY or TTM)"
    ),
    to_year: Optional[str] = Query(None, description="Upper bound year (YYYY or TTM)"),
    db: sqlite3.Connection = Depends(get_db),
):
    """Return cashflow history array with optional year range filtering."""
    cid = _resolve_ticker(ticker, db)

    if from_year:
        _validate_year(from_year, "from_year")
    if to_year:
        _validate_year(to_year, "to_year")
    _validate_year_range(from_year, to_year)

    sql = "SELECT * FROM cashflow WHERE company_id = ?"
    params: list = [cid]

    if from_year:
        sql += " AND year >= ?"
        params.append(from_year)
    if to_year:
        sql += " AND year <= ?"
        params.append(to_year)

    sql += " ORDER BY year"
    rows = db.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


# ── 6. GET /api/v1/companies/{ticker}/ratios ────────────────────────────────


@router.get("/{ticker}/ratios")
def get_ratios(
    ticker: str,
    year: Optional[str] = Query(
        None, description="Filter by specific year (YYYY or TTM)"
    ),
    db: sqlite3.Connection = Depends(get_db),
):
    """Return financial KPI ratios; filter by year if provided."""
    cid = _resolve_ticker(ticker, db)

    if year:
        _validate_year(year, "year")
        row = db.execute(
            "SELECT * FROM financial_ratios WHERE company_id = ? AND year = ?",
            (cid, year),
        ).fetchone()
        if row is None:
            return []
        return [_row_to_dict(row)]

    rows = db.execute(
        "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year",
        (cid,),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


# ── 7. GET /api/v1/companies/{ticker}/tearsheet ─────────────────────────────


@router.get("/{ticker}/tearsheet")
def get_tearsheet(ticker: str, db: sqlite3.Connection = Depends(get_db)):
    """Return the pre-generated tearsheet PDF; 404 if not available."""
    cid = _resolve_ticker(ticker, db)

    pdf_path = TEARSHEET_DIR / f"{cid}_tearsheet.pdf"
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Tearsheet not available for {cid}.",
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{cid}_tearsheet.pdf",
    )

"""
db.py — Shared cached data loader for N100 Financial Intelligence Dashboard.
All query functions use @st.cache_data(ttl=600) for 10-minute caching.
Sprint 4 — Dashboard & Valuation Module
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

_SPRINT4_ROOT  = Path(__file__).resolve().parents[3]   # Sprint-04-Dashboard-Valuation/
_PLATFORM_ROOT = Path(__file__).resolve().parents[4]   # 03-N100-Financial-Intelligence-Platform/
DB_PATH: Path = (
    _PLATFORM_ROOT
    / "Sprint-01-Data-Foundation"
    / "nifty100.db"
)


def _conn() -> sqlite3.Connection:
    """Return a read-only SQLite connection."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


# ---------------------------------------------------------------------------
# Cached query helpers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=600, show_spinner=False)
def get_companies() -> pd.DataFrame:
    """
    Return all 92 companies joined with sectors.
    Columns: company_id, company_name, broad_sector, sub_sector,
             index_weight_pct, market_cap_category,
             about_company, website, nse_profile, bse_profile,
             book_value, roce_percentage, roe_percentage
    """
    sql = """
        SELECT
            c.id            AS company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            s.index_weight_pct,
            s.market_cap_category,
            c.about_company,
            c.website,
            c.nse_profile,
            c.bse_profile,
            c.book_value,
            c.roce_percentage,
            c.roe_percentage
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        ORDER BY c.id
    """
    with _conn() as con:
        return pd.read_sql_query(sql, con)


@st.cache_data(ttl=600, show_spinner=False)
def get_ratios(ticker: Optional[str] = None, year: Optional[str] = None) -> pd.DataFrame:
    """
    Return financial_ratios rows, optionally filtered by ticker and/or year.
    All numeric ratio columns are included.
    """
    conditions: list[str] = []
    params: list[str] = []

    if ticker:
        conditions.append("company_id = ?")
        params.append(ticker.upper())
    if year:
        conditions.append("year = ?")
        params.append(str(year))

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    sql = f"SELECT * FROM financial_ratios {where} ORDER BY company_id, year"
    with _conn() as con:
        return pd.read_sql_query(sql, con, params=params if params else None)


@st.cache_data(ttl=600, show_spinner=False)
def get_pl(ticker: str) -> pd.DataFrame:
    """Return profit & loss rows for a given ticker, all available years."""
    sql = """
        SELECT * FROM profitandloss
        WHERE company_id = ?
        ORDER BY CASE year WHEN 'TTM' THEN '9999' ELSE year END
    """
    with _conn() as con:
        return pd.read_sql_query(sql, con, params=[ticker.upper()])


@st.cache_data(ttl=600, show_spinner=False)
def get_bs(ticker: str) -> pd.DataFrame:
    """Return balance sheet rows for a given ticker, all available years."""
    sql = """
        SELECT * FROM balancesheet
        WHERE company_id = ?
        ORDER BY CASE year WHEN 'TTM' THEN '9999' ELSE year END
    """
    with _conn() as con:
        return pd.read_sql_query(sql, con, params=[ticker.upper()])


@st.cache_data(ttl=600, show_spinner=False)
def get_cf(ticker: str) -> pd.DataFrame:
    """Return cash-flow rows for a given ticker, all available years."""
    sql = """
        SELECT * FROM cashflow
        WHERE company_id = ?
        ORDER BY CASE year WHEN 'TTM' THEN '9999' ELSE year END
    """
    with _conn() as con:
        return pd.read_sql_query(sql, con, params=[ticker.upper()])


@st.cache_data(ttl=600, show_spinner=False)
def get_sectors() -> pd.DataFrame:
    """
    Return sector-level summary with company counts and market_cap info.
    Columns: broad_sector, sub_sector, company_count
    """
    sql = """
        SELECT
            s.broad_sector,
            s.sub_sector,
            COUNT(s.company_id) AS company_count
        FROM sectors s
        GROUP BY s.broad_sector, s.sub_sector
        ORDER BY s.broad_sector, company_count DESC
    """
    with _conn() as con:
        return pd.read_sql_query(sql, con)


@st.cache_data(ttl=600, show_spinner=False)
def get_peers(group_name: str) -> pd.DataFrame:
    """
    Return all companies in the given peer group with their latest-year
    financial ratios and market-cap data joined.
    """
    sql = """
        SELECT
            pg.company_id,
            c.company_name,
            s.broad_sector,
            pg.is_benchmark,
            fr.return_on_equity_pct          AS roe,
            fr.return_on_capital_employed_pct AS roce,
            fr.net_profit_margin_pct          AS npm,
            fr.debt_to_equity                 AS de,
            fr.interest_coverage              AS icr,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            fr.composite_quality_score,
            mc.pe_ratio,
            mc.pb_ratio,
            mc.market_cap_crore
        FROM peer_groups pg
        JOIN companies c  ON pg.company_id  = c.id
        JOIN sectors    s ON pg.company_id  = s.company_id
        LEFT JOIN financial_ratios fr
               ON fr.company_id = pg.company_id AND fr.year = '2024'
        LEFT JOIN market_cap mc
               ON mc.company_id = pg.company_id AND mc.year = '2024'
        WHERE pg.peer_group_name = ?
        ORDER BY pg.is_benchmark DESC, fr.composite_quality_score DESC
    """
    with _conn() as con:
        return pd.read_sql_query(sql, con, params=[group_name])


@st.cache_data(ttl=600, show_spinner=False)
def get_valuation(ticker: str) -> pd.DataFrame:
    """
    Return market_cap table rows for a given ticker.
    Columns: company_id, year, market_cap_crore, enterprise_value_crore,
             pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct
    """
    sql = """
        SELECT * FROM market_cap
        WHERE company_id = ?
        ORDER BY year
    """
    with _conn() as con:
        return pd.read_sql_query(sql, con, params=[ticker.upper()])


@st.cache_data(ttl=600, show_spinner=False)
def get_all_peer_groups() -> list[str]:
    """Return sorted list of all distinct peer group names."""
    sql = "SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY peer_group_name"
    with _conn() as con:
        df = pd.read_sql_query(sql, con)
    return df["peer_group_name"].tolist()


@st.cache_data(ttl=600, show_spinner=False)
def get_all_tickers() -> list[str]:
    """Return sorted list of all company_id tickers."""
    sql = "SELECT id FROM companies ORDER BY id"
    with _conn() as con:
        df = pd.read_sql_query(sql, con)
    return df["id"].tolist()


@st.cache_data(ttl=600, show_spinner=False)
def get_proscons(ticker: str) -> pd.DataFrame:
    """Return pros and cons rows for a given ticker."""
    sql = "SELECT pros, cons FROM prosandcons WHERE company_id = ?"
    with _conn() as con:
        return pd.read_sql_query(sql, con, params=[ticker.upper()])


@st.cache_data(ttl=600, show_spinner=False)
def get_documents(ticker: str) -> pd.DataFrame:
    """Return annual report document links for a given ticker, all years."""
    sql = """
        SELECT year, annual_report FROM documents
        WHERE company_id = ?
        ORDER BY year DESC
    """
    with _conn() as con:
        return pd.read_sql_query(sql, con, params=[ticker.upper()])


@st.cache_data(ttl=600, show_spinner=False)
def get_market_cap_all(year: str = "2024") -> pd.DataFrame:
    """Return market_cap for all companies for a given year."""
    sql = """
        SELECT mc.*, c.company_name, s.broad_sector, s.sub_sector
        FROM market_cap mc
        JOIN companies c ON mc.company_id = c.id
        JOIN sectors s   ON mc.company_id = s.company_id
        WHERE mc.year = ?
    """
    with _conn() as con:
        return pd.read_sql_query(sql, con, params=[str(year)])


@st.cache_data(ttl=600, show_spinner=False)
def get_ratios_all(year: str = "2024") -> pd.DataFrame:
    """Return financial_ratios for all companies for a given year, joined with company info."""
    sql = """
        SELECT
            fr.*,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            s.market_cap_category,
            pnl.sales
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.id
        JOIN sectors s   ON fr.company_id = s.company_id
        LEFT JOIN profitandloss pnl ON fr.company_id = pnl.company_id AND fr.year = pnl.year
        WHERE fr.year = ?
        ORDER BY fr.composite_quality_score DESC
    """
    with _conn() as con:
        return pd.read_sql_query(sql, con, params=[str(year)])


@st.cache_data(ttl=600, show_spinner=False)
def get_capital_patterns(year: str = "2024") -> pd.DataFrame:
    """
    Return companies with their Sprint-2 capital allocation pattern labels.
    Pattern labels come from:
      Sprint-02-Financial-Ratio-Engine/output/capital_allocation.csv
    (columns: company_id, year, cfo_sign, cfi_sign, cff_sign, pattern_label)

    Joined with financial_ratios and market_cap for quality score / market cap.
    Returns 92 rows for the requested year with columns:
      company_id, company_name, broad_sector, pattern_label,
      composite_quality_score, free_cash_flow_cr, market_cap_crore
    """
    # ── Load Sprint-2 capital allocation CSV ──────────────────────────────
    cap_csv = (
        _PLATFORM_ROOT
        / "Sprint-02-Financial-Ratio-Engine"
        / "output"
        / "capital_allocation.csv"
    )
    if not cap_csv.exists():
        raise FileNotFoundError(
            f"Sprint-2 capital_allocation.csv not found: {cap_csv}"
        )
    cap_df = pd.read_csv(cap_csv, dtype=str)
    cap_df = cap_df[cap_df["year"] == str(year)][["company_id", "pattern_label"]].copy()

    # ── Load quality score + market_cap from DB ───────────────────────────
    sql = """
        SELECT
            fr.company_id,
            c.company_name,
            s.broad_sector,
            fr.composite_quality_score,
            fr.free_cash_flow_cr,
            mc.market_cap_crore
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.id
        JOIN sectors s   ON fr.company_id = s.company_id
        LEFT JOIN market_cap mc
               ON mc.company_id = fr.company_id AND mc.year = ?
        WHERE fr.year = ?
        ORDER BY fr.composite_quality_score DESC
    """
    with _conn() as con:
        db_df = pd.read_sql_query(sql, con, params=[str(year), str(year)])

    # ── Merge CSV patterns onto DB data ───────────────────────────────────
    merged = db_df.merge(cap_df, on="company_id", how="left")
    merged["pattern_label"] = merged["pattern_label"].fillna("Other")
    return merged


@st.cache_data(ttl=600, show_spinner=False)
def get_trend_data(ticker: str, metrics: list[str]) -> pd.DataFrame:
    """
    Return time-series ratio data for a ticker across all years (excl. TTM).
    Only returns the requested metric columns + year.
    """
    base_cols = ["year"] + [m for m in metrics if m]
    placeholders = ", ".join(base_cols)
    sql = f"""
        SELECT {placeholders}
        FROM financial_ratios
        WHERE company_id = ? AND year != 'TTM'
        ORDER BY year
    """
    with _conn() as con:
        return pd.read_sql_query(sql, con, params=[ticker.upper()])


@st.cache_data(ttl=600, show_spinner=False)
def get_sector_bubble_data(year: str = "2024") -> pd.DataFrame:
    """
    Return data for sector bubble chart: Revenue, ROE, Market Cap, sub_sector.
    """
    sql = """
        SELECT
            fr.company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            pl.sales          AS revenue_cr,
            fr.return_on_equity_pct AS roe,
            mc.market_cap_crore
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.id
        JOIN sectors s   ON fr.company_id = s.company_id
        JOIN profitandloss pl ON pl.company_id = fr.company_id AND pl.year = ?
        LEFT JOIN market_cap mc ON mc.company_id = fr.company_id AND mc.year = ?
        WHERE fr.year = ?
    """
    with _conn() as con:
        return pd.read_sql_query(sql, con, params=[str(year), str(year), str(year)])


@st.cache_data(ttl=600, show_spinner=False)
def get_de_decline_flags() -> pd.DataFrame:
    """
    Return a DataFrame indicating whether each company's D/E declined
    from FY2023 to FY2024 (used by the Turnaround Watch screener preset).
    Columns: company_id, de_2023, de_2024, de_declining (bool)
    """
    sql = """
        SELECT company_id, year, debt_to_equity
        FROM financial_ratios
        WHERE year IN ('2023', '2024')
        ORDER BY company_id, year
    """
    with _conn() as con:
        df = pd.read_sql_query(sql, con)

    # Build decline flag without pivot (avoid MultiIndex column name issues
    # across pandas versions)
    df2023 = (
        df[df["year"] == "2023"][["company_id", "debt_to_equity"]]
        .rename(columns={"debt_to_equity": "de_2023"})
    )
    df2024 = (
        df[df["year"] == "2024"][["company_id", "debt_to_equity"]]
        .rename(columns={"debt_to_equity": "de_2024"})
    )
    merged_de = df2023.merge(df2024, on="company_id", how="outer")
    merged_de["de_declining"] = merged_de["de_2024"] < merged_de["de_2023"]
    # Fill missing (company only has one year) as False
    merged_de["de_declining"] = merged_de["de_declining"].fillna(False)
    return merged_de

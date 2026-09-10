"""
Sprint 6 — Day 42: API Client Helper for Streamlit Integration.

Provides cached, typed helpers that call the FastAPI endpoints via httpx.
Designed for use inside Streamlit pages (Sprint 4 dashboard).

Usage:
    from src.api.client import (
        api_get_companies, api_get_company, api_get_pl,
        api_get_bs, api_get_cashflow, api_get_ratios,
        api_get_tearsheet, api_get_screener_presets,
        api_get_screener_results, api_get_sectors,
        api_get_sector_companies, api_get_peers,
        api_get_peer_compare, api_get_market_cap,
        api_get_portfolio_stats, api_get_portfolio_clusters,
        api_get_documents,
    )
"""

from __future__ import annotations

from typing import Any

import httpx

API_BASE = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT = 30


def _get(path: str, params: dict | None = None) -> Any:
    """Low-level GET with timeout and error handling."""
    url = f"{API_BASE}{path}"
    with httpx.Client(timeout=DEFAULT_TIMEOUT) as c:
        resp = c.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


def _get_raw(path: str, params: dict | None = None) -> bytes:
    """GET that returns raw bytes (for PDFs)."""
    url = f"{API_BASE}{path}"
    with httpx.Client(timeout=DEFAULT_TIMEOUT) as c:
        resp = c.get(url, params=params)
        resp.raise_for_status()
        return resp.content


# ── Companies ───────────────────────────────────────────────────────────────


def api_get_companies(
    sector: str | None = None,
    market_cap_category: str | None = None,
    search: str | None = None,
) -> list[dict]:
    params: dict[str, str] = {}
    if sector:
        params["sector"] = sector
    if market_cap_category:
        params["market_cap_category"] = market_cap_category
    if search:
        params["search"] = search
    return _get("/api/v1/companies/", params=params)


def api_get_company(ticker: str) -> dict:
    return _get(f"/api/v1/companies/{ticker}")


# ── Financial Statements ────────────────────────────────────────────────────


def api_get_pl(
    ticker: str, from_year: str | None = None, to_year: str | None = None
) -> list[dict]:
    params: dict[str, str] = {}
    if from_year:
        params["from_year"] = from_year
    if to_year:
        params["to_year"] = to_year
    return _get(f"/api/v1/companies/{ticker}/pl", params=params)


def api_get_bs(
    ticker: str, from_year: str | None = None, to_year: str | None = None
) -> list[dict]:
    params: dict[str, str] = {}
    if from_year:
        params["from_year"] = from_year
    if to_year:
        params["to_year"] = to_year
    return _get(f"/api/v1/companies/{ticker}/bs", params=params)


def api_get_cashflow(
    ticker: str, from_year: str | None = None, to_year: str | None = None
) -> list[dict]:
    params: dict[str, str] = {}
    if from_year:
        params["from_year"] = from_year
    if to_year:
        params["to_year"] = to_year
    return _get(f"/api/v1/companies/{ticker}/cashflow", params=params)


def api_get_ratios(ticker: str, year: str | None = None) -> list[dict]:
    params: dict[str, str] = {}
    if year:
        params["year"] = year
    return _get(f"/api/v1/companies/{ticker}/ratios", params=params)


# ── Tearsheet ───────────────────────────────────────────────────────────────


def api_get_tearsheet(ticker: str) -> bytes | None:
    try:
        return _get_raw(f"/api/v1/companies/{ticker}/tearsheet")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise


# ── Screener ────────────────────────────────────────────────────────────────


def api_get_screener_presets() -> list[dict]:
    return _get("/api/v1/screener/")


def api_get_screener_results(preset: str) -> list[dict]:
    return _get(f"/api/v1/screener/{preset}")


# ── Sectors ─────────────────────────────────────────────────────────────────


def api_get_sectors() -> list[dict]:
    return _get("/api/v1/sectors/")


def api_get_sector_companies(
    sector: str, market_cap_category: str | None = None
) -> list[dict]:
    params: dict[str, str] = {}
    if market_cap_category:
        params["market_cap_category"] = market_cap_category
    return _get(f"/api/v1/sectors/{sector}/companies", params=params)


# ── Peers ───────────────────────────────────────────────────────────────────


def api_get_peers(ticker: str) -> dict:
    return _get(f"/api/v1/peers/{ticker}")


def api_get_peer_compare(ticker: str, year: str | None = None) -> dict:
    params: dict[str, str] = {}
    if year:
        params["year"] = year
    return _get(f"/api/v1/peers/{ticker}/compare", params=params)


# ── Market Cap ──────────────────────────────────────────────────────────────


def api_get_market_cap(
    year: str | None = None,
    sector: str | None = None,
    market_cap_category: str | None = None,
) -> list[dict]:
    params: dict[str, str] = {}
    if year:
        params["year"] = year
    if sector:
        params["sector"] = sector
    if market_cap_category:
        params["market_cap_category"] = market_cap_category
    return _get("/api/v1/market-cap/", params=params)


# ── Portfolio ───────────────────────────────────────────────────────────────


def api_get_portfolio_stats() -> list[dict]:
    return _get("/api/v1/portfolio/stats")


def api_get_portfolio_clusters() -> list[dict]:
    return _get("/api/v1/portfolio/clusters")


# ── Documents ───────────────────────────────────────────────────────────────


def api_get_documents(ticker: str, year: str | None = None) -> list[dict]:
    params: dict[str, str] = {}
    if year:
        params["year"] = year
    return _get(f"/api/v1/documents/{ticker}", params=params)


# ── Health ──────────────────────────────────────────────────────────────────


def api_health() -> dict:
    return _get("/api/v1/health")

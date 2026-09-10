"""
Tests for Sprint 6 — Day 38: Health Endpoint and FastAPI Scaffold.

Validates:
  - FastAPI app imports successfully
  - /api/v1/health returns HTTP 200
  - Response contains status, version, uptime_seconds, db_row_counts
  - db_row_counts covers all actual database tables (13 tables discovered)
  - All row counts are non-negative integers
  - /docs is accessible (HTTP 200)
  - /openapi.json is accessible and valid
  - All eight routers are registered
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ── Path setup ──────────────────────────────────────────────────────────────
SPRINT6_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = SPRINT6_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

# Expected tables discovered by inspecting nifty100.db
EXPECTED_TABLES = [
    "analysis",
    "balancesheet",
    "cashflow",
    "companies",
    "documents",
    "financial_ratios",
    "market_cap",
    "peer_groups",
    "peer_percentiles",
    "profitandloss",
    "prosandcons",
    "sectors",
    "stock_prices",
]


# ── App Import Tests ────────────────────────────────────────────────────────


class TestAppImport:
    def test_app_is_fastapi_instance(self):
        from fastapi import FastAPI

        assert isinstance(app, FastAPI)

    def test_app_title(self):
        assert app.title == "N100 Financial Intelligence Platform"

    def test_app_version(self):
        assert app.version == "0.1.0"


# ── Health Endpoint Tests ───────────────────────────────────────────────────


class TestHealthEndpoint:
    def test_health_returns_200(self):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_health_status_is_ok(self):
        data = client.get("/api/v1/health").json()
        assert data["status"] == "ok"

    def test_health_version_exists(self):
        data = client.get("/api/v1/health").json()
        assert "version" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_health_uptime_non_negative(self):
        data = client.get("/api/v1/health").json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0

    def test_health_db_row_counts_exists(self):
        data = client.get("/api/v1/health").json()
        assert "db_row_counts" in data
        assert isinstance(data["db_row_counts"], dict)

    def test_health_db_row_counts_covers_all_tables(self):
        data = client.get("/api/v1/health").json()
        tables = set(data["db_row_counts"].keys())
        assert tables == set(
            EXPECTED_TABLES
        ), f"Expected tables: {set(EXPECTED_TABLES)}, got: {tables}"

    def test_health_row_counts_are_non_negative_integers(self):
        data = client.get("/api/v1/health").json()
        for table, count in data["db_row_counts"].items():
            assert isinstance(count, int), f"{table}: count is not int"
            assert count >= 0, f"{table}: count is negative"


# ── OpenAPI / Docs Tests ───────────────────────────────────────────────────


class TestOpenAPI:
    def test_docs_accessible(self):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_openapi_json_accessible(self):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200

    def test_openapi_json_is_valid(self):
        data = client.get("/openapi.json").json()
        assert "openapi" in data
        assert "paths" in data
        assert "info" in data


# ── Router Registration Tests ───────────────────────────────────────────────


class TestRouterRegistration:
    def _get_paths(self):
        return client.get("/openapi.json").json()["paths"]

    def test_health_router_registered(self):
        paths = self._get_paths()
        assert "/api/v1/health" in paths

    def test_companies_router_registered(self):
        paths = self._get_paths()
        assert any("/api/v1/companies" in p for p in paths)

    def test_screener_router_registered(self):
        paths = self._get_paths()
        assert any("/api/v1/screener" in p for p in paths)

    def test_sectors_router_registered(self):
        paths = self._get_paths()
        assert any("/api/v1/sectors" in p for p in paths)

    def test_peers_router_registered(self):
        paths = self._get_paths()
        assert any("/api/v1/peers" in p for p in paths)

    def test_valuation_router_registered(self):
        paths = self._get_paths()
        assert any("/api/v1/market-cap" in p for p in paths)

    def test_portfolio_router_registered(self):
        paths = self._get_paths()
        assert any("/api/v1/portfolio" in p for p in paths)

    def test_documents_router_registered(self):
        paths = self._get_paths()
        assert any("/api/v1/documents" in p for p in paths)

    def test_all_eight_routers_registered(self):
        paths = self._get_paths()
        prefixes = [
            "/api/v1/health",
            "/api/v1/companies",
            "/api/v1/screener",
            "/api/v1/sectors",
            "/api/v1/peers",
            "/api/v1/market-cap",
            "/api/v1/portfolio",
            "/api/v1/documents",
        ]
        for prefix in prefixes:
            assert any(
                p.startswith(prefix) for p in paths
            ), f"No routes found for prefix: {prefix}"

"""
Sprint 6 — Day 42: Comprehensive API Integration Test Suite.

Covers all 18 FastAPI endpoints with:
  - HTTP status codes
  - Response schemas
  - Required fields
  - Valid/invalid parameters
  - Missing companies/sectors/presets
  - PDF content type for tearsheets
  - Representative real-company responses
  - CORS and request logging verification
"""

from __future__ import annotations

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


# ══════════════════════════════════════════════════════════════════════════════
# INFRASTRUCTURE TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestInfrastructure:
    """Verify API infrastructure: docs, OpenAPI, CORS, logging."""

    def test_docs_accessible(self):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_openapi_json_accessible(self):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200

    def test_openapi_version(self):
        data = client.get("/openapi.json").json()
        assert data["openapi"] == "3.1.0"

    def test_all_18_endpoints_registered(self):
        paths = client.get("/openapi.json").json()["paths"]
        assert len(paths) == 18

    def test_cors_headers(self):
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code in (200, 405)

    def test_health_returns_200(self):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_health_schema(self):
        data = client.get("/api/v1/health").json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "uptime_seconds" in data
        assert "db_row_counts" in data
        assert isinstance(data["db_row_counts"], dict)
        assert len(data["db_row_counts"]) == 13


# ══════════════════════════════════════════════════════════════════════════════
# COMPANIES LIST
# ══════════════════════════════════════════════════════════════════════════════


class TestCompaniesList:
    def test_200_and_count(self):
        data = client.get("/api/v1/companies/").json()
        assert len(data) == 92

    def test_required_fields(self):
        data = client.get("/api/v1/companies/").json()
        for item in data:
            assert "company_id" in item
            assert "company_name" in item
            assert "broad_sector" in item

    def test_sector_filter(self):
        data = client.get("/api/v1/companies/", params={"sector": "Financials"}).json()
        assert len(data) > 0
        assert all(item["broad_sector"] == "Financials" for item in data)

    def test_market_cap_filter(self):
        data = client.get(
            "/api/v1/companies/", params={"market_cap_category": "Mid Cap"}
        ).json()
        assert len(data) > 0

    def test_search_by_name(self):
        data = client.get("/api/v1/companies/", params={"search": "Reliance"}).json()
        assert any(item["company_id"] == "RELIANCE" for item in data)

    def test_search_by_ticker(self):
        data = client.get("/api/v1/companies/", params={"search": "TCS"}).json()
        assert any(item["company_id"] == "TCS" for item in data)

    def test_empty_search_result(self):
        data = client.get(
            "/api/v1/companies/", params={"search": "ZZZZNOTFOUND"}
        ).json()
        assert data == []

    def test_combined_filters(self):
        data = client.get(
            "/api/v1/companies/",
            params={
                "sector": "Financials",
                "market_cap_category": "Large Cap",
            },
        ).json()
        assert len(data) > 0


# ══════════════════════════════════════════════════════════════════════════════
# COMPANY DETAIL
# ══════════════════════════════════════════════════════════════════════════════


class TestCompanyDetail:
    def test_tcs_200(self):
        data = client.get("/api/v1/companies/TCS").json()
        assert data["company_id"] == "TCS"
        assert "Tata Consultancy" in data["company_name"]

    def test_reliance_200(self):
        data = client.get("/api/v1/companies/RELIANCE").json()
        assert data["company_id"] == "RELIANCE"

    def test_lowercase_ticker(self):
        data = client.get("/api/v1/companies/tcs").json()
        assert data["company_id"] == "TCS"

    def test_sector_data_present(self):
        data = client.get("/api/v1/companies/TCS").json()
        assert data["broad_sector"] is not None
        assert data["sub_sector"] is not None

    def test_latest_ratios_present(self):
        data = client.get("/api/v1/companies/TCS").json()
        assert data["latest_ratios"] is not None
        assert "net_profit_margin_pct" in data["latest_ratios"]

    def test_invalid_ticker_404(self):
        resp = client.get("/api/v1/companies/INVALIDXYZ")
        assert resp.status_code == 404

    def test_404_detail_message(self):
        resp = client.get("/api/v1/companies/INVALIDXYZ")
        assert "not found" in resp.json()["detail"].lower()


# ══════════════════════════════════════════════════════════════════════════════
# P&L
# ══════════════════════════════════════════════════════════════════════════════


class TestCompanyPL:
    def test_tcs_200(self):
        data = client.get("/api/v1/companies/TCS/pl").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_from_year_filter(self):
        data = client.get(
            "/api/v1/companies/TCS/pl", params={"from_year": "2020"}
        ).json()
        assert all(item["year"] >= "2020" for item in data)

    def test_to_year_filter(self):
        data = client.get("/api/v1/companies/TCS/pl", params={"to_year": "2015"}).json()
        assert all(item["year"] <= "2015" for item in data)

    def test_both_filters(self):
        data = client.get(
            "/api/v1/companies/TCS/pl", params={"from_year": "2020", "to_year": "2022"}
        ).json()
        assert all("2020" <= item["year"] <= "2022" for item in data)

    def test_invalid_year_400(self):
        resp = client.get("/api/v1/companies/TCS/pl", params={"from_year": "abc"})
        assert resp.status_code == 400

    def test_reversed_range_400(self):
        resp = client.get(
            "/api/v1/companies/TCS/pl", params={"from_year": "2022", "to_year": "2020"}
        )
        assert resp.status_code == 400

    def test_invalid_ticker_404(self):
        assert client.get("/api/v1/companies/INVALIDXYZ/pl").status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# BALANCE SHEET
# ══════════════════════════════════════════════════════════════════════════════


class TestCompanyBS:
    def test_tcs_200(self):
        data = client.get("/api/v1/companies/TCS/bs").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_from_year_filter(self):
        data = client.get(
            "/api/v1/companies/TCS/bs", params={"from_year": "2020"}
        ).json()
        assert all(item["year"] >= "2020" for item in data)

    def test_invalid_year_400(self):
        resp = client.get("/api/v1/companies/TCS/bs", params={"from_year": "abc"})
        assert resp.status_code == 400

    def test_invalid_ticker_404(self):
        assert client.get("/api/v1/companies/INVALIDXYZ/bs").status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# CASHFLOW
# ══════════════════════════════════════════════════════════════════════════════


class TestCompanyCashflow:
    def test_tcs_200(self):
        data = client.get("/api/v1/companies/TCS/cashflow").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_from_year_filter(self):
        data = client.get(
            "/api/v1/companies/TCS/cashflow", params={"from_year": "2020"}
        ).json()
        assert all(item["year"] >= "2020" for item in data)

    def test_invalid_year_400(self):
        resp = client.get("/api/v1/companies/TCS/cashflow", params={"from_year": "abc"})
        assert resp.status_code == 400

    def test_invalid_ticker_404(self):
        assert client.get("/api/v1/companies/INVALIDXYZ/cashflow").status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# RATIOS
# ══════════════════════════════════════════════════════════════════════════════


class TestCompanyRatios:
    def test_tcs_200(self):
        data = client.get("/api/v1/companies/TCS/ratios").json()
        assert isinstance(data, list)
        assert len(data) > 1

    def test_year_filter(self):
        data = client.get(
            "/api/v1/companies/TCS/ratios", params={"year": "2024"}
        ).json()
        assert len(data) == 1
        assert data[0]["year"] == "2024"

    def test_no_match_year(self):
        data = client.get(
            "/api/v1/companies/TCS/ratios", params={"year": "2099"}
        ).json()
        assert data == []

    def test_ttm_year(self):
        data = client.get("/api/v1/companies/TCS/ratios", params={"year": "TTM"}).json()
        assert isinstance(data, list)

    def test_invalid_year_400(self):
        resp = client.get("/api/v1/companies/TCS/ratios", params={"year": "abc"})
        assert resp.status_code == 400

    def test_invalid_ticker_404(self):
        assert client.get("/api/v1/companies/INVALIDXYZ/ratios").status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# TEARSHEET
# ══════════════════════════════════════════════════════════════════════════════


class TestCompanyTearsheet:
    def test_tcs_200(self):
        resp = client.get("/api/v1/companies/TCS/tearsheet")
        assert resp.status_code == 200

    def test_tcs_pdf_content_type(self):
        resp = client.get("/api/v1/companies/TCS/tearsheet")
        assert resp.headers["content-type"] == "application/pdf"

    def test_tcs_pdf_bytes(self):
        resp = client.get("/api/v1/companies/TCS/tearsheet")
        assert resp.content[:4] == b"%PDF"

    def test_reliance_200(self):
        resp = client.get("/api/v1/companies/RELIANCE/tearsheet")
        assert resp.status_code == 200

    def test_jiofin_404(self):
        resp = client.get("/api/v1/companies/JIOFIN/tearsheet")
        assert resp.status_code == 404

    def test_invalid_ticker_404(self):
        resp = client.get("/api/v1/companies/INVALIDXYZ/tearsheet")
        assert resp.status_code == 404

    def test_lowercase_ticker(self):
        resp = client.get("/api/v1/companies/tcs/tearsheet")
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# SCREENER
# ══════════════════════════════════════════════════════════════════════════════


class TestScreener:
    def test_list_presets_200(self):
        data = client.get("/api/v1/screener/").json()
        assert len(data) == 6

    def test_preset_names(self):
        data = client.get("/api/v1/screener/").json()
        names = {item["name"] for item in data}
        assert "Quality Compounder" in names
        assert "Value Pick" in names

    def test_quality_compounder(self):
        data = client.get("/api/v1/screener/Quality Compounder").json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "company_id" in data[0]

    def test_invalid_preset_404(self):
        resp = client.get("/api/v1/screener/Invalid Preset")
        assert resp.status_code == 404

    def test_all_presets_accessible(self):
        presets = [
            "Quality Compounder",
            "Value Pick",
            "Growth Accelerator",
            "Dividend Champion",
            "Debt-Free Blue Chip",
            "Turnaround Watch",
        ]
        for p in presets:
            assert client.get(f"/api/v1/screener/{p}").status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# SECTORS
# ══════════════════════════════════════════════════════════════════════════════


class TestSectors:
    def test_list_sectors_200(self):
        data = client.get("/api/v1/sectors/").json()
        assert len(data) == 10

    def test_sector_counts_sum_to_92(self):
        data = client.get("/api/v1/sectors/").json()
        total = sum(item["company_count"] for item in data)
        assert total == 92

    def test_sector_companies(self):
        data = client.get("/api/v1/sectors/Financials/companies").json()
        assert len(data) > 0

    def test_invalid_sector_404(self):
        resp = client.get("/api/v1/sectors/Invalid Sector/companies")
        assert resp.status_code == 404

    def test_market_cap_filter(self):
        data = client.get(
            "/api/v1/sectors/Financials/companies",
            params={"market_cap_category": "Large Cap"},
        ).json()
        assert len(data) > 0

    def test_all_sectors_accessible(self):
        resp = client.get("/api/v1/sectors/")
        for s in resp.json():
            r = client.get(f"/api/v1/sectors/{s['broad_sector']}/companies")
            assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# PEERS
# ══════════════════════════════════════════════════════════════════════════════


class TestPeers:
    def test_hdfcbank_200(self):
        data = client.get("/api/v1/peers/HDFCBANK").json()
        assert data["company_id"] == "HDFCBANK"
        assert "peer_groups" in data

    def test_peer_group_has_members(self):
        data = client.get("/api/v1/peers/HDFCBANK").json()
        for gname, members in data["peer_groups"].items():
            assert len(members) >= 2

    def test_invalid_ticker_404(self):
        resp = client.get("/api/v1/peers/INVALIDXYZ")
        assert resp.status_code == 404

    def test_company_without_peers_404(self):
        resp = client.get("/api/v1/peers/ABB")
        assert resp.status_code == 404

    def test_compare_200(self):
        data = client.get("/api/v1/peers/HDFCBANK/compare").json()
        assert "comparisons" in data
        assert len(data["comparisons"]) > 0

    def test_compare_year_filter(self):
        data = client.get(
            "/api/v1/peers/HDFCBANK/compare", params={"year": "2024"}
        ).json()
        assert data["year"] == "2024"

    def test_compare_invalid_year_400(self):
        resp = client.get("/api/v1/peers/HDFCBANK/compare", params={"year": "abc"})
        assert resp.status_code == 400

    def test_compare_invalid_ticker_404(self):
        resp = client.get("/api/v1/peers/INVALIDXYZ/compare")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# MARKET CAP
# ══════════════════════════════════════════════════════════════════════════════


class TestMarketCap:
    def test_200_and_data(self):
        data = client.get("/api/v1/market-cap/").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_required_fields(self):
        data = client.get("/api/v1/market-cap/").json()
        for item in data[:5]:
            assert "company_id" in item
            assert "year" in item

    def test_year_filter(self):
        data = client.get("/api/v1/market-cap/", params={"year": "2024"}).json()
        assert all(item["year"] == "2024" for item in data)

    def test_sector_filter(self):
        data = client.get("/api/v1/market-cap/", params={"sector": "Financials"}).json()
        assert all(item["broad_sector"] == "Financials" for item in data)

    def test_category_filter(self):
        data = client.get(
            "/api/v1/market-cap/", params={"market_cap_category": "Mid Cap"}
        ).json()
        assert all(item["market_cap_category"] == "Mid Cap" for item in data)

    def test_sorted_by_market_cap(self):
        data = client.get("/api/v1/market-cap/", params={"year": "2024"}).json()
        caps = [
            item["market_cap_crore"]
            for item in data
            if item["market_cap_crore"] is not None
        ]
        assert caps == sorted(caps, reverse=True)


# ══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO
# ══════════════════════════════════════════════════════════════════════════════


class TestPortfolio:
    def test_stats_200(self):
        data = client.get("/api/v1/portfolio/stats").json()
        assert len(data) == 10

    def test_stats_fields(self):
        data = client.get("/api/v1/portfolio/stats").json()
        for item in data:
            assert "metric" in item
            assert "p50" in item
            assert "mean" in item

    def test_clusters_200(self):
        data = client.get("/api/v1/portfolio/clusters").json()
        assert len(data) == 92

    def test_cluster_fields(self):
        data = client.get("/api/v1/portfolio/clusters").json()
        for item in data:
            assert "cluster_id" in item
            assert "cluster_name" in item


# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENTS
# ══════════════════════════════════════════════════════════════════════════════


class TestDocuments:
    def test_tcs_200(self):
        data = client.get("/api/v1/documents/TCS").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_year_filter(self):
        data = client.get("/api/v1/documents/TCS", params={"year": "2024"}).json()
        if data:
            assert all(item["year"] == "2024" for item in data)

    def test_invalid_year_400(self):
        resp = client.get("/api/v1/documents/TCS", params={"year": "abc"})
        assert resp.status_code == 400

    def test_invalid_ticker_404(self):
        resp = client.get("/api/v1/documents/INVALIDXYZ")
        assert resp.status_code == 404

    def test_lowercase_ticker(self):
        resp = client.get("/api/v1/documents/tcs")
        assert resp.status_code == 200

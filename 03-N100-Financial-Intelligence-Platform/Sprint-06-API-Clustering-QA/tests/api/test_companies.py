"""
Tests for Sprint 6 — Day 39: Company Data Endpoints.

Validates all 7 endpoints:
  GET /api/v1/companies
  GET /api/v1/companies/{ticker}
  GET /api/v1/companies/{ticker}/pl
  GET /api/v1/companies/{ticker}/bs
  GET /api/v1/companies/{ticker}/cashflow
  GET /api/v1/companies/{ticker}/ratios
  GET /api/v1/companies/{ticker}/tearsheet
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
# 1. GET /api/v1/companies
# ══════════════════════════════════════════════════════════════════════════════


class TestCompaniesList:
    def test_returns_200(self):
        assert client.get("/api/v1/companies").status_code == 200

    def test_returns_92_companies(self):
        data = client.get("/api/v1/companies").json()
        assert len(data) == 92

    def test_required_fields_present(self):
        data = client.get("/api/v1/companies").json()
        required = {
            "company_id",
            "company_name",
            "broad_sector",
            "sub_sector",
            "roe_pct",
            "roce_pct",
        }
        for item in data:
            assert required.issubset(
                set(item.keys())
            ), f"Missing fields in {item.get('company_id')}: {required - set(item.keys())}"

    def test_sector_filter(self):
        data = client.get(
            "/api/v1/companies", params={"sector": "Information Technology"}
        ).json()
        assert len(data) > 0
        assert all(item["broad_sector"] == "Information Technology" for item in data)

    def test_market_cap_filter(self):
        data = client.get(
            "/api/v1/companies", params={"market_cap_category": "Large Cap"}
        ).json()
        assert len(data) > 0
        assert all(item["market_cap_category"] == "Large Cap" for item in data)

    def test_search_by_name(self):
        data = client.get("/api/v1/companies", params={"search": "Tata"}).json()
        assert len(data) > 0
        assert any("Tata" in item["company_name"] for item in data)

    def test_search_by_ticker(self):
        data = client.get("/api/v1/companies", params={"search": "TCS"}).json()
        assert len(data) >= 1
        assert any(item["company_id"] == "TCS" for item in data)

    def test_combined_filters(self):
        data = client.get(
            "/api/v1/companies",
            params={
                "sector": "Information Technology",
                "market_cap_category": "Large Cap",
            },
        ).json()
        assert len(data) > 0
        assert all(
            item["broad_sector"] == "Information Technology"
            and item["market_cap_category"] == "Large Cap"
            for item in data
        )

    def test_empty_search_returns_valid_list(self):
        data = client.get("/api/v1/companies", params={"search": "ZZZZNOTFOUND"}).json()
        assert isinstance(data, list)
        assert len(data) == 0


# ══════════════════════════════════════════════════════════════════════════════
# 2. GET /api/v1/companies/{ticker}
# ══════════════════════════════════════════════════════════════════════════════


class TestCompanyDetail:
    def test_returns_200(self):
        assert client.get("/api/v1/companies/TCS").status_code == 200

    def test_correct_company(self):
        data = client.get("/api/v1/companies/TCS").json()
        assert data["company_id"] == "TCS"
        assert "Tata Consultancy Services" in data["company_name"]

    def test_sector_data_present(self):
        data = client.get("/api/v1/companies/TCS").json()
        assert data["broad_sector"] is not None
        assert data["sub_sector"] is not None

    def test_latest_kpi_data_present(self):
        data = client.get("/api/v1/companies/TCS").json()
        assert data["latest_ratios"] is not None
        assert "net_profit_margin_pct" in data["latest_ratios"]

    def test_lowercase_ticker_works(self):
        data = client.get("/api/v1/companies/tcs").json()
        assert data["company_id"] == "TCS"

    def test_invalid_ticker_returns_404(self):
        resp = client.get("/api/v1/companies/INVALIDXYZ")
        assert resp.status_code == 404

    def test_404_detail_message(self):
        resp = client.get("/api/v1/companies/INVALIDXYZ")
        assert "not found" in resp.json()["detail"].lower()


# ══════════════════════════════════════════════════════════════════════════════
# 3. GET /api/v1/companies/{ticker}/pl
# ══════════════════════════════════════════════════════════════════════════════


class TestCompanyPL:
    def test_returns_200(self):
        assert client.get("/api/v1/companies/TCS/pl").status_code == 200

    def test_returns_array(self):
        data = client.get("/api/v1/companies/TCS/pl").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_from_year_filter(self):
        data = client.get(
            "/api/v1/companies/TCS/pl", params={"from_year": "2020"}
        ).json()
        assert all(item["year"] >= "2020" for item in data)

    def test_to_year_filter(self):
        data = client.get("/api/v1/companies/TCS/pl", params={"to_year": "2020"}).json()
        assert all(item["year"] <= "2020" for item in data)

    def test_both_filters(self):
        data = client.get(
            "/api/v1/companies/TCS/pl", params={"from_year": "2020", "to_year": "2022"}
        ).json()
        assert all("2020" <= item["year"] <= "2022" for item in data)

    def test_invalid_year_returns_400(self):
        resp = client.get("/api/v1/companies/TCS/pl", params={"from_year": "abc"})
        assert resp.status_code == 400

    def test_reversed_range_returns_400(self):
        resp = client.get(
            "/api/v1/companies/TCS/pl", params={"from_year": "2022", "to_year": "2020"}
        )
        assert resp.status_code == 400

    def test_invalid_ticker_returns_404(self):
        assert client.get("/api/v1/companies/INVALIDXYZ/pl").status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 4. GET /api/v1/companies/{ticker}/bs
# ══════════════════════════════════════════════════════════════════════════════


class TestCompanyBS:
    def test_returns_200(self):
        assert client.get("/api/v1/companies/TCS/bs").status_code == 200

    def test_returns_array(self):
        data = client.get("/api/v1/companies/TCS/bs").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_from_year_filter(self):
        data = client.get(
            "/api/v1/companies/TCS/bs", params={"from_year": "2020"}
        ).json()
        assert all(item["year"] >= "2020" for item in data)

    def test_to_year_filter(self):
        data = client.get("/api/v1/companies/TCS/bs", params={"to_year": "2020"}).json()
        assert all(item["year"] <= "2020" for item in data)

    def test_invalid_year_returns_400(self):
        resp = client.get("/api/v1/companies/TCS/bs", params={"from_year": "abc"})
        assert resp.status_code == 400

    def test_reversed_range_returns_400(self):
        resp = client.get(
            "/api/v1/companies/TCS/bs", params={"from_year": "2022", "to_year": "2020"}
        )
        assert resp.status_code == 400

    def test_invalid_ticker_returns_404(self):
        assert client.get("/api/v1/companies/INVALIDXYZ/bs").status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 5. GET /api/v1/companies/{ticker}/cashflow
# ══════════════════════════════════════════════════════════════════════════════


class TestCompanyCashflow:
    def test_returns_200(self):
        assert client.get("/api/v1/companies/TCS/cashflow").status_code == 200

    def test_returns_array(self):
        data = client.get("/api/v1/companies/TCS/cashflow").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_from_year_filter(self):
        data = client.get(
            "/api/v1/companies/TCS/cashflow", params={"from_year": "2020"}
        ).json()
        assert all(item["year"] >= "2020" for item in data)

    def test_to_year_filter(self):
        data = client.get(
            "/api/v1/companies/TCS/cashflow", params={"to_year": "2020"}
        ).json()
        assert all(item["year"] <= "2020" for item in data)

    def test_invalid_year_returns_400(self):
        resp = client.get("/api/v1/companies/TCS/cashflow", params={"from_year": "abc"})
        assert resp.status_code == 400

    def test_invalid_ticker_returns_404(self):
        assert client.get("/api/v1/companies/INVALIDXYZ/cashflow").status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 6. GET /api/v1/companies/{ticker}/ratios
# ══════════════════════════════════════════════════════════════════════════════


class TestCompanyRatios:
    def test_returns_200(self):
        assert client.get("/api/v1/companies/TCS/ratios").status_code == 200

    def test_returns_multiple_years(self):
        data = client.get("/api/v1/companies/TCS/ratios").json()
        assert isinstance(data, list)
        assert len(data) > 1

    def test_year_filter_single(self):
        data = client.get(
            "/api/v1/companies/TCS/ratios", params={"year": "2024"}
        ).json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["year"] == "2024"

    def test_year_filter_no_match(self):
        data = client.get(
            "/api/v1/companies/TCS/ratios", params={"year": "2099"}
        ).json()
        assert data == []

    def test_invalid_year_returns_400(self):
        resp = client.get("/api/v1/companies/TCS/ratios", params={"year": "abc"})
        assert resp.status_code == 400

    def test_invalid_ticker_returns_404(self):
        assert client.get("/api/v1/companies/INVALIDXYZ/ratios").status_code == 404

    def test_ttm_year_works(self):
        data = client.get("/api/v1/companies/TCS/ratios", params={"year": "TTM"}).json()
        assert isinstance(data, list)


# ══════════════════════════════════════════════════════════════════════════════
# 7. GET /api/v1/companies/{ticker}/tearsheet
# ══════════════════════════════════════════════════════════════════════════════


class TestCompanyTearsheet:
    def test_returns_200(self):
        resp = client.get("/api/v1/companies/TCS/tearsheet")
        assert resp.status_code == 200

    def test_content_type_is_pdf(self):
        resp = client.get("/api/v1/companies/TCS/tearsheet")
        assert resp.headers["content-type"] == "application/pdf"

    def test_response_contains_pdf_bytes(self):
        resp = client.get("/api/v1/companies/TCS/tearsheet")
        assert resp.content[:4] == b"%PDF"

    def test_jiofin_missing_tearsheet_returns_404(self):
        resp = client.get("/api/v1/companies/JIOFIN/tearsheet")
        assert resp.status_code == 404

    def test_invalid_ticker_returns_404(self):
        resp = client.get("/api/v1/companies/INVALIDXYZ/tearsheet")
        assert resp.status_code == 404

    def test_lowercase_tearsheet_works(self):
        resp = client.get("/api/v1/companies/tcs/tearsheet")
        assert resp.status_code == 200

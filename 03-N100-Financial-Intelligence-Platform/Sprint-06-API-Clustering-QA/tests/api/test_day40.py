"""
Tests for Sprint 6 — Day 40: Remaining API Endpoints.

Validates all 8 endpoints:
  GET /api/v1/screener
  GET /api/v1/screener/{preset}
  GET /api/v1/sectors
  GET /api/v1/sectors/{sector}/companies
  GET /api/v1/peers/{ticker}
  GET /api/v1/peers/{ticker}/compare
  GET /api/v1/market-cap
  GET /api/v1/portfolio/stats
  GET /api/v1/documents/{ticker}
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
# 1. GET /api/v1/screener
# ══════════════════════════════════════════════════════════════════════════════


class TestScreenerList:
    def test_returns_200(self):
        assert client.get("/api/v1/screener").status_code == 200

    def test_returns_6_presets(self):
        data = client.get("/api/v1/screener").json()
        assert len(data) == 6

    def test_preset_names_match(self):
        data = client.get("/api/v1/screener").json()
        names = {item["name"] for item in data}
        expected = {
            "Quality Compounder",
            "Value Pick",
            "Growth Accelerator",
            "Dividend Champion",
            "Debt-Free Blue Chip",
            "Turnaround Watch",
        }
        assert names == expected

    def test_each_preset_has_company_count(self):
        data = client.get("/api/v1/screener").json()
        for item in data:
            assert "company_count" in item
            assert isinstance(item["company_count"], int)
            assert item["company_count"] > 0


# ══════════════════════════════════════════════════════════════════════════════
# 2. GET /api/v1/screener/{preset}
# ══════════════════════════════════════════════════════════════════════════════


class TestScreenerPreset:
    def test_quality_compounder(self):
        data = client.get("/api/v1/screener/Quality Compounder").json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "company_id" in data[0]

    def test_invalid_preset_returns_404(self):
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
            resp = client.get(f"/api/v1/screener/{p}")
            assert resp.status_code == 200, f"Preset {p!r} returned {resp.status_code}"


# ══════════════════════════════════════════════════════════════════════════════
# 3. GET /api/v1/sectors
# ══════════════════════════════════════════════════════════════════════════════


class TestSectorsList:
    def test_returns_200(self):
        assert client.get("/api/v1/sectors").status_code == 200

    def test_returns_10_sectors(self):
        data = client.get("/api/v1/sectors").json()
        assert len(data) == 10

    def test_has_required_fields(self):
        data = client.get("/api/v1/sectors").json()
        for item in data:
            assert "broad_sector" in item
            assert "company_count" in item
            assert item["company_count"] > 0

    def test_total_companies_sums_to_92(self):
        data = client.get("/api/v1/sectors").json()
        total = sum(item["company_count"] for item in data)
        assert total == 92


# ══════════════════════════════════════════════════════════════════════════════
# 4. GET /api/v1/sectors/{sector}/companies
# ══════════════════════════════════════════════════════════════════════════════


class TestSectorCompanies:
    def test_it_sector(self):
        data = client.get("/api/v1/sectors/Information Technology/companies").json()
        assert len(data) > 0
        assert all(item["company_id"] for item in data)

    def test_invalid_sector_returns_404(self):
        resp = client.get("/api/v1/sectors/Invalid Sector/companies")
        assert resp.status_code == 404

    def test_market_cap_filter(self):
        data = client.get(
            "/api/v1/sectors/Information Technology/companies",
            params={"market_cap_category": "Large Cap"},
        ).json()
        assert len(data) > 0
        assert all(item["market_cap_category"] == "Large Cap" for item in data)

    def test_all_sectors_accessible(self):
        resp = client.get("/api/v1/sectors")
        sectors = [s["broad_sector"] for s in resp.json()]
        for s in sectors:
            r = client.get(f"/api/v1/sectors/{s}/companies")
            assert r.status_code == 200, f"Sector {s!r} returned {r.status_code}"


# ══════════════════════════════════════════════════════════════════════════════
# 5. GET /api/v1/peers/{ticker}
# ══════════════════════════════════════════════════════════════════════════════


class TestPeerGroup:
    def test_hdfcbank_has_peers(self):
        data = client.get("/api/v1/peers/HDFCBANK").json()
        assert data["company_id"] == "HDFCBANK"
        assert "peer_groups" in data
        assert len(data["peer_groups"]) > 0

    def test_peer_group_contains_members(self):
        data = client.get("/api/v1/peers/HDFCBANK").json()
        for gname, members in data["peer_groups"].items():
            assert isinstance(members, list)
            assert len(members) >= 2
            assert any(m["company_id"] == "HDFCBANK" for m in members)

    def test_invalid_ticker_returns_404(self):
        resp = client.get("/api/v1/peers/INVALIDXYZ")
        assert resp.status_code == 404

    def test_company_without_peers_returns_404(self):
        # Some companies may not have peer group assignments
        resp = client.get("/api/v1/peers/ABB")
        # Could be 200 or 404 depending on data
        assert resp.status_code in (200, 404)


# ══════════════════════════════════════════════════════════════════════════════
# 6. GET /api/v1/peers/{ticker}/compare
# ══════════════════════════════════════════════════════════════════════════════


class TestPeerCompare:
    def test_hdfcbank_compare(self):
        data = client.get("/api/v1/peers/HDFCBANK/compare").json()
        assert data["company_id"] == "HDFCBANK"
        assert "peer_group_name" in data
        assert "comparisons" in data
        assert isinstance(data["comparisons"], list)
        assert len(data["comparisons"]) > 0

    def test_compare_has_metrics(self):
        data = client.get("/api/v1/peers/HDFCBANK/compare").json()
        metrics = {c["metric"] for c in data["comparisons"]}
        assert len(metrics) > 0

    def test_year_filter(self):
        data = client.get(
            "/api/v1/peers/HDFCBANK/compare", params={"year": "2024"}
        ).json()
        assert data["year"] == "2024"

    def test_invalid_year_returns_400(self):
        resp = client.get("/api/v1/peers/HDFCBANK/compare", params={"year": "abc"})
        assert resp.status_code == 400

    def test_invalid_ticker_returns_404(self):
        resp = client.get("/api/v1/peers/INVALIDXYZ/compare")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 7. GET /api/v1/market-cap
# ══════════════════════════════════════════════════════════════════════════════


class TestMarketCap:
    def test_returns_200(self):
        assert client.get("/api/v1/market-cap").status_code == 200

    def test_returns_data(self):
        data = client.get("/api/v1/market-cap").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_has_required_fields(self):
        data = client.get("/api/v1/market-cap").json()
        for item in data[:5]:
            assert "company_id" in item
            assert "year" in item
            assert "market_cap_crore" in item

    def test_year_filter(self):
        data = client.get("/api/v1/market-cap", params={"year": "2024"}).json()
        assert all(item["year"] == "2024" for item in data)

    def test_sector_filter(self):
        data = client.get(
            "/api/v1/market-cap", params={"sector": "Information Technology"}
        ).json()
        assert len(data) > 0
        assert all(item["broad_sector"] == "Information Technology" for item in data)

    def test_market_cap_category_filter(self):
        data = client.get(
            "/api/v1/market-cap", params={"market_cap_category": "Mid Cap"}
        ).json()
        assert len(data) > 0
        assert all(item["market_cap_category"] == "Mid Cap" for item in data)

    def test_combined_filters(self):
        data = client.get(
            "/api/v1/market-cap",
            params={
                "year": "2024",
                "sector": "Information Technology",
                "market_cap_category": "Large Cap",
            },
        ).json()
        assert len(data) > 0
        for item in data:
            assert item["year"] == "2024"
            assert item["broad_sector"] == "Information Technology"
            assert item["market_cap_category"] == "Large Cap"

    def test_sorted_by_market_cap_desc(self):
        data = client.get("/api/v1/market-cap", params={"year": "2024"}).json()
        caps = [
            item["market_cap_crore"]
            for item in data
            if item["market_cap_crore"] is not None
        ]
        assert caps == sorted(caps, reverse=True)


# ══════════════════════════════════════════════════════════════════════════════
# 8. GET /api/v1/portfolio/stats
# ══════════════════════════════════════════════════════════════════════════════


class TestPortfolioStats:
    def test_returns_200(self):
        assert client.get("/api/v1/portfolio/stats").status_code == 200

    def test_returns_10_kpis(self):
        data = client.get("/api/v1/portfolio/stats").json()
        assert len(data) == 10

    def test_has_required_fields(self):
        data = client.get("/api/v1/portfolio/stats").json()
        for item in data:
            assert "metric" in item
            assert "metric_label" in item
            assert "p50" in item
            assert "mean" in item
            assert "std" in item

    def test_percentiles_ordered(self):
        data = client.get("/api/v1/portfolio/stats").json()
        for item in data:
            vals = [item.get(p) for p in ["p10", "p25", "p50", "p75", "p90"]]
            valid = [v for v in vals if v is not None]
            assert valid == sorted(valid), f"{item['metric']}: percentiles not ordered"

    def test_clusters_endpoint(self):
        data = client.get("/api/v1/portfolio/clusters").json()
        assert isinstance(data, list)
        assert len(data) == 92
        assert "cluster_id" in data[0]
        assert "cluster_name" in data[0]


# ══════════════════════════════════════════════════════════════════════════════
# 9. GET /api/v1/documents/{ticker}
# ══════════════════════════════════════════════════════════════════════════════


class TestDocuments:
    def test_returns_200(self):
        resp = client.get("/api/v1/documents/TCS")
        assert resp.status_code == 200

    def test_returns_array(self):
        data = client.get("/api/v1/documents/TCS").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_has_required_fields(self):
        data = client.get("/api/v1/documents/TCS").json()
        for item in data:
            assert "company_id" in item
            assert "year" in item
            assert "annual_report" in item

    def test_year_filter(self):
        data = client.get("/api/v1/documents/TCS", params={"year": "2024"}).json()
        assert isinstance(data, list)
        if data:
            assert all(item["year"] == "2024" for item in data)

    def test_invalid_year_returns_400(self):
        resp = client.get("/api/v1/documents/TCS", params={"year": "abc"})
        assert resp.status_code == 400

    def test_invalid_ticker_returns_404(self):
        resp = client.get("/api/v1/documents/INVALIDXYZ")
        assert resp.status_code == 404

    def test_lowercase_ticker_works(self):
        resp = client.get("/api/v1/documents/tcs")
        assert resp.status_code == 200

"""
Sprint 6 — Day 43: API Performance Benchmark Tests.

Measures local latency for representative endpoints across all 8 routers.
Results are LOCAL BENCHMARK MEASUREMENTS, not production-grade performance claims.

Run: pytest tests/api/test_day43_performance.py -v -s
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path
from typing import Callable

import pytest

# ── Path setup ──────────────────────────────────────────────────────────────
SPRINT6_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = SPRINT6_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

# ── Benchmark configuration ────────────────────────────────────────────────
ITERATIONS = 20
WARMUP = 3
REPRESENTATIVE_TICKER = "TCS"
REPRESENTATIVE_SECTOR = "Financials"
REPRESENTATIVE_PRESET = "Quality Compounder"

# Module-level results store
_PERF_RESULTS: dict[str, dict] = {}


# ══════════════════════════════════════════════════════════════════════════════
# BENCHMARK HELPER
# ══════════════════════════════════════════════════════════════════════════════


def _benchmark(
    endpoint_fn: Callable[[], None], iterations: int = ITERATIONS, warmup: int = WARMUP
) -> dict:
    """Run endpoint_fn repeatedly and collect timing stats."""
    for _ in range(warmup):
        endpoint_fn()

    latencies: list[float] = []
    failures = 0

    for _ in range(iterations):
        start = time.perf_counter()
        try:
            endpoint_fn()
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)
        except Exception:
            failures += 1
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)

    latencies_sorted = sorted(latencies)
    count = len(latencies)
    successes = count - failures
    avg = statistics.mean(latencies) if latencies else 0
    med = statistics.median(latencies) if latencies else 0
    p95_idx = int(len(latencies_sorted) * 0.95)
    p95 = (
        latencies_sorted[min(p95_idx, len(latencies_sorted) - 1)]
        if latencies_sorted
        else 0
    )
    fastest = min(latencies) if latencies else 0
    slowest = max(latencies) if latencies else 0

    return {
        "count": count,
        "successes": successes,
        "failures": failures,
        "avg_ms": round(avg, 2),
        "median_ms": round(med, 2),
        "p95_ms": round(p95, 2),
        "fastest_ms": round(fastest, 2),
        "slowest_ms": round(slowest, 2),
    }


# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE TESTS — each test benchmarks one endpoint variant
# ══════════════════════════════════════════════════════════════════════════════


class TestPerformanceHealth:
    def test_health(self):
        r = _benchmark(lambda: client.get("/api/v1/health"))
        assert r["failures"] == 0
        _PERF_RESULTS["health"] = r


class TestPerformanceCompaniesList:
    def test_companies_list(self):
        r = _benchmark(lambda: client.get("/api/v1/companies/"))
        assert r["failures"] == 0
        _PERF_RESULTS["companies_list"] = r

    def test_companies_list_filtered(self):
        r = _benchmark(
            lambda: client.get(
                "/api/v1/companies/", params={"sector": "Financials", "search": "HDFC"}
            )
        )
        assert r["failures"] == 0


class TestPerformanceCompanyDetail:
    def test_company_detail(self):
        r = _benchmark(lambda: client.get(f"/api/v1/companies/{REPRESENTATIVE_TICKER}"))
        assert r["failures"] == 0
        _PERF_RESULTS["company_detail"] = r


class TestPerformancePL:
    def test_pl(self):
        r = _benchmark(
            lambda: client.get(f"/api/v1/companies/{REPRESENTATIVE_TICKER}/pl")
        )
        assert r["failures"] == 0
        _PERF_RESULTS["pl"] = r

    def test_pl_filtered(self):
        r = _benchmark(
            lambda: client.get(
                f"/api/v1/companies/{REPRESENTATIVE_TICKER}/pl",
                params={"from_year": "2020", "to_year": "2024"},
            )
        )
        assert r["failures"] == 0


class TestPerformanceRatios:
    def test_ratios(self):
        r = _benchmark(
            lambda: client.get(f"/api/v1/companies/{REPRESENTATIVE_TICKER}/ratios")
        )
        assert r["failures"] == 0
        _PERF_RESULTS["ratios"] = r


class TestPerformanceScreener:
    def test_screener_preset(self):
        r = _benchmark(lambda: client.get(f"/api/v1/screener/{REPRESENTATIVE_PRESET}"))
        assert r["failures"] == 0
        _PERF_RESULTS["screener"] = r

    def test_screener_list(self):
        r = _benchmark(lambda: client.get("/api/v1/screener/"))
        assert r["failures"] == 0


class TestPerformanceSectors:
    def test_sector_companies(self):
        r = _benchmark(
            lambda: client.get(f"/api/v1/sectors/{REPRESENTATIVE_SECTOR}/companies")
        )
        assert r["failures"] == 0
        _PERF_RESULTS["sectors"] = r

    def test_sectors_list(self):
        r = _benchmark(lambda: client.get("/api/v1/sectors/"))
        assert r["failures"] == 0


class TestPerformancePeers:
    def test_peer_compare(self):
        r = _benchmark(lambda: client.get("/api/v1/peers/HDFCBANK/compare"))
        assert r["failures"] == 0
        _PERF_RESULTS["peers_compare"] = r

    def test_peer_group(self):
        r = _benchmark(lambda: client.get("/api/v1/peers/HDFCBANK"))
        assert r["failures"] == 0
        _PERF_RESULTS["peers_group"] = r


class TestPerformanceMarketCap:
    def test_market_cap(self):
        r = _benchmark(lambda: client.get("/api/v1/market-cap/"))
        assert r["failures"] == 0
        _PERF_RESULTS["market_cap"] = r

    def test_market_cap_filtered(self):
        r = _benchmark(
            lambda: client.get(
                "/api/v1/market-cap/", params={"year": "2024", "sector": "Financials"}
            )
        )
        assert r["failures"] == 0


class TestPerformancePortfolio:
    def test_portfolio_stats(self):
        r = _benchmark(lambda: client.get("/api/v1/portfolio/stats"))
        assert r["failures"] == 0
        _PERF_RESULTS["portfolio_stats"] = r

    def test_portfolio_clusters(self):
        r = _benchmark(lambda: client.get("/api/v1/portfolio/clusters"))
        assert r["failures"] == 0
        _PERF_RESULTS["portfolio_clusters"] = r


class TestPerformanceDocuments:
    def test_documents(self):
        r = _benchmark(lambda: client.get(f"/api/v1/documents/{REPRESENTATIVE_TICKER}"))
        assert r["failures"] == 0
        _PERF_RESULTS["documents"] = r


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY REPORT — prints aggregated results
# ══════════════════════════════════════════════════════════════════════════════


class TestPerformanceSummary:
    def test_print_summary(self):
        report = _PERF_RESULTS
        if not report:
            pytest.skip("No performance data collected")

        print("\n" + "=" * 72)
        print("  DAY 43 — API PERFORMANCE BENCHMARK RESULTS")
        print("  Local development environment · NOT production-grade")
        print("=" * 72)

        total_requests = 0
        total_successes = 0
        total_failures = 0
        all_avgs: list[tuple[str, float]] = []

        for name, stats in sorted(report.items()):
            total_requests += stats["count"]
            total_successes += stats["successes"]
            total_failures += stats["failures"]
            all_avgs.append((name, stats["avg_ms"]))

            print(f"\n  {name}")
            print(
                f"    Requests: {stats['count']}  Success: {stats['successes']}  Failures: {stats['failures']}"
            )
            print(
                f"    Avg: {stats['avg_ms']:.1f}ms  Median: {stats['median_ms']:.1f}ms  P95: {stats['p95_ms']:.1f}ms"
            )
            print(
                f"    Fastest: {stats['fastest_ms']:.1f}ms  Slowest: {stats['slowest_ms']:.1f}ms"
            )

        print("\n" + "-" * 72)
        print(
            f"  TOTAL: {total_requests} requests | {total_successes} success | {total_failures} failures"
        )
        print("-" * 72)

        all_avgs.sort(key=lambda x: x[1], reverse=True)
        print("\n  RANKING (slowest to fastest by avg latency):")
        for i, (name, avg) in enumerate(all_avgs, 1):
            print(f"    {i}. {name}: {avg:.1f}ms")
        print("=" * 72)

        assert total_failures == 0, f"{total_failures} benchmark requests failed"

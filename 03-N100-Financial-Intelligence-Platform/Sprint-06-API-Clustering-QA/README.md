# Sprint 6 — API, Clustering & QA

**N100 Financial Intelligence Platform**
Days 36–45 Deliverable Documentation

---

## 1. Executive Summary

Sprint 6 completes the API, clustering, and quality assurance layer of the N100 Financial Intelligence Platform:

1. **Day 36 (Clustering):** KMeans clustering pipeline grouping 92 Nifty-100 companies into 5 financially meaningful clusters using 5 features (ROE, D/E, Revenue CAGR, FCF CAGR, OPM).
2. **Day 37 (Analytics):** Cluster profiling, 10-KPI correlation heatmap, sector outlier detection (Z-score), and portfolio distribution statistics.
3. **Day 38 (API Scaffold):** FastAPI application with CORS, request logging, read-only SQLite dependency, and health endpoint.
4. **Day 39 (Company Endpoints):** 7 company data endpoints (list, detail, P&L, balance sheet, cashflow, ratios, tearsheet PDF).
5. **Day 40 (Remaining Endpoints):** 10 additional endpoints (screener, sectors, peers, market cap, portfolio, documents).
6. **Day 41 (Data Quality):** ETL completeness, KPI validation, referential integrity, and regression safety tests.
7. **Day 42 (Integration):** Comprehensive API integration tests, HTML test report, and Streamlit API client.
8. **Day 43 (Performance):** Local performance benchmarks, bottleneck analysis, and database index assessment.
9. **Day 44 (Documentation):** Analyst guide, README, code quality (Black/flake8), formatting.
10. **Day 45 (Final Acceptance):** Complete audit, acceptance gate verification, sign-off.

---

## 2. Completed Deliverables

### Source Code
| File | Lines | Description |
|------|-------|-------------|
| `src/analytics/clustering.py` | 655 | KMeans clustering pipeline |
| `src/analytics/day37.py` | 428 | Profiling, correlation, outliers, portfolio stats |
| `src/api/main.py` | ~125 | FastAPI app scaffold |
| `src/api/client.py` | ~191 | httpx-based API client for Streamlit |
| `src/api/routers/health.py` | ~25 | Health endpoint |
| `src/api/routers/companies.py` | ~359 | 7 company endpoints |
| `src/api/routers/screener.py` | ~75 | Screener presets |
| `src/api/routers/sectors.py` | ~83 | Sector listing |
| `src/api/routers/peers.py` | ~174 | Peer comparison |
| `src/api/routers/valuation.py` | ~72 | Market cap data |
| `src/api/routers/portfolio.py` | ~80 | Portfolio stats/clusters |
| `src/api/routers/documents.py` | ~62 | Document access |

### Tests
| File | Tests | Scope |
|------|-------|-------|
| `tests/test_clustering.py` | 44 | KMeans pipeline, determinism, naming |
| `tests/test_cluster_profiling.py` | 15 | Profile schema, membership consistency |
| `tests/test_portfolio_stats.py` | 11 | Distribution statistics, percentile ordering |
| `tests/test_outlier_detection.py` | 13 | Z-score calculation, edge cases |
| `tests/test_data_quality.py` | 53 | ETL, KPI validation, regression safety |
| `tests/api/test_health.py` | 22 | Health endpoint, OpenAPI, router registration |
| `tests/api/test_companies.py` | 50 | All 7 company endpoints |
| `tests/api/test_day40.py` | 44 | Screener, sectors, peers, market cap, portfolio, documents |
| `tests/api/test_day42.py` | 84 | Comprehensive integration (all 18 endpoints) |
| `tests/api/test_day43_performance.py` | 19 | Performance benchmarks |
| **Total** | **355** | |

### Outputs
| File | Description |
|------|-------------|
| `output/cluster_labels.csv` | 92 company cluster assignments (5 clusters) |
| `output/cluster_profile.csv` | 5 cluster profile summaries |
| `output/portfolio_stats.csv` | 10 KPI distribution statistics |
| `output/outlier_report.csv` | 912 sector outlier records |
| `reports/correlation_heatmap.png` | 10-KPI Pearson correlation matrix |
| `reports/elbow_plot.png` | KMeans inertia vs k curve |
| `reports/sprint6_test_report.html` | Generated test report |
| `reports/day43_performance_report.html` | Performance benchmark report |

---

## 3. Test Results

### Regression Suite
```
352 passed, 3 skipped, 0 failed
```

### Test Breakdown by Day
| Day | Tests | Status |
|-----|-------|--------|
| Day 36 (Clustering) | 44 | All pass |
| Day 37 (Analytics) | 39 | All pass |
| Day 38 (API Scaffold) | 22 | All pass |
| Day 39 (Company Endpoints) | 50 | All pass |
| Day 40 (Remaining Endpoints) | 44 | All pass |
| Day 41 (Data Quality) | 53 | 3 skipped (legitimate extreme values) |
| Day 42 (Integration) | 84 | All pass |
| Day 43 (Performance) | 19 | All pass |

---

## 4. API Endpoint Inventory

18 endpoints across 8 routers:

| Router | Endpoints | Prefix |
|--------|-----------|--------|
| health | 1 | `/api/v1` |
| companies | 7 | `/api/v1/companies` |
| screener | 2 | `/api/v1/screener` |
| sectors | 2 | `/api/v1/sectors` |
| peers | 2 | `/api/v1/peers` |
| valuation | 1 | `/api/v1/market-cap` |
| portfolio | 2 | `/api/v1/portfolio` |
| documents | 1 | `/api/v1/documents` |

---

## 5. Clustering Outputs

### Cluster Distribution
| Cluster | Name | Count |
|---------|------|-------|
| 0 | Capital Efficient | 60 |
| 1 | Premium Margin Leaders | 14 |
| 2 | Defense PSU — Extreme ROE Outlier | 2 |
| 3 | Financial Sector — High Leverage Growth | 15 |
| 4 | High FCF Growth Outlier | 1 |

### Key Features Used
- Return on Equity (%)
- Debt-to-Equity Ratio
- 5-Year Revenue CAGR
- 5-Year FCF CAGR
- Operating Profit Margin (%)

---

## 6. Performance Results

Local benchmark (20 requests per endpoint):

| Endpoint | Avg | Median | P95 |
|----------|-----|--------|-----|
| screener | 15.1ms | 14.6ms | 16.6ms |
| market_cap | 7.0ms | 7.0ms | 7.4ms |
| ratios | 5.0ms | 3.4ms | 34.8ms |
| portfolio_clusters | 4.4ms | 4.3ms | 6.0ms |
| peers_compare | 3.0ms | 2.8ms | 5.7ms |
| All others | 2.0–2.9ms | — | — |

**Note:** LOCAL BENCHMARK MEASUREMENTS, not production-grade.

---

## 7. Known Warnings & Exceptions

| Exception | Status |
|-----------|--------|
| JIOFIN no tearsheet | Documented — listed 2023, < 3 years history |
| 4/92 companies with pros/cons | Legitimate — only 4 companies have data |
| 36/92 companies without peer groups | Legitimate — 56 companies have membership |
| 1 company missing from documents | Documented |
| Extreme financial ratios (~10) | Legitimate outliers, not errors |
| 13 database tables | All legitimate and used |

---

## 8. Setup & Run Instructions

### Prerequisites
- Python 3.13+
- Packages: fastapi, uvicorn, httpx, openpyxl, scikit-learn, pandas, pytest

### Start the API
```bash
cd Sprint-06-API-Clustering-QA
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

### Access Swagger UI
```
http://127.0.0.1:8000/docs
```

### Run Tests
```bash
pytest tests/ -v
```

### Generate Reports
```bash
python scripts/generate_report.py        # Test report
python scripts/generate_perf_report.py   # Performance report
```

---

## 9. Cross-Sprint Dependencies

| Dependency | Source | Usage |
|------------|--------|-------|
| SQLite Database | Sprint-01 | 13 tables, 92 companies |
| Screener Excel | Sprint-03 | 6 screener presets |
| Tearsheet PDFs | Sprint-05 | 91 pre-generated PDFs |
| Cashflow Intelligence | Sprint-05 | Clustering feature input |

**Guardrail:** Sprints 1–5 are never modified.

---

## 10. Git Safety

- Only `Sprint-06-API-Clustering-QA/` files are created/modified
- Sprint 1–5 directories remain completely untouched
- No commits made during Sprint 6 development

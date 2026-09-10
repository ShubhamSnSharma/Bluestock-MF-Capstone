# Sprint 6 — Analyst & User Guide

**N100 Financial Intelligence Platform**
API, Clustering & Quality Assurance — Days 36–45

---

## 1. Project Architecture

Sprint 6 builds two major capabilities on top of the N100 Financial Intelligence Platform:

1. **KMeans Clustering Pipeline** — Groups 92 Nifty-100 companies into 5 financially meaningful clusters using 5 key features.
2. **REST API Layer** — FastAPI-based read-only API serving company data, screener results, peer comparisons, portfolio analytics, and document access.

### Directory Structure

```
Sprint-06-API-Clustering-QA/
├── src/
│   ├── analytics/
│   │   ├── clustering.py        # Day 36 — KMeans clustering pipeline
│   │   └── day37.py             # Day 37 — Profiling, correlation, outliers, portfolio stats
│   └── api/
│       ├── main.py              # Day 38 — FastAPI app, CORS, logging, DB dependency
│       ├── client.py            # Day 42 — httpx-based API client for Streamlit
│       └── routers/
│           ├── health.py        # /api/v1/health
│           ├── companies.py     # /api/v1/companies/* (7 endpoints)
│           ├── screener.py      # /api/v1/screener/*
│           ├── sectors.py       # /api/v1/sectors/*
│           ├── peers.py         # /api/v1/peers/*
│           ├── valuation.py     # /api/v1/market-cap
│           ├── portfolio.py     # /api/v1/portfolio/*
│           └── documents.py     # /api/v1/documents/*
├── tests/
│   ├── test_clustering.py       # 44 clustering tests
│   ├── test_cluster_profiling.py # 15 profiling tests
│   ├── test_portfolio_stats.py  # 11 portfolio stats tests
│   ├── test_outlier_detection.py # 13 outlier tests
│   ├── test_data_quality.py     # 53 data quality tests
│   └── api/
│       ├── test_health.py       # 22 health/scaffold tests
│       ├── test_companies.py    # 50 company endpoint tests
│       ├── test_day40.py        # 44 remaining endpoint tests
│       ├── test_day42.py        # 84 comprehensive integration tests
│       └── test_day43_performance.py # 19 performance benchmark tests
├── output/
│   ├── cluster_labels.csv       # 92 company cluster assignments
│   ├── cluster_profile.csv      # 5 cluster profile summaries
│   ├── portfolio_stats.csv      # 10 KPI portfolio statistics
│   └── outlier_report.csv       # 912 sector outlier records
├── reports/
│   ├── correlation_heatmap.png  # 10-KPI Pearson correlation matrix
│   ├── elbow_plot.png           # KMeans inertia vs k curve
│   ├── sprint6_test_report.html # Generated test report
│   └── day43_performance_report.html # Performance benchmark report
└── scripts/
    ├── generate_report.py       # HTML test report generator
    └── generate_perf_report.py  # HTML performance report generator
```

---

## 2. Data Sources

### Primary Database
- **File:** `Sprint-01-Data-Foundation/nifty100.db` (SQLite, 1.97 MB)
- **Access:** Read-only mode (`file:?mode=ro`)
- **13 Tables:**

| Table | Rows | Description |
|-------|------|-------------|
| `companies` | 92 | Company master data (name, logo, ROE, ROCE, etc.) |
| `sectors` | 92 | Sector classifications, market cap categories |
| `financial_ratios` | 1,164 | Yearly KPI ratios (12+ years × 92 companies) |
| `profitandloss` | 1,164 | Annual P&L statements |
| `balancesheet` | 1,058 | Annual balance sheets |
| `cashflow` | 1,063 | Annual cash flow statements |
| `market_cap` | 552 | Market cap and valuation metrics |
| `peer_groups` | 56 | Peer group membership |
| `peer_percentiles` | 560 | Percentile-ranked peer comparisons |
| `documents` | 1,456 | Annual report links |
| `analysis` | 16 | Screener/computed analysis |
| `prosandcons` | 14 | Pros/cons text (4 companies only) |
| `stock_prices` | 5,520 | Historical stock prices |

### Secondary Data Sources
- **Sprint-03:** `output/screener_output.xlsx` — 6 screener presets (Quality Compounder, Value Pick, Growth Accelerator, Dividend Champion, Debt-Free Blue Chip, Turnaround Watch)
- **Sprint-05:** `reports/tearsheets/` — 91 pre-generated PDF tearsheets
- **Sprint-05:** `output/cashflow_intelligence.xlsx` — Cash flow intelligence metrics (used by clustering)

---

## 3. Clustering Methodology

### Features Used (5)
1. `return_on_equity_pct` — Return on equity percentage
2. `debt_to_equity` — Debt-to-equity ratio
3. `revenue_cagr_5yr` — 5-year revenue CAGR
4. `fcf_cagr_5yr` — 5-year free cash flow CAGR
5. `operating_profit_margin_pct` — Operating profit margin

### Pipeline
1. **Data Loading:** Financial ratios (year=2024) + sector data from SQLite + cashflow intelligence from Excel
2. **Imputation:** Sector-median imputation for missing values (logged in-memory for validation)
3. **Scaling:** StandardScaler (zero mean, unit variance)
4. **Optimal k:** Elbow method (k=2..10), k=5 selected near elbow
5. **Clustering:** KMeans(n_clusters=5, random_state=42, n_init=10, max_iter=300)
6. **Naming:** Profile-based cluster naming using median feature values

### Cluster Archetypes (5)

| Cluster | Name | Count | Key Characteristics |
|---------|------|-------|---------------------|
| 0 | Capital Efficient | 60 | Low D/E, moderate ROE, stable margins |
| 1 | Premium Margin Leaders | 14 | High OPM, strong ROE, moderate growth |
| 2 | Defense PSU — Extreme ROE Outlier | 2 | Extreme ROE (>500%), defense PSU |
| 3 | Financial Sector — High Leverage Growth | 15 | High D/E (leverage), strong growth, financial sector dominated |
| 4 | High FCF Growth Outlier | 1 | Exceptional FCF growth, high ROE |

### Determinism
- `random_state=42` ensures reproducibility
- Verified: repeated runs produce identical cluster assignments
- Cluster assignments are stable across runs

---

## 4. API Architecture

### FastAPI Application
- **Title:** N100 Financial Intelligence Platform
- **Version:** 0.1.0
- **Base URL:** `http://127.0.0.1:8000`
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **OpenAPI JSON:** `http://127.0.0.1:8000/openapi.json`

### Middleware
- **CORS:** Allow all origins (development mode)
- **Request Logging:** Logs method, path, status code, and response time for every request

### Database Dependency
- Read-only SQLite connection per request
- Connection closed after request completes
- `sqlite3.Row` factory for dict-like access

---

## 5. API Endpoints (18 Total)

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Service status, uptime, version, DB row counts |

### Companies (7 endpoints)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/companies/` | List all 92 companies (filters: sector, market_cap_category, search) |
| GET | `/api/v1/companies/{ticker}` | Full company profile with latest ratios |
| GET | `/api/v1/companies/{ticker}/pl` | P&L history (filters: from_year, to_year) |
| GET | `/api/v1/companies/{ticker}/bs` | Balance sheet history (filters: from_year, to_year) |
| GET | `/api/v1/companies/{ticker}/cashflow` | Cashflow history (filters: from_year, to_year) |
| GET | `/api/v1/companies/{ticker}/ratios` | Financial KPI ratios (filter: year) |
| GET | `/api/v1/companies/{ticker}/tearsheet` | Pre-generated tearsheet PDF |

### Screener
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/screener/` | List 6 screener presets with company counts |
| GET | `/api/v1/screener/{preset}` | Companies matching a preset |

### Sectors
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/sectors/` | List 10 broad sectors with company counts |
| GET | `/api/v1/sectors/{sector}/companies` | Companies in a sector (filter: market_cap_category) |

### Peers
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/peers/{ticker}` | Peer group membership |
| GET | `/api/v1/peers/{ticker}/compare` | Percentile-ranked peer comparison (filter: year) |

### Market Cap
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/market-cap/` | Market cap data (filters: year, sector, market_cap_category) |

### Portfolio
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/portfolio/stats` | Portfolio statistics for 10 KPIs |
| GET | `/api/v1/portfolio/clusters` | Cluster assignments for 92 companies |

### Documents
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/documents/{ticker}` | Annual report documents (filter: year) |

---

## 6. Screener Presets

| Preset | Description | Data Source |
|--------|-------------|-------------|
| Quality Compounder | High ROE, consistent growth | Sprint-03 screener_output.xlsx |
| Value Pick | Low PE, high dividend yield | Sprint-03 screener_output.xlsx |
| Growth Accelerator | High revenue CAGR | Sprint-03 screener_output.xlsx |
| Dividend Champion | High dividend payout | Sprint-03 screener_output.xlsx |
| Debt-Free Blue Chip | Zero or low D/E | Sprint-03 screener_output.xlsx |
| Turnaround Watch | Improving financials | Sprint-03 screener_output.xlsx |

---

## 7. Portfolio Statistics

10 key performance indicators with distribution statistics:

| Metric | Description |
|--------|-------------|
| net_profit_margin_pct | Net profit as % of revenue |
| operating_profit_margin_pct | Operating profit as % of revenue |
| return_on_equity_pct | Return on shareholders' equity |
| debt_to_equity | Total debt / shareholders' equity |
| return_on_capital_employed_pct | ROCE percentage |
| asset_turnover | Revenue / total assets |
| revenue_cagr_5yr | 5-year revenue compound annual growth rate |
| fcf_conversion_pct | Free cash flow / operating profit |
| cfo_quality_score | Cash from operations / net profit |
| capex_intensity_pct | Capital expenditure / revenue |

For each metric: P10, P25, P50 (median), P75, P90, Mean, Std, n_valid, n_missing.

---

## 8. How to Start the API

```bash
cd Sprint-06-API-Clustering-QA

# Start the FastAPI server
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload

# Access Swagger UI
open http://127.0.0.1:8000/docs

# Access OpenAPI JSON
curl http://127.0.0.1:8000/openapi.json
```

---

## 9. How to Use the API Client

The API client (`src/api/client.py`) provides typed helper functions for Streamlit integration:

```python
from src.api.client import (
    api_health,
    api_get_companies, api_get_company,
    api_get_pl, api_get_bs, api_get_cashflow, api_get_ratios,
    api_get_tearsheet,
    api_get_screener_presets, api_get_screener_results,
    api_get_sectors, api_get_sector_companies,
    api_get_peers, api_get_peer_compare,
    api_get_market_cap,
    api_get_portfolio_stats, api_get_portfolio_clusters,
    api_get_documents,
)

# Example usage
companies = api_get_companies(sector="Financials")
tcs = api_get_company("TCS")
pl = api_get_pl("TCS", from_year="2020")
tearsheet_pdf = api_get_tearsheet("TCS")  # Returns bytes or None
```

**Requirements:** FastAPI server must be running on `http://127.0.0.1:8000`.

---

## 10. How to Run Tests

```bash
cd Sprint-06-API-Clustering-QA

# Run all tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_clustering.py -v          # Clustering tests
pytest tests/api/test_day42.py -v           # Integration tests
pytest tests/api/test_day43_performance.py -v -s  # Performance benchmarks

# Generate HTML test report
python scripts/generate_report.py
```

---

## 11. Performance Benchmarks

Local benchmark results (20 requests per endpoint, 3 warmup):

| Rank | Endpoint | Avg Latency | Median | P95 |
|------|----------|-------------|--------|-----|
| 1 | screener | 15.1ms | 14.6ms | 16.6ms |
| 2 | market_cap | 7.0ms | 7.0ms | 7.4ms |
| 3 | ratios | 5.0ms | 3.4ms | 34.8ms |
| 4 | portfolio_clusters | 4.4ms | 4.3ms | 6.0ms |
| 5 | peers_compare | 3.0ms | 2.8ms | 5.7ms |
| 6-13 | all others | 2.0–2.9ms | — | — |

**Note:** These are LOCAL BENCHMARK MEASUREMENTS, not production-grade performance claims.

---

## 12. Known Data-Quality Exceptions

| Exception | Count | Explanation |
|-----------|-------|-------------|
| JIOFIN no tearsheet | 1 | Listed in 2023, < 3 years history, legitimately skipped by Sprint-05 |
| Companies with pros/cons | 4/92 | Only 4 companies have pros/cons data in the database |
| Companies without peer groups | 36/92 | 56 companies have peer group membership |
| Missing from documents | 1 | One company has no document records |
| Extreme financial ratios | ~10 | ROE > 500% (BEL, HAL, INDIGO), ROCE > 500% (5 companies), NPM > 200% (BAJAJHLDNG) — legitimate outliers, not data errors |
| Database tables | 13 | All 13 tables are legitimate and used |

---

## 13. Database Indexes

All queries are covered by existing indexes:

| Index | Table | Columns | Purpose |
|-------|-------|---------|---------|
| `idx_pnl_company` | profitandloss | company_id | P&L queries by company |
| `idx_bs_company` | balancesheet | company_id | Balance sheet queries |
| `idx_cf_company` | cashflow | company_id | Cashflow queries |
| `idx_fr_company` | financial_ratios | company_id | Ratio queries |
| `idx_mc_company` | market_cap | company_id | Market cap queries |
| `idx_prices_company_date` | stock_prices | company_id, date | Stock price queries |
| `idx_sectors_broad` | sectors | broad_sector | Sector listing |
| `idx_pp_company` | peer_percentiles | company_id | Peer lookups |
| `idx_pp_group` | peer_percentiles | peer_group_name | Peer compare |

**No new indexes required.** With 92 companies, all queries complete in under 16ms.

---

## 14. Final Acceptance Status — Sprint 6

**Status: CONDITIONAL PASS**

All 20 acceptance gates pass. Three upstream data-coverage exceptions are acknowledged but are **not** Sprint 6 defects — they originate from source data pipelines (Sprint-01, Sprint-05) and do not block API functionality or clustering correctness.

### Upstream Data Exceptions (Not Sprint 6 Defects)

| # | Exception | Impact | Origin |
|---|-----------|--------|--------|
| 1 | JIOFIN tearsheet missing | `/companies/JIOFIN/tearsheet` returns 404 | Sprint-05 — company listed 2023, <3yr history |
| 2 | 4/92 companies have pros/cons | Peer compare pros/cons sparse | Sprint-01 — only 4 companies populated |
| 3 | 36/92 companies lack peer groups | Peer endpoints return 404 for 36 tickers | Sprint-01 — only 56 companies in peer_groups |

### Test Suite Summary

- **Collected:** 355
- **Passed:** 352
- **Skipped:** 3 (data-coverage gaps, upstream)
- **Failed:** 0

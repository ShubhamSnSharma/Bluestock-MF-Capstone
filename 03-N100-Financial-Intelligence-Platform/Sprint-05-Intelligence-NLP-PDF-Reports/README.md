# Sprint 5 — Intelligence, NLP & PDF Reports

**N100 Financial Intelligence Platform**  
Comprehensive Days 29–35 Deliverable Documentation

---

## 1. Executive Summary & Sprint Goal

Sprint 5 completes the end-to-end intelligence and automated reporting tier of the N100 Financial Intelligence Platform:
1. **Day 29 (NLP Parser):** Parses unstructured CAGR and return metrics from text disclosures into structured numeric data with automated cross-validation against ratio engines.
2. **Day 30 (Pros & Cons Signal Engine):** Evaluates 24 investment rules (12 PRO + 12 CON) across the 92-company universe with deterministic confidence scoring (60–99%).
3. **Day 31 (Cash Flow Intelligence):** Computes multi-year CFO earnings quality, CapEx intensity, FCF conversion/CAGR, and operational distress alerts.
4. **Day 32 (Capital Allocation Analysis):** Tracks 8-pattern capital allocation profiles, latest-year universe distributions, and year-over-year transitions across consecutive numeric fiscal years.
5. **Day 33–34 (Company Tearsheets):** Generates executive-grade 2-page research tearsheet PDFs for all eligible N100 companies with zero overflow and embedded vector charts.
6. **Day 34 (Sector Intelligence Reports):** Generates dedicated overview PDFs for all 11 standard GICS sectors with benchmark medians and constituent peer comparison tables.
7. **Day 35 (Portfolio Summary PDF):** Produces a consolidated 92-page portfolio document (1 page per company in alphabetical order by ticker) with year-over-year KPI trajectory trend arrows (`↑`, `↓`, `→`).

---

## 2. Architecture & Directory Structure

```
Sprint-05-Intelligence-NLP-PDF-Reports/
├── src/
│   ├── __init__.py
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── cashflow_kpis.py            # Day 31 — Cash Flow Intelligence Engine
│   │   └── capital_allocation.py       # Day 32 — Capital Allocation Distribution & YoY Changes
│   ├── nlp/
│   │   ├── __init__.py
│   │   ├── parser.py                   # Day 29 — NLP Analysis Text Parser
│   │   └── pros_cons_generator.py      # Day 30 — Auto Pros/Cons 24-Rule Signal Engine
│   └── reports/
│       ├── __init__.py
│       ├── tearsheet.py                # Day 33/34 — 2-Page Company Tearsheet PDF Generator
│       ├── sector_report.py            # Day 34 — 11 Sector Overview PDF Generator
│       └── portfolio_report.py         # Day 35 — Consolidated 92-Page Portfolio PDF Generator
├── tests/
│   ├── __init__.py
│   ├── test_nlp_parser.py              # 36 tests (Day 29)
│   ├── test_pros_cons.py               # 39 tests (Day 30)
│   ├── test_cashflow_kpis.py           # 28 tests (Day 31)
│   ├── test_capital_allocation.py      # 14 tests (Day 32)
│   ├── test_tearsheet.py               # 9 tests (Day 33)
│   ├── test_sector_report.py           # 6 tests (Day 34)
│   ├── test_portfolio_report.py        # 5 tests (Day 35)
│   └── test_integration.py             # 25 tests (End-to-End Pipeline Output Validation)
├── output/
│   ├── analysis_parsed.csv             # Day 29 parsed rows (80 rows)
│   ├── parse_failures.csv              # Day 29 parse failures (0 failures)
│   ├── pros_cons_generated.csv         # Day 30 signals (431 rows)
│   ├── coverage_failures.csv           # Day 30 classified coverage exceptions (48 rows)
│   ├── cashflow_intelligence.xlsx      # Day 31 cash flow metrics (92 rows)
│   ├── distress_alerts.csv             # Day 31 distress flags (13 rows)
│   ├── capital_allocation_distribution.csv # Day 32 latest year pattern counts (8 rows)
│   ├── pattern_changes.csv             # Day 32 YoY pattern transitions (468 rows)
│   └── skipped_tearsheets.csv          # Day 34 history skip log (1 row: JIOFIN)
├── reports/
│   ├── tearsheets/                     # 91 individual 2-page company PDFs
│   ├── sector/                         # 11 standard sector overview PDFs
│   └── portfolio/                      # portfolio_summary.pdf (92 pages)
├── Makefile
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 3. Data Sources & Source Integrity

All financial statements, market data, and ratios are ingested strictly as read-only inputs from Sprint 1 and Sprint 2:
- `Sprint-01-Data-Foundation/nifty100.db`: SQLite database containing `companies`, `sectors`, `profitandloss`, `balancesheet`, `cashflow`, `financial_ratios`, `market_cap`.
- `Sprint-01-Data-Foundation/core datasets/analysis.xlsx`: Raw free-text disclosures.
- `Sprint-02-Financial-Ratio-Engine/output/capital_allocation.csv`: 8-pattern historical capital allocation profiles (1,164 rows).

**Strict Guardrail:** Sprints 1–4 are never modified (`git diff HEAD` remains zero).

---

## 4. Component Details & Methodologies

### Day 29 — NLP Analysis Text Parser (`src/nlp/parser.py`)
- **Authoritative Source:** `analysis.xlsx` across 5 core companies (`HDFCBANK`, `INFY`, `SBILIFE`, `TCS`, `WIPRO`).
- **Extraction Rules:**
  - Regex pattern: `r"(\d+)\s*Years?:?\s*([\d.]+)%"` with extensions for TTM, Last Year, and negative percentages.
  - Multi-year CAGR periods (`10`, `5`, `3`) mapped to numeric `period_years`.
  - TTM / Last Year / 1 Year mapped explicitly to `period_years = 0`.
- **Output:** `output/analysis_parsed.csv` (80 rows), `output/parse_failures.csv` (0 rows).

### Day 30 — Pros & Cons 24-Rule Engine (`src/nlp/pros_cons_generator.py`)
- **12 PRO Rules (P01–P12):**
  - `P01`: ROE > 20% sustained for 3+ years
  - `P02`: FCF positive for 5+ consecutive years
  - `P03`: D/E = 0 in latest year
  - `P04`: Revenue CAGR > 15% (5-year)
  - `P05`: OPM > 25% in latest year
  - `P06`: PAT CAGR > 20% (5-year)
  - `P07`: ICR > 10 OR Debt Free
  - `P08`: Dividend Yield > 2% AND FCF positive
  - `P09`: EPS CAGR > 15% (5-year)
  - `P10`: ROE improving for 3 consecutive years
  - `P11`: Revenue CAGR > PAT CAGR (5-year)
  - `P12`: Assets growing AND debt declining (3 years)
- **12 CON Rules (C01–C12):**
  - `C01`: D/E > 2.0 (non-financial companies only)
  - `C02`: FCF negative for 3 consecutive years
  - `C03`: OPM declining for 3 consecutive years
  - `C04`: Net profit negative in latest year
  - `C05`: Revenue declining for 2+ consecutive years
  - `C06`: ICR < 1.5
  - `C07`: Dividend payout > 100%
  - `C08`: D/E rising for 3 consecutive years
  - `C09`: EPS declining for 3 consecutive years
  - `C10`: ROCE < 10%
  - `C11`: Net Debt > 3× EBITDA (where EBITDA = `operating_profit`)
  - `C12`: Revenue CAGR < 5% (5-year)
- **Confidence Scoring:** `conf = 70 + floor(min(|magnitude| / scale, 29))` (range 70–99%). Only signals with confidence > 60% are emitted.
- **Coverage Output:** `output/pros_cons_generated.csv` (431 rows), `output/coverage_failures.csv` (48 rows classified as `A_GENUINE_NO_CON` or `C_MISSING_METRIC`).

### Day 31 — Cash Flow Intelligence Module (`src/analytics/cashflow_kpis.py`)
- **CFO Earnings Quality:** 5-year average of `(CFO / PAT)` excluding `PAT == 0`. Categorized into `High Quality` (> 1.0), `Moderate` (0.5–1.0), and `Accrual Risk` (< 0.5).
- **CapEx Intensity:** `(abs(investing_activity) / sales) * 100`. Categorized into `Asset Light` (< 3%), `Moderate` (3–8%), and `Capital Intensive` (> 8%).
- **Distress & Deleveraging Flags:**
  - `Distress Flag`: `latest CFO < 0 AND latest CFF > 0` (13 companies triggered).
  - `Deleveraging Flag`: `latest CFF < 0 AND borrowings declining YoY` (26 companies triggered).
- **Deliverables:** `output/cashflow_intelligence.xlsx` (92 rows), `output/distress_alerts.csv` (13 rows).

### Day 32 — Capital Allocation Report (`src/analytics/capital_allocation.py`)
- Ingests Sprint 2 `output/capital_allocation.csv` (1,164 rows, 92 companies).
- Filters to numeric fiscal years and selects latest year (2024).
- **Latest Year 2024 Distribution (`output/capital_allocation_distribution.csv`):**
  - `Shareholder Returns`: 44
  - `Mixed`: 13
  - `Growth Funded by Debt`: 12
  - `Reinvestor`: 12
  - `Liquidating Assets`: 7
  - `Other`: 2
  - `Distress Signal`: 1
  - `Pre-Revenue`: 1
  - **Total: 92 Companies**
- **Pattern Transitions (`output/pattern_changes.csv`):** 468 actual year-over-year pattern shifts across consecutive numeric fiscal years.

### Day 33 & 34 — Company Tearsheets (`src/reports/tearsheet.py`)
- **Format:** Strict 2-page executive PDF built with ReportLab and Matplotlib.
- **Page 1 Content:**
  1. Navy header bar (`#0F2942`) with company name, ticker, and sector.
  2. 6 KPI tiles: Revenue, Net Profit, ROE, ROCE, Debt/Equity, OPM.
  3. 10-year Revenue & Net Profit grouped bar chart (₹ Cr).
  4. ROE vs ROCE trend line chart with 15% benchmark line.
- **Page 2 Content:**
  1. Balance sheet capital structure stacked bar chart (Equity, Borrowings, Other Liabilities).
  2. Latest FY Cash Flow waterfall bridge (CFO, CFI, CFF, Net Cash Flow).
  3. Capital Allocation badge bar (Pattern, CFO Quality, CapEx Intensity).
  4. Pros and Cons side-by-side formatted cards with confidence ratings and rule IDs.
- **Batch Generation:** 91 company tearsheets saved to `reports/tearsheets/<ticker>_tearsheet.pdf`.
- **Skip Handling:** `JIOFIN` legitimately skipped (< 3 years history) and documented in `output/skipped_tearsheets.csv`.

### Day 34 — Sector Overview Reports (`src/reports/sector_report.py`)
- Generates 11 standard GICS sector PDFs in `reports/sector/<safe_sector_name>_report.pdf`:
  - `communication_services_report.pdf` (2 companies)
  - `consumer_discretionary_report.pdf` (14 companies)
  - `consumer_staples_report.pdf` (7 companies)
  - `energy_report.pdf` (6 companies)
  - `financials_report.pdf` (23 companies)
  - `healthcare_report.pdf` (6 companies)
  - `industrials_report.pdf` (10 companies)
  - `information_technology_report.pdf` (5 companies)
  - `materials_report.pdf` (9 companies)
  - `real_estate_report.pdf` (2 companies)
  - `utilities_report.pdf` (8 companies)
  - **Total: 92 companies covered (11 sectors)**
- **Contents:** Sector header, 8 median KPI cards, peer comparison table with repeated table headers and word wrapping.

### Day 35 — Portfolio Summary PDF (`src/reports/portfolio_report.py`)
- Produces `reports/portfolio/portfolio_summary.pdf`.
- **Pages:** Exactly 92 pages (1 page per company, sorted alphabetically from `ABB` to `ZYDUSLIFE`).
- **Metrics & Trajectory:** Top 6 financial KPIs with prior year, latest year, YoY growth %, and directional trend arrows:
  - `↑ UP`: Improved by > +2% (or deleveraged for D/E)
  - `↓ DOWN`: Declined by < -2% (or increased leverage for D/E)
  - `→ FLAT`: Maintained within ±2%

---

## 5. Verification & Test Suite

Run all tests via pytest:

```bash
make test
# or
pytest tests/ -v
```

### Complete Test Coverage Breakdown (162/162 Tests Passing)

| Test Module | Tests | Verified Scope |
|---|---|---|
| `tests/test_nlp_parser.py` | 36 | Source file validation, regex parsing, TTM period mapping, schema, cross-validation |
| `tests/test_pros_cons.py` | 39 | 24 investment rules, confidence scoring bounds (60–99), C01 financial exemption, determinism |
| `tests/test_cashflow_kpis.py` | 28 | CFO quality, CapEx intensity, FCF CAGR/conversion, distress/deleveraging flags, 92-row schema |
| `tests/test_capital_allocation.py` | 14 | Source integrity, 92-company distribution, latest year selection, YoY transitions, Excel join |
| `tests/test_tearsheet.py` | 9 | 2-page constraint, file size (> 30KB), chart rendering, metadata, smoke test (TCS, HDFC, RELIANCE, SUNPHARMA, TATASTEEL) |
| `tests/test_sector_report.py` | 6 | Sector discovery (11 sectors), median calculations, 92-company coverage without duplication |
| `tests/test_portfolio_report.py` | 5 | Alphabetical ticker ordering, 92-page PDF integrity, trend arrow computation |
| `tests/test_integration.py` | 25 | End-to-end pipeline output validation: all output CSVs/Excel, 91 tearsheet PDFs, 11 sector PDFs, 92-page portfolio PDF |
| **Total** | **162** | **162 passed in ~40s** |

---

## 6. Makefile Command Reference

```bash
make install         # Install Python dependencies from requirements.txt
make parse           # Run NLP parser → output/analysis_parsed.csv
make pros-cons       # Run pros/cons generator → output/pros_cons_generated.csv
make cashflow        # Run cash flow KPIs → output/cashflow_intelligence.xlsx
make capital-alloc   # Run capital allocation → output/capital_allocation_distribution.csv
make tearsheets      # Generate 2-page tearsheets → reports/tearsheets/
make sector-reports  # Generate sector reports → reports/sector/
make portfolio       # Generate portfolio summary → reports/portfolio/
make reports         # Generate all PDF reports (tearsheets, sector, portfolio)
make test            # Run full test suite (137 tests)
make clean           # Remove generated outputs and test caches
```

---

## 7. Known Data Characteristics & Coverage Summary

1. **JIOFIN Data History:** JIOFIN was listed in 2023 and has only 2 years of financial history in the database. It is legitimately skipped for tearsheets (requiring >= 3 years for multi-year trend charts) and documented in `output/skipped_tearsheets.csv`. It is included in sector tables and portfolio summaries (having 1-year YoY trajectory).
2. **Literal Pro+Con Exit Criterion:** Not literally satisfied. 48 companies legitimately trigger no con rule under the specified thresholds. No artificial signals were generated. This is documented as an analytical exception (91/92 companies have ≥1 PRO; 45/92 companies have ≥1 CON; 48 companies have no CON condition triggered and are classified in `output/coverage_failures.csv`).
3. **C09 Rule Trigger:** C09 (EPS declining 3 consecutive years) triggers 0 times across the 92-company universe because no company experienced continuous 3-year EPS decline in this dataset.

---

## 8. Git Safety & Integrity

- Only `Sprint-05-Intelligence-NLP-PDF-Reports/` files are created/modified.
- Sprint 1, 2, 3, and 4 directories remain completely untouched.
- Clean working directory with no temporary files or caches committed.

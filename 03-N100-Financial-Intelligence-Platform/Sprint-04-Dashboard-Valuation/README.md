# Sprint 4 — Dashboard & Valuation Module

**N100 Financial Intelligence Platform · Sprint 4**
Days 22–28 · 55 Story Points · Epics 05 & 06

---

## Sprint Goal

A fully working **8-screen Streamlit dashboard** running on `localhost:8501`.
All screens load without errors for any of the 92 Nifty 100 company tickers.
The valuation module produces `valuation_summary.xlsx` with FCF yield, P/E flags,
and Caution / Discount / Fair labels for all 92 companies.

---

## Quick Start

```bash
# From the repository root
source .venv/bin/activate

# Start the dashboard
streamlit run 03-N100-Financial-Intelligence-Platform/Sprint-04-Dashboard-Valuation/src/dashboard/app.py

# Or using make
make -C 03-N100-Financial-Intelligence-Platform/Sprint-04-Dashboard-Valuation run
```

The dashboard opens at **http://localhost:8501**

---

## Valuation Engine

```bash
make -C 03-N100-Financial-Intelligence-Platform/Sprint-04-Dashboard-Valuation valuation
```

---

## Unit Tests

```bash
make -C 03-N100-Financial-Intelligence-Platform/Sprint-04-Dashboard-Valuation test
```

---

## Deliverables

| File | Description |
|---|---|
| `src/dashboard/app.py` | Main Streamlit entry point — 8-screen navigation |
| `src/dashboard/utils/db.py` | Shared cached data loader (`@st.cache_data(ttl=600)`) |
| `pages/01_home.py` | Home: 6 KPI tiles, sector donut, Top-5 quality table |
| `pages/02_profile.py` | Company Profile: card, charts, pros/cons, partial-data note |
| `pages/03_screener.py` | Screener: 10 sliders, 6 presets, Financials D/E exempt, Debt-Free ICR |
| `pages/04_peers.py` | Peer Comparison: radar chart + KPI table |
| `pages/05_trends.py` | Trend Analysis: multi-metric 10-year line chart |
| `pages/06_sectors.py` | Sector Analysis: bubble chart + median bar chart |
| `pages/07_capital.py` | Capital Allocation: Sprint-2 treemap + drill-down |
| `pages/08_reports.py` | Annual Reports: BSE PDF links with HTTP 200/404/unverified check |
| `src/analytics/valuation.py` | FCF yield + P/E flag engine |
| `output/valuation_summary.xlsx` | 92-row valuation report |
| `output/valuation_flags.csv` | Caution + Discount companies only |
| `tests/test_valuation.py` | 27 valuation unit tests |
| `tests/test_screener.py` | 34 screener + capital + page-import + strict preset boundary tests |
| `tests/test_performance.py` | 5 profile performance tests (< 3s each) |

**Total: 66 tests, 66 passing**

---

## 8 Screen Descriptions

### 🏠 Home
- **6 KPI tiles**: Average ROE, Median P/E, Median D/E, Total Companies, Median Revenue CAGR 5yr, Debt-Free Company count
- **Sector donut chart**: 11 sectors with company count (Plotly)
- **Top-5 by composite quality score**: sortable table
- **Year selector** (2019–2024): all metrics update on change

### 🏢 Company Profile
- Autocomplete company search dropdown (92 companies)
- Company card: name, sector, sub-sector, NSE/BSE links, about description
- 6 KPI tiles: ROE, ROCE, NPM, D/E, Revenue CAGR 5yr, FCF
- 10-year Revenue & Net Profit grouped bar chart
- ROE / ROCE dual-axis line chart
- Pros & Cons displayed as green ✓ / red ✗ badges
- **Partial-data note**: shown automatically when fewer than 10 years of data are available for a company

### 🔍 Screener
- 10 metric sliders: ROE, D/E, FCF, Rev CAGR, PAT CAGR, OPM, P/E, P/B, Dividend Yield, ICR
- **6 preset buttons**: Quality Compounder, Value Pick, Growth Accelerator, Dividend Champion, Debt-Free Blue Chip, Turnaround Watch
- **Financials D/E exemption**: Financials sector companies are exempt from the D/E filter (per spec)
- **Debt-Free ICR**: Companies with D/E ≤ 0.05 automatically pass all ICR minimums (proxy for Debt Free since icr_label is NULL in FY2024 rows)
- **Turnaround Watch**: Uses Revenue CAGR 3yr (not 5yr), FCF > 0, and D/E declining YoY
- Result count label (e.g. "23 companies match your filters")
- CSV download with **numeric values** preserved (not formatted strings)

### 👥 Peer Comparison
- Peer group dropdown (all 11 groups: Automobiles, FMCG, IT, Pharma, etc.)
- Radar chart: selected company vs peer group average (8 metrics, normalised to [0,1])
- Side-by-side KPI table with benchmark row highlighted

### 📈 Trend Analysis
- Company search + multi-metric selector (up to 3 metrics overlaid)
- Available-years note when < 10 years of data exist
- Multiple Y-axes when > 1 metric selected
- Raw data expander for CSV-style view

### 🏭 Sector Analysis
- Sector dropdown (All Sectors or individual)
- **Bubble chart**: X = Revenue, Y = ROE, bubble size = Market Cap, colour = sub-sector
- Sector median KPI bar chart (horizontal, colour-graded)

### 💰 Capital Allocation Map
- **Uses actual Sprint-2 capital allocation patterns** from:
  `Sprint-02-Financial-Ratio-Engine/output/capital_allocation.csv`
- Pattern labels (FY2024 distribution):
  - Shareholder Returns: 44 companies
  - Mixed: 13 companies
  - Reinvestor: 12 companies
  - Growth Funded by Debt: 12 companies
  - Liquidating Assets: 7 companies
  - Other: 2 companies
  - Distress Signal: 1 company
  - Pre-Revenue: 1 company
- Treemap tile size = Composite Quality Score
- Pattern definitions with colour legend
- Drill-down: select a pattern → see all member companies with KPIs
- Summary table in expander

> **Note**: The old implementation incorrectly derived patterns from CFO Quality × CapEx Intensity (producing a 3×3 grid). This has been corrected to use Sprint-2's canonical `pattern_label`.

### 📄 Annual Reports
- Company search box
- Year-by-year report cards with BSE India PDF links
- **Real HTTP status check** (HEAD request, 4-second timeout):
  - HTTP 200 → clickable ✓ Available badge
  - HTTP 404 → 🚫 Report unavailable
  - Timeout / network error / other → ⚠️ Unable to verify (try link shown)
- Verification results cached in session_state (no repeated requests on rerun)
- Summary footer: total / available / unavailable / unable-to-verify counts

---

## Valuation Module

| Metric | Formula |
|---|---|
| **FCF Yield %** | `(FCF / Market Cap) × 100` |
| **Sector Median P/E** | Median P/E across all companies in `broad_sector` for FY2024 |
| **PE vs Sector Median %** | `((P/E − sector_median) / sector_median) × 100` |
| **Caution** | `P/E > sector_median × 1.5` |
| **Discount** | `P/E < sector_median × 0.7` |
| **Fair** | Otherwise |

### FY2024 Results (92 companies)

| Flag | Count |
|---|---|
| Fair | 48 |
| Discount | 30 |
| Caution | 14 |

---

## Tests (66 total · 0 failures)

| File | Tests | Coverage |
|---|---|---|
| `test_valuation.py` | 27 | Schema, FCF yield formula, PE flags, output files |
| `test_screener.py` | 34 | Financials D/E exemption, Debt-Free ICR, Turnaround 3yr, CSV, capital patterns, 8-page syntax smoke, strict preset boundaries |
| `test_performance.py` | 5 | Profile load < 3s for ADANIPORTS, TCS, HDFCBANK, RELIANCE, SUNPHARMA |

### Cross-sprint test chain (all pass)

```
Sprint 1: 78 passed
Sprint 2: 42 passed
Sprint 3: 17 passed
Sprint 4: 66 passed
Total across Sprints 1–4: 203 passed
```

---

## Known Source-Data Limitations

| Limitation | Impact | Verdict |
|---|---|---|
| Value Pick preset returns 2 companies | Spec says 5–50 | Source-data limitation — thresholds unchanged |
| `icr_label` is NULL for all FY2024 rows | Debt-Free ICR uses D/E ≤ 0.05 proxy | Transparent in UI and documented in screener sidebar |
| `prosandcons` covers only 14 of 92 companies | Others show "No pros/cons data" | Source-data limitation |
| Annual report HTTP check may return "Unable to verify" on network errors | BSE PDFs rate-limit HEAD requests | Try link still shown for manual access |

---

## Database Integration

Sprint 4 reads **read-only** from the shared Sprint 1 database:

```
Sprint-01-Data-Foundation/nifty100.db
```

**Tables used**: `companies`, `sectors`, `financial_ratios`, `market_cap`,
`profitandloss`, `balancesheet`, `cashflow`, `peer_groups`, `peer_percentiles`,
`prosandcons`, `documents`, `stock_prices`

**External CSV**: `Sprint-02-Financial-Ratio-Engine/output/capital_allocation.csv`
(for Capital Allocation Map patterns)

No schema changes were made to the shared database in Sprint 4.

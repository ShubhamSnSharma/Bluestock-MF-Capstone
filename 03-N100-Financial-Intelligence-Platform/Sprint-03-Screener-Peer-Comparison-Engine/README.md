# Sprint 3: Screener & Peer Comparison Engine

**Epic 03 & 04**: Financial Screener + Peer Comparison Engine (Days 15–21 | 49 Story Points)
**Location**: `03-N100-Financial-Intelligence-Platform/Sprint-03-Screener-Peer-Comparison-Engine/`
**Shared Database**: `03-N100-Financial-Intelligence-Platform/Sprint-01-Data-Foundation/nifty100.db`

---

## 1. Overview & Objectives

Sprint 3 implements an institutional-grade **Financial Screener** and **Peer Comparison Engine** for all 92 constituents of the Nifty 100 universe:
1. **Financial Screener**: Customizable filtering across 15 financial, valuation, and growth metrics with 6 analyst presets and sector-aware leverage handling.
2. **Composite Quality Score (0–100)**: Multi-factor scoring engine using P10/P90 winsorisation and sector-relative normalisation.
3. **Peer Comparison Engine**: Intra-group percentile rankings across 10 financial metrics for 11 distinct peer groups (with inverse D/E ranking).
4. **Visual & Excel Reporting**: Automated production of 6-sheet screener workbooks, 11-sheet peer comparison workbooks with conditional formatting, and 92 company radar charts.

---

## 2. Directory Structure

```text
03-N100-Financial-Intelligence-Platform/
├── Sprint-01-Data-Foundation/
│   └── nifty100.db                             # Shared verified SQLite database
├── Sprint-02-Financial-Ratio-Engine/           # Ratio & CAGR engine
└── Sprint-03-Screener-Peer-Comparison-Engine/
    ├── Makefile                                # Execution and validation targets
    ├── README.md                               # Architectural and user guide
    ├── config/
    │   └── screener_config.yaml                # Analyst-editable preset & weight config
    ├── notebooks/
    │   └── screener_validation.sql             # 12 verification SQL queries
    ├── output/
    │   ├── screener_output.xlsx                # 6 sheets, colour-coded screener results
    │   └── peer_comparison.xlsx                # 11 sheets, percentile colour-coded comparison
    ├── reports/
    │   └── radar_charts/                       # 92 company radar charts (.png)
    ├── src/
    │   ├── __init__.py
    │   ├── screener/
    │   │   ├── __init__.py
    │   │   ├── engine.py                       # Filter engine & composite score
    │   │   └── validate.py                     # SQL validation runner
    │   └── analytics/
    │       ├── __init__.py
    │       └── peer.py                         # Peer percentiles & radar chart generator
    └── tests/
        ├── __init__.py
        └── screener/
            ├── __init__.py
            ├── test_screener.py                # Screener & preset unit tests
            └── test_peer.py                    # Peer ranking & chart unit tests
```

---

## 3. Financial Screener Architecture

### Supported Filterable Metrics (15 Metrics)
1. `roe_min`: Minimum Return on Equity (%)
2. `de_max`: Maximum Debt-to-Equity ratio (*Automatically bypassed for Financials sector*)
3. `fcf_min`: Minimum Free Cash Flow (₹ Cr)
4. `revenue_cagr_5yr_min`: Minimum 5-Year Revenue CAGR (%)
5. `pat_cagr_5yr_min`: Minimum 5-Year PAT CAGR (%)
6. `opm_min`: Minimum Operating Profit Margin (%)
7. `pe_max`: Maximum Price-to-Earnings multiple
8. `pb_max`: Maximum Price-to-Book multiple
9. `dividend_yield_min`: Minimum Dividend Yield (%)
10. `icr_min`: Minimum Interest Coverage Ratio (*Debt-free companies treated as infinite ICR*)
11. `market_cap_min`: Minimum Market Capitalization (₹ Cr)
12. `net_profit_min`: Minimum Net Profit (₹ Cr)
13. `eps_cagr_5yr_min`: Minimum 5-Year EPS CAGR (%)
14. `asset_turnover_min`: Minimum Asset Turnover ratio
15. `sales_min`: Minimum Sales / Revenue (₹ Cr)

### 6 Preset Screeners & Results

| Preset Name | Criteria / Thresholds | Results (FY24 Universe) | Spec Target (5–50) | Implementation Status |
|---|---|---|---|---|
| **Quality Compounder** | ROE > 15%, D/E < 1.0 (or Financials), FCF > 0, Rev CAGR 5Y > 10% | **23 companies** | MET | PASS |
| **Value Pick** | P/E < 20, P/B < 3.0, D/E < 2.0 (or Financials), Div Yield > 1% | **2 companies** | **NOT MET** (Source Limitation) | **PASS** |
| **Growth Accelerator** | PAT CAGR 5Y > 20%, Rev CAGR 5Y > 15%, D/E < 2.0 (or Financials) | **19 companies** | MET | PASS |
| **Dividend Champion** | Div Yield > 2%, Div Payout < 80%, FCF > 0 | **30 companies** | MET | PASS |
| **Debt-Free Blue Chip** | D/E ≤ 0.05 (or Debt Free), ROE > 12%, Sales > ₹5,000 Cr | **16 companies** | MET | PASS |
| **Turnaround Watch** | Rev CAGR 3Y > 10%, FCF > 0 in FY24, D/E 2024 < D/E 2023 | **33 companies** | MET | PASS |

> **Value Pick Audit Note**:
> - **Implementation Status**: **PASS** (Filter algorithm mathematically faithful to specification).
> - **Required 5–50 Result-Count Criterion**: **NOT MET** (Actual result: 2 companies — `M&M` and `MOTHERSON`).
> - **Reason**: Supplied FY2024 source-data limitation. The Nifty 100 universe exhibits elevated valuation multiples (mean P/B: 7.49x, median P/B: 7.54x). Only 10 companies have P/B < 3.0, of which only 2 also meet P/E < 20 and Dividend Yield > 1%.
> - **Data Integrity Principle**: Specified thresholds were kept strictly unchanged, and no data was manipulated to artificially force count expansion.

---

## 4. Composite Scoring Methodology

The **Composite Quality Score** (0–100 scale) aggregates multi-dimensional fundamental performance:
- **35% Profitability**: ROE (15%), ROCE (10%), Net Profit Margin (10%)
- **30% Cash Quality**: FCF Growth/CAGR (15%), CFO/PAT Ratio (10%), Positive FCF Flag (5%)
- **20% Growth**: 5-Year Revenue CAGR (10%), 5-Year PAT CAGR (10%)
- **15% Leverage**: D/E Score (10%, inverted so lower is better), ICR Score (5%)

### P10 / P90 Winsorisation
To prevent extreme outliers from distorting linear scaling, each metric is winsorised at the 10th ($P_{10}$) and 90th ($P_{90}$) percentiles before normalization:
$$\text{Scaled Value} = \frac{\text{Clipped}(X, P_{10}, P_{90}) - P_{10}}{P_{90} - P_{10}} \times 100$$

### Sector-Relative Normalisation
In addition to the global score, a **Sector-Relative Score** is computed by running the winsorisation and weighted aggregation within each constituent's respective `broad_sector` peer universe.

---

## 5. Peer Percentile Ranking & Comparison

### 11 Peer Groups (56 Constituent Companies)
1. `Private Banks` (5 peers, Benchmark: `HDFCBANK`)
2. `Public Sector Banks` (4 peers, Benchmark: `SBIN`)
3. `IT Services` (5 peers, Benchmark: `TCS`)
4. `Pharmaceuticals` (5 peers, Benchmark: `SUNPHARMA`)
5. `Automobiles` (7 peers, Benchmark: `TATAMOTORS`)
6. `Life Insurance` (4 peers, Benchmark: `LICI`)
7. `Oil & Gas` (5 peers, Benchmark: `RELIANCE`)
8. `Power & Utilities` (7 peers, Benchmark: `NTPC`)
9. `Steel` (4 peers, Benchmark: `TATASTEEL`)
10. `FMCG` (7 peers, Benchmark: `ITC`)
11. `Consumer Finance` (3 peers, Benchmark: `BAJFINANCE`)

### Database Table: `peer_percentiles`
Created and populated in `nifty100.db` with 560 records (56 companies × 10 ranking metrics):
- Foreign key linked to `companies(id)` with `ON DELETE CASCADE`.
- Inverted percentile rank for D/E ($100 - \text{Rank}$).

---

## 6. Verification & Test Execution

Run the complete test and validation suite using the Makefile:

```bash
# 1. Run all screener and peer generation workflows
make -C 03-N100-Financial-Intelligence-Platform/Sprint-03-Screener-Peer-Comparison-Engine reports

# 2. Run SQL validation queries
make -C 03-N100-Financial-Intelligence-Platform/Sprint-03-Screener-Peer-Comparison-Engine validate

# 3. Run unit test suite
make -C 03-N100-Financial-Intelligence-Platform/Sprint-03-Screener-Peer-Comparison-Engine test
```

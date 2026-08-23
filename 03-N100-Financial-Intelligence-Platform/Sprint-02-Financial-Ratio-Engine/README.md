# Sprint 2 — Financial Ratio Engine

**Epic 02**: Financial Ratio Engine (Days 08–14 | 42 Story Points)
**Location**: `03-N100-Financial-Intelligence-Platform/Sprint-02-Financial-Ratio-Engine/`
**Database**: `03-N100-Financial-Intelligence-Platform/Sprint-01-Data-Foundation/nifty100.db`

---

## 1. Executive Summary & Objectives

The primary objective of Sprint 2 is to construct a **Financial Ratio Engine** that calculates 50+ Key Performance Indicators (KPIs) for all 92 Nifty 100 constituent companies across all historical reporting periods (2011–2024 and TTM).

The engine consumes the clean, relational SQLite database established in Sprint 1 (`nifty100.db`) without modifying the underlying raw Excel datasets or Sprint 1 ETL foundation. It extends the `financial_ratios` table to **1,164 company-year rows** with computed profitability, leverage, efficiency, growth CAGR, cash flow, and composite quality score metrics.

---

## 2. Architecture & File Structure

```text
03-N100-Financial-Intelligence-Platform/Sprint-02-Financial-Ratio-Engine/
├── Makefile                          # Automation targets (compute, test, report, clean)
├── README.md                         # Comprehensive architecture and formula documentation
├── src/
│   ├── __init__.py
│   └── analytics/
│       ├── __init__.py
│       ├── ratios.py                 # Profitability, Leverage, and Efficiency Ratio calculations
│       ├── cagr.py                   # Multi-year CAGR Engine with 6 edge-case handlers
│       ├── cashflow_kpis.py          # FCF, CFO Quality, CapEx intensity, Capital Allocation
│       └── engine.py                 # Ratio orchestration and SQLite database updater
├── tests/
│   ├── __init__.py
│   └── kpi/
│       ├── __init__.py
│       ├── test_ratios.py            # 20 ratio unit tests
│       ├── test_cagr.py              # 11 CAGR engine & edge-case unit tests
│       └── test_cashflow_kpis.py     # 11 cash flow & capital allocation unit tests
├── output/
│   ├── capital_allocation.csv        # 8-pattern classification per company-year (1,164 rows)
│   └── ratio_edge_cases.log          # Documented anomaly log for OPM, ROCE, and ROE checks
└── notebooks/
    └── ratio_validation.sql          # 10 SQL verification queries against nifty100.db
```

---

## 3. KPI Formulas & Technical Specifications

### A. Profitability Ratios (`src/analytics/ratios.py`)
1. **Net Profit Margin (NPM %)**:
   $$\text{NPM} = \frac{\text{Net Profit}}{\text{Sales}} \times 100$$
   *Returns `None` if $\text{Sales} \le 0$.*
2. **Operating Profit Margin (OPM %)**:
   $$\text{OPM} = \frac{\text{Operating Profit}}{\text{Sales}} \times 100$$
   *Cross-checked against reported `opm_percentage`; logged to `ratio_edge_cases.log` if absolute difference $> 1.0\%$.*
3. **Return on Equity (ROE %)**:
   $$\text{ROE} = \frac{\text{Net Profit}}{\text{Equity Capital} + \text{Reserves}} \times 100$$
   *Returns `None` if Net Worth ($\text{Equity Capital} + \text{Reserves}$) $\le 0$.*
4. **Return on Capital Employed (ROCE %)**:
   $$\text{ROCE} = \frac{\text{EBIT}}{\text{Equity Capital} + \text{Reserves} + \text{Borrowings}} \times 100$$
   *Where $\text{EBIT} = \text{Operating Profit} + \text{Other Income}$. Returns `None` if Capital Employed $\le 0$.*
5. **Return on Assets (ROA %)**:
   $$\text{ROA} = \frac{\text{Net Profit}}{\text{Total Assets}} \times 100$$
   *Returns `None` if $\text{Total Assets} \le 0$.*

### B. Leverage & Efficiency Ratios (`src/analytics/ratios.py`)
1. **Debt-to-Equity (D/E)**:
   $$\text{D/E} = \frac{\text{Borrowings}}{\text{Equity Capital} + \text{Reserves}}$$
   *Returns `0.0` if $\text{Borrowings} = 0$.*
2. **Financial Sector Carve-Out & High Leverage Flag**:
   - For all 23 companies classified under `sectors.broad_sector == 'Financials'`, the standard high leverage warning is suppressed due to structural balance sheet characteristics.
   - For non-financial companies: `high_leverage_flag = True` if $\text{D/E} > 5.0$.
3. **Interest Coverage Ratio (ICR)**:
   $$\text{ICR} = \frac{\text{Operating Profit} + \text{Other Income}}{\text{Interest}}$$
   - If $\text{Interest} = 0$: returns `None` with `icr_label = "Debt Free"`.
   - If $\text{ICR} < 1.5$: `icr_warning_flag = True`.
4. **Net Debt**:
   $$\text{Net Debt} = \text{Borrowings} - \text{Investments}$$
   *(Uses financial investments as the liquid asset proxy).*
5. **Asset Turnover**:
   $$\text{Asset Turnover} = \frac{\text{Sales}}{\text{Total Assets}}$$

### C. Multi-Year CAGR Engine (`src/analytics/cagr.py`)
Formula for $n$-year window:
$$\text{CAGR} = \left( \left(\frac{\text{Value}_t}{\text{Value}_{t-n}}\right)^{\frac{1}{n}} - 1 \right) \times 100$$

Computed for **3-year, 5-year, and 10-year** windows across:
- **Revenue CAGR** (`revenue_cagr_3yr`, `revenue_cagr_5yr`, `revenue_cagr_10yr`)
- **PAT CAGR** (`pat_cagr_3yr`, `pat_cagr_5yr`, `pat_cagr_10yr`)
- **EPS CAGR** (`eps_cagr_3yr`, `eps_cagr_5yr`, `eps_cagr_10yr`)

#### Six Mandatory CAGR Edge Case Handlers:
| Edge Case Condition | Return Value | Assigned Flag |
|---|---|---|
| **1. Positive $\to$ Positive** | Calculated Float | `None` (Normal) |
| **2. Positive $\to$ Negative** | `None` | `DECLINE_TO_LOSS` |
| **3. Negative $\to$ Positive** | `None` | `TURNAROUND` |
| **4. Negative $\to$ Negative** | `None` | `BOTH_NEGATIVE` |
| **5. Zero Base ($\text{Start} = 0$)** | `None` | `ZERO_BASE` |
| **6. Missing History / Gap ($< n$ yrs)** | `None` | `INSUFFICIENT` |

### D. Cash Flow KPIs & Capital Allocation (`src/analytics/cashflow_kpis.py`)
1. **Free Cash Flow (FCF in ₹ Cr)**:
   $$\text{FCF} = \text{CFO} + \text{CFI}$$
2. **CFO Quality Score**:
   $$\text{CFO Quality Score} = \text{5-Year Average of } \left(\frac{\text{CFO}}{\text{PAT}}\right)$$
   - `> 1.0`: `High Quality`
   - `0.5 – 1.0`: `Moderate`
   - `< 0.5`: `Accrual Risk`
   *(Periods where $\text{PAT} = 0$ are excluded from the average).*
3. **CapEx Intensity (%)**:
   $$\text{CapEx Intensity} = \frac{|\text{CFI}|}{\text{Sales}} \times 100$$
   - `< 3%`: `Asset Light`
   - `3% – 8%`: `Moderate`
   - `> 8%`: `Capital Intensive`
4. **FCF Conversion Rate (%)**:
   $$\text{FCF Conversion} = \frac{\text{FCF}}{\text{Operating Profit}} \times 100$$
5. **Capital Allocation 8-Pattern Classifier**:
   Based on the signs $(S_{\text{CFO}}, S_{\text{CFI}}, S_{\text{CFF}})$:
   - **`(+,-,-)` with 5-yr avg $\text{CFO/PAT} > 1.0$**: **Shareholder Returns** (Precedence rule)
   - **`(+,-,-)` otherwise**: **Reinvestor**
   - **`(+,-,+)`**: **Mixed**
   - **`(-,-,+)`**: **Growth Funded by Debt**
   - **`(+,-,-)`**: **Reinvestor**
   - **`(+,-,+)`**: **Mixed**
   - **`(+,-,+)`**: **Liquidating Assets**
   - **`(-,+,+)`**: **Distress Signal**
   - **`(+,-,-)`**: **Pre-Revenue**
   - **`(+,-,+)`**: **Cash Accumulator**
   - All 1,164 records exported to `output/capital_allocation.csv`.

### E. Composite Quality Score
Deterministic percentile ranking across four equal dimensions (25% each):
$$\text{Quality Score} = 0.25 \times P_{\text{ROE}} + 0.25 \times P_{\text{Inv D/E}} + 0.25 \times P_{\text{CFO Quality}} + 0.25 \times P_{\text{5Y Rev CAGR}}$$
- Scaled from $0$ to $100$.
- Missing sub-components default to median percentile (50.0).

---

## 4. Manual Spot-Check Validation (< 0.1% Tolerance)

Spot checks conducted for three major constituents across diverse sectors:

| Company Ticker | Metric | Source Recomputed | Database Value | Difference (%) | Result |
|---|---|---|---|---|---|
| **ABB** | **ROE (FY24)** | $32.4682\%$ | $32.4682\%$ | $0.000000\%$ | **PASS** |
| **ABB** | **5Y Rev CAGR** | $9.7161\%$ | $9.7161\%$ | $0.000000\%$ | **PASS** |
| **HDFCBANK** | **ROE (FY24)** | $14.3397\%$ | $14.3397\%$ | $0.000000\%$ | **PASS** |
| **HDFCBANK** | **5Y Rev CAGR** | $21.9510\%$ | $21.9510\%$ | $0.000000\%$ | **PASS** |
| **RELIANCE** | **ROE (FY24)** | $9.9587\%$ | $9.9587\%$ | $0.000000\%$ | **PASS** |
| **RELIANCE** | **5Y Rev CAGR** | $9.6061\%$ | $9.6061\%$ | $0.000000\%$ | **PASS** |

---

## 5. Verification & Test Suite Summary

- **Total Test Cases**: **42 Unit Tests** across `test_ratios.py`, `test_cagr.py`, and `test_cashflow_kpis.py`.
- **Pass Rate**: **100% (42 passed, 0 failed, 0 skipped)**.
- **Database Row Count**: `SELECT COUNT(*) FROM financial_ratios` = **1,164** (Requirement $\ge 1,100$).
- **Foreign Key Check**: `PRAGMA foreign_key_check` = **0 errors**.
- **Screener Preview (ROE > 15% & D/E < 1.0)**: **38 companies returned** (Expected range: 15–50).

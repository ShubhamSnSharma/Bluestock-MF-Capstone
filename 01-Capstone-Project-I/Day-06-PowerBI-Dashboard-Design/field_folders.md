# Power BI Measure Display Folders Specification

To ensure a clean, intuitive, and production-ready authoring environment in Power BI Desktop, all DAX measures must reside inside a single dedicated table (`_Measures`) organized into standardized **Display Folders**.

---

## Folder Structure Overview

```text
_Measures/
├── 01 Executive KPIs/
├── 02 Performance Metrics/
├── 03 Risk Analytics/
├── 04 Investor Behavior/
└── 05 Benchmark Comparison/
```

---

## Detailed Measure Display Folder Mapping

### `01 Executive KPIs`
High-level summary metrics intended for C-suite executive cards, key headers, and macro performance scorecards.

| Measure Name | Display Folder | Description / Primary Usage |
| :--- | :--- | :--- |
| `Total AUM` | `01 Executive KPIs` | Total AUM in Crores INR across schemes. |
| `Total Schemes` | `01 Executive KPIs` | Distinct count of active mutual fund schemes. |
| `Total Investors` | `01 Executive KPIs` | Total unique investor count across transactions. |
| `Total Investment` | `01 Executive KPIs` | Total capital committed (SIP + Lumpsum). |
| `Total SIP` | `01 Executive KPIs` | Total capital committed specifically via SIP payments. |
| `Average NAV` | `01 Executive KPIs` | Arithmetic average unit pricing across schemes. |

---

### `02 Performance Metrics`
Return and risk-adjusted efficiency metrics evaluating scheme performance over 1Y, 3Y, and historical horizons.

| Measure Name | Display Folder | Description / Primary Usage |
| :--- | :--- | :--- |
| `CAGR` | `02 Performance Metrics` | 3-Year Compound Annual Growth Rate (%). |
| `Sharpe` | `02 Performance Metrics` | Annualized Sharpe Ratio ($R_f = 6.5\%$). |
| `Sortino` | `02 Performance Metrics` | Downside risk-adjusted Sortino Ratio. |
| `Alpha` | `02 Performance Metrics` | Excess benchmark return percentage generated. |
| `Beta` | `02 Performance Metrics` | Systematic market risk volatility factor. |
| `Max Drawdown` | `02 Performance Metrics` | Maximum historical peak-to-trough drop (%). |

---

### `03 Risk Analytics`
Quantitative tail-risk, market concentration, and downside vulnerability metrics for risk officer reviews.

| Measure Name | Display Folder | Description / Primary Usage |
| :--- | :--- | :--- |
| `VaR 95` | `03 Risk Analytics` | 95% Historical Value at Risk (5th percentile daily loss). |
| `CVaR 95` | `03 Risk Analytics` | 95% Conditional Value at Risk (Expected Shortfall). |
| `HHI` | `03 Risk Analytics` | Herfindahl-Hirschman Index for AMC market concentration. |

---

### `04 Investor Behavior`
Customer retention, onboarding cohort lifetime value, and SIP continuity churn risk indicators.

| Measure Name | Display Folder | Description / Primary Usage |
| :--- | :--- | :--- |
| `At Risk Investors` | `04 Investor Behavior` | Count of investors with SIP gaps > 35 days. |
| `At Risk Rate` | `04 Investor Behavior` | Percentage of total SIP investors flagged as At-Risk. |

---

### `05 Benchmark Comparison`
Relative benchmark index performance and tracking variance metrics.

| Measure Name | Display Folder | Description / Primary Usage |
| :--- | :--- | :--- |
| `Tracking Error` | `05 Benchmark Comparison` | Annualized active return volatility vs benchmark. |
| `Expense Ratio` | `05 Benchmark Comparison` | Average annual expense ratio percentage. |

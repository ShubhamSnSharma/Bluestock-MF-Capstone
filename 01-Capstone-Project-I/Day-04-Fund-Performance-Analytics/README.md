# Bluestock Mutual Fund Capstone
## Day 04: Fund Performance Analytics

This project implements quantitative fund performance analytics, risk-adjusted metrics, Jensen's Alpha & Beta estimation, maximum drawdown analysis, benchmark comparison, and multi-factor fund scoring for the Bluestock Mutual Fund dataset.

---

## Objectives

- Calculate daily return distributions and historical CAGR (1Y, 3Y, and ~4.4Y Available History).
- Compute risk-adjusted metrics (Sharpe Ratio, Sortino Ratio using $R_f = 6.5\%$).
- Estimate Jensen's Alpha and Beta via OLS linear regression (`scipy.stats.linregress`) against NIFTY 100.
- Perform Maximum Drawdown stress testing with Peak, Trough, and Recovery date tracking.
- Formulate a 5-factor weighted composite Fund Scorecard (0–100).
- Compare Top 5 schemes against NIFTY 50 and NIFTY 100 indices with Tracking Error analysis.

---

## Project Workflow

```text
Processed CSV Datasets
          │
          ▼
`performance_metrics.py` (9 Financial Formula Functions)
          │
          ▼
`Performance_Analytics.ipynb` (Top-to-Bottom Executed Notebook)
          │
          ├── Daily Return Analysis (Histograms, Boxplots)
          ├── CAGR Analysis (1Y, 3Y, ~4.4Y Available)
          ├── Risk-Adjusted Ratios (Sharpe, Sortino)
          ├── Regression Analytics (Alpha, Beta vs NIFTY 100)
          ├── Stress Testing (Maximum Drawdown & Recovery)
          ├── Multi-Factor Fund Scorecard (0–100)
          └── Benchmark Outperformance & Tracking Error
          │
          ▼
Outputs, PNG Visualizations, & Phase Reports
```

---

## Project Structure

```text
Day-04-Fund-Performance-Analytics/
├── data/
│   ├── raw/
│   ├── processed/
│   └── bluestock_mf.db
├── notebooks/
│   └── Performance_Analytics.ipynb
├── charts/
│   ├── png/          # 12 static PNG visualizations (300 DPI)
│   └── html/
├── reports/          # Phase validation reports & final checklist
├── scripts/
│   ├── performance_metrics.py    # Reusable financial functions
│   └── run_final_verification.py # Automated test & verification suite
├── outputs/          # 8 CSV analytics & scorecard datasets
├── README.md
└── requirements.txt
```

---

## Metrics & Outputs Overview

| Category | Output File | Description |
| :--- | :--- | :--- |
| **Time Series** | `outputs/daily_returns.csv` | Daily percentage return matrix (1150 days x 40 schemes) |
| **Growth Rates** | `outputs/cagr_comparison.csv` | 1Y, 3Y, and ~4.4Y Available History CAGR |
| **Risk-Adjusted** | `outputs/sharpe_ratio.csv` & `sortino_ratio.csv` | Sharpe & Sortino ratios with $R_f = 6.5\%$ |
| **Regression** | `outputs/alpha_beta.csv` | OLS Jensen's Alpha & Beta against NIFTY 100 |
| **Stress Testing** | `outputs/drawdown_summary.csv` | Maximum Drawdown, Peak, Trough, & Recovery dates |
| **Canonical Risk** | `outputs/risk_metrics.csv` | Unified Sharpe, Sortino, Alpha, Beta, & MDD table |
| **Fund Scorecard** | `outputs/fund_scorecard.csv` | 5-factor composite score (0–100), ranks, & tracking error |

---

## How to Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run automated verification suite:
   ```bash
   python scripts/run_final_verification.py
   ```

---

## Deliverables

- `Performance_Analytics.ipynb` (Executed notebook)
- `performance_metrics.py` (Reusable financial calculation module)
- 8 CSV output datasets (`outputs/`)
- 12 publication-quality PNG charts (`charts/png/`)
- Phase validation reports & `final_validation_checklist.md` (`reports/`)

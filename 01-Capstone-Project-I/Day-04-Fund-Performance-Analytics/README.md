# Bluestock Mutual Fund Capstone
## Day 04: Fund Performance Analytics

This project implements quantitative fund performance analytics, risk-adjusted metrics, Jensen's Alpha & Beta estimation, maximum drawdown analysis, benchmark comparison, and multi-factor fund scoring for the Bluestock Mutual Fund dataset.

---

## Objectives

- Calculate daily return distributions and historical CAGR over available investment horizons.
- Compute risk-adjusted metrics (Sharpe Ratio, Sortino Ratio using $R_f = 6.5\%$).
- Estimate Jensen's Alpha and Beta via OLS linear regression (`scipy.stats.linregress`) against NIFTY 100.
- Perform Maximum Drawdown analysis with Peak, Trough, and Recovery date tracking.
- Formulate a 5-factor weighted composite Fund Scorecard (0–100).
- Compare Top 5 schemes against NIFTY 50 and NIFTY 100 indices with Tracking Error analysis.

> **Note:** The NAV dataset spans approximately 4.4 years (Jan 2022 – May 2026). Therefore, the longest CAGR reported is calculated over the available history rather than a full five-year period.

---

## Project Workflow

```text
Processed NAV & Benchmark Data
          │
          ▼
Financial Metrics Module
          │
          ▼
Performance Analytics Notebook
          │
          ▼
CSV Outputs • Charts • Reports
```

---

## Technologies Used

- Python
- Pandas
- NumPy
- SciPy (`scipy.stats.linregress`)
- Matplotlib
- Seaborn
- Plotly
- Jupyter Notebook
- Git & GitHub

---

## Key Results

- Computed daily returns for 40 mutual fund schemes over 1,150 historical trading days.
- Evaluated CAGR, Sharpe Ratio, Sortino Ratio, Jensen's Alpha, Beta, and Maximum Drawdown metrics.
- Built a 5-factor weighted composite fund scorecard (0–100) combining growth and risk factors.
- Compared top-performing schemes against NIFTY 50 and NIFTY 100 benchmarks with tracking error analysis.
- Exported 8 analytical datasets, 12 publication-quality PNG visualizations, and phase validation reports.

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
| **Growth Rates** | `outputs/cagr_comparison.csv` | 1Y, 3Y, and Available History CAGR |
| **Risk-Adjusted** | `outputs/sharpe_ratio.csv` & `sortino_ratio.csv` | Sharpe & Sortino ratios with $R_f = 6.5\%$ |
| **Regression** | `outputs/alpha_beta.csv` | OLS Jensen's Alpha & Beta against NIFTY 100 |
| **Drawdowns** | `outputs/drawdown_summary.csv` | Maximum Drawdown, Peak, Trough, & Recovery dates |
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

- `Performance_Analytics.ipynb` (Fully executed analysis notebook)
- `performance_metrics.py` (Reusable financial calculation module)
- 8 CSV output datasets (`outputs/`)
- 12 publication-quality PNG charts (`charts/png/`)
- Phase validation reports & `final_validation_checklist.md` (`reports/`)

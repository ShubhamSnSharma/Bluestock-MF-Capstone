# Bluestock Mutual Fund Capstone
## Day 05: Advanced Risk & Investor Analytics

This directory contains the Day 05 extension of the Bluestock Mutual Fund Analytics Capstone. It implements advanced quantitative risk modeling (Historical Value at Risk, Conditional Value at Risk), 90-day rolling Sharpe ratios, Herfindahl-Hirschman Index (HHI) concentration analysis, investor onboarding cohort analysis, SIP continuity & at-risk investor identification, and automated risk-profile scheme recommendations.

---

## Deliverables & Organization

```text
Day-05-Advanced-Risk-Analytics/
├── charts/
│   ├── png/
│   │   ├── rolling_sharpe_chart.png
│   │   └── sip_gap_distribution.png
│   └── html/
├── data/
│   ├── raw/
│   ├── processed/          # 10 Cleaned CSV datasets
│   └── bluestock_mf.db     # SQLite database
├── notebooks/
│   └── Advanced_Analytics.ipynb
├── outputs/
│   └── var_cvar_report.csv # 40 schemes VaR & CVaR report
├── reports/
│   └── day5_validation.md
├── scripts/
│   ├── advanced_metrics.py    # Historical VaR, CVaR, Rolling Sharpe, HHI engine
│   ├── cohort_analysis.py     # Investor cohort LTV & retention analytics
│   ├── sip_analysis.py        # SIP gap computation & at-risk investor engine
│   ├── recommender.py         # Risk-profile fund recommendation engine
│   ├── insight_engine.py      # Automated 5 advanced insight generator
│   ├── performance_metrics.py # Shared core financial formulas
│   ├── create_day5_notebook.py
│   └── run_final_verification.py
├── README.md
└── requirements.txt
```

---

## Reusable Modules

| Module | Description |
| :--- | :--- |
| `scripts/advanced_metrics.py` | Production risk engine for 95% Historical VaR, CVaR (Expected Shortfall), 90-day Rolling Sharpe ratio, and Herfindahl-Hirschman Index (HHI). |
| `scripts/cohort_analysis.py` | Investor cohort classification, lifetime value (LTV) summary, and cohort fund preference tracking. |
| `scripts/sip_analysis.py` | SIP contribution gap calculation, at-risk investor detection (>35-day threshold), and gap distribution plotting. |
| `scripts/recommender.py` | Quantitative scheme recommendation engine supporting Conservative, Moderate, and Aggressive investor risk profiles. |
| `scripts/insight_engine.py` | Automated quantitative business insight generator producing structured observations, business implications, and recommendations. |

---

## Key Executive Summary Metrics

- **Schemes Evaluated**: 40 Mutual Fund Schemes
- **Mean 95% Historical VaR**: -1.47% daily loss threshold
- **Mean 95% CVaR (Expected Shortfall)**: -1.86% worst 5% tail-risk loss
- **Market Concentration HHI Score**: 0.1300 (Unconcentrated AMC Market)
- **Total Tracked Investors**: 4,762 Investors
- **At-Risk SIP Investors**: 3,906 Investors (82.0% exhibit gaps > 35 days)

---

## Verification & Execution

To run the automated end-to-end verification suite:

```bash
python3 scripts/run_final_verification.py
```

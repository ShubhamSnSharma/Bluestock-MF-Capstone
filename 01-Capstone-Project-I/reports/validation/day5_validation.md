# Day 05 Advanced Risk Analytics Validation Report

**Date**: 2026-08-12  
**Module**: Day 05 - Advanced Risk Analytics  
**Status**: PASSED  

---

## 1. Executive Summary

- **Total Schemes Evaluated**: 40
- **Mean 95% Historical VaR**: -1.4711%
- **Mean 95% CVaR (Expected Shortfall)**: -1.8580%
- **Market Concentration HHI Score**: 0.1300 (Unconcentrated Market)
- **Total Investors Tracked**: 4,762
- **At-Risk Investors (>35 Day Gap)**: 4,694 (98.6%)

---

## 2. Validation Checklist

- [x] Historical VaR (95%) and CVaR (95%) calculated for all 40 schemes.
- [x] 90-Day Rolling Sharpe ratio calculated and plotted (`charts/png/rolling_sharpe_chart.png`).
- [x] Herfindahl-Hirschman Index (HHI) concentration calculated across AMC AUM.
- [x] Investor Cohort analysis executed (`cohort_summary`, `top_funds_by_cohort`).
- [x] SIP Continuity gaps & at-risk status flagged (`charts/png/sip_gap_distribution.png`).
- [x] Simple risk-based recommender executed for Conservative, Moderate, and Aggressive profiles.
- [x] 5 structured quantitative business insights generated.

---

## 3. Generated Deliverables

- `outputs/var_cvar_report.csv` (40 rows x 18 cols)
- `charts/png/rolling_sharpe_chart.png`
- `charts/png/sip_gap_distribution.png`
- `scripts/advanced_metrics.py`
- `scripts/cohort_analysis.py`
- `scripts/sip_analysis.py`
- `scripts/recommender.py`
- `scripts/insight_engine.py`
- `reports/day5_validation.md`

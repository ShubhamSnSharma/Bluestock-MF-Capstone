# Bluestock Mutual Fund Capstone
## Day 06: Power BI Dashboard Design Specification

This directory contains the Day 06 Power BI Dashboard Specification and Implementation Blueprint for the Bluestock Mutual Fund Analytics Capstone.

---

## Deliverables

- `dashboard_specification.md`: Enterprise-grade Power BI implementation blueprint detailing data model architecture, Star Schema relationships, DAX measure calculations, 4 dashboard page specifications, theme design system, and VertiPaq performance optimization guidelines.

---

## Key Highlights of Specification

1. **Semantic Data Model**:
   - 11 pre-processed datasets mapped into Star Schema architecture.
   - Explicit DAX date table (`Dim_Calendar`).
   - $1 : N$ single-direction relationship filter propagation.

2. **DAX Calculation Engine**:
   - 20+ syntactically validated DAX measures covering AUM, CAGR, Sharpe, Sortino, Alpha, Beta, Max Drawdown, Historical VaR (95%), CVaR (95%), Tracking Error, HHI Index, and At-Risk Investor Continuity metrics.

3. **4-Page Dashboard Layout**:
   - **Page 1**: Executive Overview & AUM Analytics
   - **Page 2**: Scheme Performance & Risk-Adjusted Returns
   - **Page 3**: Advanced Risk Analytics & Tail-Risk (VaR / CVaR)
   - **Page 4**: Investor Behavior, Cohort LTV & SIP Continuity

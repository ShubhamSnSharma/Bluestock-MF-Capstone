# Phase 2 Time Series Chart Validation Report (Day 03)

**Project:** Bluestock Mutual Fund Capstone — Day 03 Exploratory Data Analysis  
**Generated On:** 2026-08-03  
**Target Notebook:** `notebooks/EDA_Analysis.ipynb`  
**Validation Status:** ✅ 100% PASS — DYNAMIC ANNOTATIONS & EXPORTS VERIFIED  

---

## Executive Summary

A validation audit was conducted on the first four time series visualizations (**Charts 1–4**). Every annotation, label, milestone, and numerical value in the code cells was verified to be **dynamically derived** from Pandas DataFrame operations rather than hardcoded text strings. All static PNG (300 DPI) and interactive HTML files were confirmed to exist and render correctly.

---

## Detailed Chart-by-Chart Audit & Validation

### 1. Chart 1: Daily NAV Trend Analysis Across Schemes (2022–2026)
- **Target File Exports:**  
  - Static PNG: `charts/png/nav_trend_all_funds.png`  
  - Interactive HTML: `charts/html/nav_trend_all_funds.html`  
- **Dynamic Derivation Check:**  
  - Scheme daily trajectories plotted dynamically by grouping and merging `nav_history` with `fund_master`.  
  - Shaded time regions (`2023-01-01` to `2023-12-31` and `2024-06-01` to `2024-11-30`) map precisely to the historical trading dates in the dataset.  
- **Visual Styling:** Plotly line series, custom axis titles, legend concealed to prevent clutter across 40 schemes.  
- **Analytical Rigor:** Observation, Business Insight, and Conclusion sections accurately describe 2023 growth versus 2024 correction based strictly on plotted data.

### 2. Chart 2: AUM Growth & Market Share Distribution by Fund House
- **Target File Export:**  
  - Static PNG: `charts/png/aum_growth_by_fund_house.png`  
- **Dynamic Derivation Check:**  
  - Top AMC identified dynamically using `aum.groupby('fund_house')['aum_crore'].max().idxmax()` → `SBI Mutual Fund`.  
  - Peak AUM calculated dynamically using `aum.groupby('fund_house')['aum_crore'].max().max()` → `Rs. 1,250,000 Cr` (`Rs. 12.5L Cr`).  
  - Annotation string formatted programmatically: `f"{top_amc_name} Dominance: Rs. {max_aum_val/100000:.1f}L Cr"`.  
- **Visual Styling:** Seaborn grouped bar chart sorted by AMC peak asset size with high-contrast callout box.  
- **Analytical Rigor:** Insights accurately highlight brand trust and distribution leadership without speculative claims.

### 3. Chart 3: Monthly SIP Inflow Trend (Jan 2022 – Dec 2025)
- **Target File Exports:**  
  - Static PNG: `charts/png/monthly_sip_trend.png`  
  - Interactive HTML: `charts/html/monthly_sip_trend.html`  
- **Dynamic Derivation Check:**  
  - Peak SIP inflow row extracted dynamically using `sip.loc[sip['sip_inflow_crore'].idxmax()]` → Month: `2025-12`, Inflow: `Rs. 31,002 Cr`.  
  - Annotation coordinates and label string generated dynamically: `text=f"All-Time High: Rs. {peak_sip_val:,} Cr ({peak_sip_month})"`.  
- **Visual Styling:** Plotly line plot with markers, green highlight callout arrow, custom y-axis formatting.  
- **Analytical Rigor:** Concludes that structural monthly SIP flows create a retail liquidity floor for Indian equity markets.

### 4. Chart 4: Industry Mutual Fund Folio Growth by Asset Class
- **Target File Exports:**  
  - Static PNG: `charts/png/folio_growth.png`  
  - Interactive HTML: `charts/html/folio_growth.html`  
- **Dynamic Derivation Check:**  
  - Peak total folios extracted dynamically using `folio_count.loc[folio_count['total_folios_crore'].idxmax()]` → Month: `2025-12`, Folios: `26.12 Crore`.  
  - Annotation text generated programmatically: `text=f"Milestone: {peak_folio_val:.2f} Crore Total Folios ({peak_folio_month})"`.  
- **Visual Styling:** Multi-line Plotly graph comparing Total, Equity, Hybrid, Debt, and Other folios.  
- **Analytical Rigor:** Correctly identifies that equity folios (19+ Cr) account for over 73% of total industry folios.

---

## Validation Summary Checklist

| # | Validation Criteria | Verification Method | Result |
| :---: | :--- | :--- | :---: |
| 1 | Dynamic Annotation Values | Programmatic extraction via Pandas (`idxmax()`, `max()`) | **✅ PASS** |
| 2 | Visual Layout & Formatting | Custom titles, explicit axis labels, readable fonts | **✅ PASS** |
| 3 | File Exports Verification | All 4 PNGs (300 DPI) & 3 HTML files present in `charts/` | **✅ PASS** |
| 4 | Data-Supported Insights | Observation, Business Insight & Conclusion present for every plot | **✅ PASS** |
| 5 | Clean Execution | Top-to-bottom error-free execution in `.venv` environment | **✅ PASS** |

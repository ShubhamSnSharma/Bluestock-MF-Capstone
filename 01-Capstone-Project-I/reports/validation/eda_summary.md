# Exploratory Data Analysis (EDA) Executive Summary (Day 03)

**Project:** Bluestock Mutual Fund Capstone — Day 03 Exploratory Data Analysis  
**Generated On:** 2026-08-03  
**Target Notebook:** `notebooks/EDA_Analysis.ipynb`  
**Total Visualizations Created:** 16 High-Resolution Charts (PNG + Interactive HTML)  

---

## 1. Objectives Achieved

1. **Comprehensive Exploratory Data Analysis**: Analyzed 10 mutual fund datasets encompassing historical NAV prices, AMC AUM growth, SIP inflows, folio registrations, retail transactions, portfolio sector weights, and benchmark market indices.
2. **Standardized Visualization Theme**: Designed and integrated central design system themes in `scripts/eda_utils.py` to enforce uniform color palettes, typography (`Arial, sans-serif`), grid lines, and 300 DPI image resolution.
3. **Dynamic Data-Driven Annotations**: Extracted all chart callouts, peak milestones, and AMC market share dominance programmatically using Pandas DataFrame queries rather than hardcoded text strings.
4. **Structured Analytical Rigor**: Accompanied every visualization with concise, factual **Observation**, **Business Insight**, and **Conclusion** sections.
5. **Interactive & Static Asset Exports**: Exported 16 high-resolution PNG charts (`charts/png/`) and 7 interactive Plotly HTML charts (`charts/html/`).

---

## 2. Inventory of Visualizations

| Chart # | Title / Business Subject | Plot Type | Source Dataset | PNG Export | HTML Export |
| :---: | :--- | :---: | :--- | :---: | :---: |
| **1** | Daily NAV Trend Analysis Across Schemes (2022–2026) | Plotly Line | `02_nav_history_cleaned.csv` | ✅ | ✅ |
| **2** | Quarterly AUM Growth & Distribution by Fund House | Seaborn Bar | `03_aum_by_fund_house_cleaned.csv` | ✅ | N/A |
| **3** | Monthly Industry SIP Inflow Trend (Jan 2022 – Dec 2025) | Plotly Line | `04_monthly_sip_inflows_cleaned.csv` | ✅ | ✅ |
| **4** | Industry Mutual Fund Folio Growth by Asset Class | Plotly Multi-Line | `06_industry_folio_count_cleaned.csv` | ✅ | ✅ |
| **5** | Monthly Net Capital Inflow Heatmap by Asset Category | Seaborn Heatmap | `05_category_inflows_cleaned.csv` | ✅ | N/A |
| **6** | Retail Investor Age Group Distribution | Seaborn Bar | `08_investor_transactions_cleaned.csv` | ✅ | N/A |
| **7** | Investment Amount Distribution Across Age Groups | Seaborn Boxplot | `08_investor_transactions_cleaned.csv` | ✅ | N/A |
| **8** | Investor Gender Split & Payment Channel Preference | Pie & Bar | `08_investor_transactions_cleaned.csv` | ✅ | N/A |
| **9** | Total Investment Capital Flow by State (Rs. Crore) | Plotly Bar | `08_investor_transactions_cleaned.csv` | ✅ | ✅ |
| **10** | Retail Transaction Distribution: Metro (T30) vs B30 | Plotly Pie | `08_investor_transactions_cleaned.csv` | ✅ | ✅ |
| **11** | Scheme Returns & Risk Metrics Correlation Matrix | Seaborn Heatmap | `07_scheme_performance_cleaned.csv` | ✅ | N/A |
| **12** | Portfolio Sector Weight Distribution Across Holdings | Plotly Bar | `09_portfolio_holdings_cleaned.csv` | ✅ | ✅ |
| **13** | Top Stock Holdings by Total Market Value (Rs. Crore) | Seaborn Bar | `09_portfolio_holdings_cleaned.csv` | ✅ | N/A |
| **14** | Top 10 Schemes by 5-Year Annualized Return (%) | Seaborn Bar | `07_scheme_performance_cleaned.csv` | ✅ | N/A |
| **15** | Total Expense Ratio (TER %) Distribution Across Schemes | Seaborn Hist/KDE | `07_scheme_performance_cleaned.csv` | ✅ | N/A |
| **16** | Benchmark Indices Historical Closing Value Performance | Plotly Line | `10_benchmark_indices_cleaned.csv` | ✅ | ✅ |

---

## 3. Key Analytical Findings & Business Recommendations

1. **SIP Resilience & Structural Liquidity**: Monthly SIP inflows reached an all-time high of **Rs. 31,002 Crore** in December 2025, providing a permanent structural liquidity floor for Indian equity markets.
2. **Equity Dominance in Household Savings**: Industry folios expanded to **26.12 Crore**, with Equity folios accounting for over 73% (19+ Cr) of total accounts.
3. **AMC Concentration**: Top 3 AMCs (SBI, ICICI Prudential, HDFC) control over 50% of sampled industry AUM, with SBI leading at **Rs. 12.5 Lakh Crore**.
4. **Demographic & Geographic Expansion**: Millennials (26–35) and Gen-X (36–45) drive 60%+ of transaction volume. Beyond-30 (B30) cities now generate 41.6% of total transactions.
5. **Portfolio Sector Heavyweights**: Financial Services and IT comprise over 45% of total portfolio stock weights, mirroring benchmark NIFTY 50 allocations.

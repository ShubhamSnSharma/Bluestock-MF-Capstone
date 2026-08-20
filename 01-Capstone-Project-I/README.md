# Bluestock Mutual Fund Analytics Platform
## End-to-End Data Engineering, Performance Analytics & Interactive BI Dashboard

[![Python](https://img.shields.io/badge/Python-3.11%2B%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%203-lightgrey.svg)](https://www.sqlite.org/)
[![BI Platform](https://img.shields.io/badge/BI%20Platform-Tableau-E97627.svg)](https://www.tableau.com/)

---

## 1. Project Overview

The **Bluestock Mutual Fund Analytics Platform** is an end-to-end data engineering and financial analytics project developed for Bluestock Fintech. The project processes, cleans, validates, and analyzes Indian mutual fund data across 40 schemes, 10 AMC fund houses, and 5,000 investors over a multi-year timeline (2022–2026).

### Analytical Pipeline Stages
1. **Data Ingestion & Cleaning**: Ingestion of raw datasets, live NAV API connectivity (`mfapi.in`), type coercion, and data cleaning.
2. **Relational Modeling & SQL Storage**: A star-schema database in SQLite with 10 tables, referential integrity checks, and analytical SQL queries.
3. **Exploratory Data Analysis (EDA)**: Statistical profiling, distribution analysis, AUM concentration across fund houses, and demographic transaction patterns.
4. **Fund Performance & Multi-Factor Ranking**: Annualized CAGR (1Y, 3Y, 5Y), Volatility, Sharpe Ratio, Sortino Ratio, Benchmark Alpha/Beta (OLS Regression vs NIFTY 100/50), Max Drawdown, and a weighted multi-factor composite fund scorecard.
5. **Advanced Risk & Behavioral Analytics**: Historical Value at Risk (VaR 95%), Conditional VaR (CVaR 95%), rolling 90-day Sharpe ratios, Herfindahl-Hirschman Index (HHI) for sector concentration, investor cohort analysis, and SIP continuity gap analysis (>35 days at-risk detection).
6. **Executive BI Dashboard**: A 4-page interactive dashboard built in Tableau covering Industry Overview, Fund Performance, Investor Analytics, and SIP & Market Trends.

> **Note on BI Implementation**: While the Day 06 workspace directory is named `Day-06-PowerBI-Dashboard-Design` in accordance with the capstone structure, the final interactive BI dashboard was implemented and delivered using **Tableau** (`.twbx`), located in [`Day-06-PowerBI-Dashboard-Design/tableau/`](Day-06-PowerBI-Dashboard-Design/tableau/).

---

## 2. Project Objectives

- **O1 — Automated Data Pipeline**: Ingest, standardize, and clean multi-source mutual fund datasets with automated validation checks.
- **O2 — Relational Data Modeling**: Design and implement a normalized relational star-schema database in SQLite.
- **O3 — Exploratory Data Analysis**: Analyze industry-scale growth, SIP inflows, AUM distribution across top AMCs, and investor transaction patterns.
- **O4 — Quantitative Risk & Return Analytics**: Implement quantitative financial algorithms for risk-adjusted returns (Sharpe, Sortino), market sensitivity (Alpha, Beta), tail risk (VaR, CVaR), and multi-factor ranking.
- **O5 — Executive Dashboard Design**: Develop a 4-page interactive BI dashboard in Tableau with dynamic filtering, normalized benchmark comparison, and dual-axis time series.
- **O6 — Investor Retention & Behavior Modeling**: Track investor onboarding cohorts, transaction frequency, and detect at-risk investors with SIP gaps exceeding 35 days.
- **O7 — Comprehensive Documentation & Reproducibility**: Deliver reproducible scripts, verified Jupyter Notebooks, analytical markdown reports, and executive PDF exports.

---

## 3. Dataset Inventory

The project utilizes 10 core datasets covering fund master metadata, daily NAVs, AUM, SIP trends, folios, transactions, holdings, and benchmark indices:

| # | Dataset File | Rows | Description | Key Fields |
|---|---|---|---|---|
| **01** | `01_fund_master_cleaned.csv` | 40 | Scheme metadata & classification | `amfi_code`, `fund_house`, `scheme_name`, `category`, `plan`, `expense_ratio`, `risk_grade` |
| **02** | `02_nav_history_cleaned.csv` | 46,000 | Daily NAV history (Jan 2022 – May 2026) | `amfi_code`, `date`, `nav` |
| **03** | `03_aum_by_fund_house_cleaned.csv` | 90 | Quarterly AUM for Top 10 AMCs | `date`, `fund_house`, `aum_lakh_crore`, `aum_crore`, `num_schemes` |
| **04** | `04_monthly_sip_inflows_cleaned.csv` | 48 | Monthly industry SIP inflow & accounts (2022–2025) | `month`, `sip_inflow_crore`, `active_sip_accounts_crore`, `new_sip_accounts_lakh`, `yoy_growth_pct` |
| **05** | `05_category_inflows_cleaned.csv` | 144 | Monthly category net inflows for FY25 | `month`, `category`, `net_inflow_crore` |
| **06** | `06_industry_folio_count_cleaned.csv` | 21 | Industry folio milestones & breakdown | `month`, `total_folios_crore`, `equity_folios_crore`, `debt_folios_crore` |
| **07** | `07_scheme_performance_cleaned.csv` | 40 | Pre-computed & validated performance metrics | `amfi_code`, `return_1yr`, `return_3yr`, `return_5yr`, `std_dev`, `sharpe_ratio`, `alpha`, `beta`, `max_drawdown` |
| **08** | `08_investor_transactions_cleaned.csv` | 32,778 | Investor transaction ledger (5,000 investors) | `investor_id`, `transaction_date`, `amfi_code`, `transaction_type`, `amount_inr`, `city`, `state`, `age_group`, `city_tier` |
| **09** | `09_portfolio_holdings_cleaned.csv` | 322 | Underlying stock holdings & sector weights | `amfi_code`, `stock_symbol`, `stock_name`, `sector`, `holding_pct` |
| **10** | `10_benchmark_indices_cleaned.csv` | 8,050 | Daily closing values for NIFTY 50, NIFTY 100, etc. | `date`, `index_name`, `close_value` |

---

## 4. Tools & Technologies Used

- **Programming & Scripting**: Python 3.11+ / 3.13 (Pandas, NumPy, SciPy, Statsmodels, Matplotlib, Seaborn)
- **Database & Query Engine**: SQLite 3, SQL (DDL, DML, Window Functions, Aggregate Joins)
- **Interactive Analytics**: Jupyter Notebooks (`.ipynb`)
- **Business Intelligence & Dashboarding**: Tableau Desktop / Tableau Public (`.twbx`, `.twb`, Hyper API extracts)
- **Version Control & Repository Management**: Git, GitHub

---

## 5. Repository Structure

```text
01-Capstone-Project-I/
├── README.md                                   # Root project documentation
├── run_pipeline.py                             # Master pipeline orchestration script
├── .gitignore                                  # Git exclusion rules
│
├── Day-01-Project-Setup-ETL/                   # Day 01: Ingestion & Live API
│   ├── README.md                               # Stage documentation
│   ├── requirements.txt                        # Python dependencies
│   ├── data_ingestion.py                       # Ingestion & raw profiling script
│   ├── live_nav_fetch.py                       # Live NAV API connector (mfapi.in)
│   └── data/
│       ├── raw/                                # 10 raw source CSVs
│       └── api/                                # Live API cached responses
│
├── Day-02-Data-Cleaning-SQL/                   # Day 02: Data Cleaning & SQL Database
│   ├── README.md                               # Stage documentation
│   ├── requirements.txt                        # Dependencies
│   ├── database/
│   │   └── bluestock_mf.db                     # SQLite relational database (10 tables)
│   ├── sql/
│   │   ├── schema.sql                          # DDL table creation scripts
│   │   └── queries.sql                         # Analytical SQL queries
│   ├── scripts/
│   │   ├── run_cleaning_pipeline.py            # Master data cleaning execution script
│   │   ├── build_database.py                   # Database builder & table loader
│   │   ├── validate_cleaned_data.py            # Automated data validation script
│   │   └── execute_queries.py                  # Query runner script
│   ├── data/
│   │   ├── raw/                                # Raw source CSVs
│   │   └── processed/                          # 10 cleaned & validated CSVs
│   └── reports/                                # Data dictionary, star schema, validation reports
│
├── Day-03-Exploratory-Data-Analysis/           # Day 03: Exploratory Data Analysis
│   ├── notebooks/
│   │   └── EDA_Analysis.ipynb                  # Comprehensive EDA Jupyter notebook
│   ├── data/processed/                         # Processed data references
│   └── reports/                                # EDA summary & validation checklists
│
├── Day-04-Fund-Performance-Analytics/          # Day 04: Performance & Risk Modeling
│   ├── README.md                               # Stage documentation
│   ├── requirements.txt                        # Dependencies
│   ├── notebooks/
│   │   └── Performance_Analytics.ipynb         # Performance & multi-factor notebook
│   ├── scripts/
│   │   └── performance_metrics.py              # Quantitative metric calculation engine
│   ├── outputs/                                # Exported metric tables (CAGR, Sharpe, Scorecard)
│   ├── charts/png/                             # Exported performance charts
│   └── reports/                                # Validation reports & methodology notes
│
├── Day-05-Advanced-Risk-Analytics/             # Day 05: Tail Risk, Cohorts & Retention
│   ├── README.md                               # Stage documentation
│   ├── requirements.txt                        # Dependencies
│   ├── notebooks/
│   │   └── Advanced_Analytics.ipynb            # VaR/CVaR, cohorts & SIP gap notebook
│   ├── scripts/
│   │   ├── advanced_metrics.py                 # VaR, CVaR, Rolling Sharpe, HHI engine
│   │   ├── cohort_analysis.py                  # Investor cohort analysis script
│   │   ├── sip_analysis.py                     # SIP continuity & at-risk detection script
│   │   └── recommender.py                      # Risk-grade recommendation engine
│   ├── outputs/                                # VaR/CVaR reports
│   └── charts/png/                             # Exported risk charts
│
└── Day-06-PowerBI-Dashboard-Design/            # Day 06: Dashboard Design & Final BI Deliverables
    ├── README.md                               # Day 06 overview
    ├── dashboard_specification.md              # Visual specifications
    ├── dashboard_theme.json                    # Bluestock theme palette
    ├── data_model.md                           # Semantic data model specification
    ├── dax_measures.md                         # Measure dictionary (20 core measures)
    ├── field_folders.md                        # Display folder structure
    └── tableau/                                # Final Tableau Deliverables
        ├── bluestock_mf_dashboard.twbx         # Packaged Tableau workbook (4 pages, embedded Hyper data)
        ├── Dashboard.pdf                       # 4-page exported dashboard PDF
        ├── P1_Industry_Overview.png            # Page 1 high-resolution screenshot
        ├── P2_Fund_Performance.png             # Page 2 high-resolution screenshot
        ├── P3_Investor_Analytics.png           # Page 3 high-resolution screenshot
        └── P4_SIP_Market_Trends.png            # Page 4 high-resolution screenshot
```

---

## 6. Setup & Installation Instructions

### Prerequisites
- **Python**: Version 3.11 or higher
- **Tableau**: Tableau Desktop or Tableau Public (to open `.twbx`)
- **SQLite**: SQLite 3 (or a GUI client like DB Browser for SQLite)

### Environment Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ShubhamSnSharma/Bluestock-MF-Capstone.git
   cd Bluestock-MF-Capstone/01-Capstone-Project-I
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate    # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r Day-02-Data-Cleaning-SQL/requirements.txt
   pip install -r Day-04-Fund-Performance-Analytics/requirements.txt
   pip install -r Day-05-Advanced-Risk-Analytics/requirements.txt
   ```

---

## 7. How to Run the Pipeline & Analytics

### Recommended: Run the Complete Master Pipeline
To execute the entire multi-stage data engineering, cleaning, database generation, and analytical verification pipeline in sequence with a single command:

```bash
python run_pipeline.py
```

`run_pipeline.py` orchestrates the completed project stages sequentially:
1. **Raw Data Ingestion & Profiling** (`Day-01-Project-Setup-ETL`)
2. **Automated Data Cleaning & Validation** (`Day-02-Data-Cleaning-SQL`)
3. **SQLite Database Build & Population** (`Day-02-Data-Cleaning-SQL`)
4. **Analytical SQL Query Execution** (`Day-02-Data-Cleaning-SQL`)
5. **Fund Performance & Scorecard Analytics** (`Day-04-Fund-Performance-Analytics`)
6. **Advanced Risk, VaR/CVaR & Investor Analytics** (`Day-05-Advanced-Risk-Analytics`)

*(Note: `run_pipeline.py` executes the data processing and analytical engines. The interactive Tableau workbook, PDF export, and presentation are standalone final deliverables described in Sections 8 & 9).*

---

### Alternative: Run Individual Stages Manually
Each stage of the analytics pipeline can also be executed independently via its respective Python scripts or explored interactively inside the Jupyter Notebooks.

#### Step 1: Run Data Ingestion & Live NAV Fetching (Day 01)
```bash
python3 Day-01-Project-Setup-ETL/data_ingestion.py
python3 Day-01-Project-Setup-ETL/live_nav_fetch.py
```

#### Step 2: Execute Data Cleaning & Build SQLite Database (Day 02)
```bash
# Run data cleaning and validation
python3 Day-02-Data-Cleaning-SQL/scripts/run_cleaning_pipeline.py

# Build SQLite database and load cleaned tables
python3 Day-02-Data-Cleaning-SQL/scripts/build_database.py

# Execute analytical SQL queries
python3 Day-02-Data-Cleaning-SQL/scripts/execute_queries.py
```

#### Step 3: Run Fund Performance & Multi-Factor Scorecard Engine (Day 04)
```bash
python3 Day-04-Fund-Performance-Analytics/scripts/performance_metrics.py
```
*Or open and run `Day-04-Fund-Performance-Analytics/notebooks/Performance_Analytics.ipynb` in Jupyter.*

#### Step 4: Run Advanced Risk, VaR/CVaR, Cohort & SIP Gap Engine (Day 05)
```bash
python3 Day-05-Advanced-Risk-Analytics/scripts/advanced_metrics.py
python3 Day-05-Advanced-Risk-Analytics/scripts/cohort_analysis.py
python3 Day-05-Advanced-Risk-Analytics/scripts/sip_analysis.py
```
*Or open and run `Day-05-Advanced-Risk-Analytics/notebooks/Advanced_Analytics.ipynb` in Jupyter.*

---

## 8. Tableau Dashboard Deliverables & Usage

The final executive dashboard is built in Tableau and stored in [`Day-06-PowerBI-Dashboard-Design/tableau/`](Day-06-PowerBI-Dashboard-Design/tableau/).

### How to Open the Dashboard
- **Using Tableau Desktop / Tableau Public**:
  Open the packaged workbook:
  [`Day-06-PowerBI-Dashboard-Design/tableau/bluestock_mf_dashboard.twbx`](Day-06-PowerBI-Dashboard-Design/tableau/bluestock_mf_dashboard.twbx)
  *Because it is a packaged `.twbx` workbook, all Hyper data extracts are self-contained—no external database connection or file path configuration is required.*
- **Using PDF Reader**:
  Open the exported multi-page document:
  [`Day-06-PowerBI-Dashboard-Design/tableau/Dashboard.pdf`](Day-06-PowerBI-Dashboard-Design/tableau/Dashboard.pdf)

### Dashboard Pages Breakdown

| Page | Dashboard Name | Key Visuals & Features | Deliverable File |
|---|---|---|---|
| **Page 1** | `P1_Industry_Overview` | • 4 Executive KPI Cards (Top 10 AMC AUM ₹62.74L Cr, Monthly SIP Inflow ₹31,002 Cr, Folios 26.12 Cr, Top 10 Schemes 1,522)<br>• Industry AUM Growth Area Chart (2022–2026)<br>• AMC AUM Horizontal Bar Chart (Top 10 AMCs) | [`P1_Industry_Overview.png`](Day-06-PowerBI-Dashboard-Design/tableau/P1_Industry_Overview.png) |
| **Page 2** | `P2_Fund_Performance` | • Interactive Filter Bar (Fund House, Category, Plan, Scheme Name)<br>• Risk vs Return Scatter Plot (Return 3Y vs Std Dev, bubble size by AUM)<br>• 13-Column Sortable Fund Performance Scorecard<br>• Normalized NAV vs Benchmark Tracking (Base = 100) | [`P2_Fund_Performance.png`](Day-06-PowerBI-Dashboard-Design/tableau/P2_Fund_Performance.png) |
| **Page 3** | `P3_Investor_Analytics` | • State-wise Transaction Amount Bar Chart (Descending by state volume)<br>• Transaction Type Split (Lumpsum 58.5%, Redemption 35.3%, SIP 6.2%)<br>• Age Group vs Average SIP Amount Column Chart<br>• Monthly Transaction Volume Trend | [`P3_Investor_Analytics.png`](Day-06-PowerBI-Dashboard-Design/tableau/P3_Investor_Analytics.png) |
| **Page 4** | `P4_SIP_Market_Trends` | • SIP YoY Growth KPI Badge (`17.17%` for Dec 2025)<br>• Dual-Axis Time Series Chart (Monthly SIP Inflow Bars + NIFTY 50 Line overlay)<br>• Top 5 Categories by FY25 Net Inflow Bar Chart (Liquid, Sectoral, Flexi Cap, Large & Mid Cap, Short Duration)<br>• $12 \times 12$ Category Net Inflow Heatmap with contrast intensity scaling | [`P4_SIP_Market_Trends.png`](Day-06-PowerBI-Dashboard-Design/tableau/P4_SIP_Market_Trends.png) |

---

## 9. Final Reports & Presentation Materials

In addition to the repository assets, the project includes executive presentation materials:
- **Final Project Report (`Final_Report.pdf`)**: A 16-page report covering dataset inventory, ETL architecture, EDA findings, quantitative performance methodology, composite scoring, dashboard walkthroughs, limitations, and recommendations.
- **Executive Presentation (`Bluestock_MF_Presentation.pptx`)**: A slide deck detailing project findings, data pipelines, and analytical outcomes.

---

## 10. Data Authenticity & Limitations

1. **Educational & Demonstration Context**: This analytics platform is developed as a capstone project for Bluestock Fintech. Mutual fund investments are subject to market risks, and this solution does not constitute financial investment advice.
2. **Data Sources & Synthesis**:
   - AMFI master data, benchmark index history, and AMC quarterly AUM values reflect real public market figures.
   - Investor transaction records (5,000 investors, 32,778 transactions) are synthetically generated for demonstration.
   - Forward NAV data points are anchored to historical trajectories with simulated extensions.
3. **Dataset vs Industry Scope**:
   - The Top 10 AMC AUM figure (**₹62.74 Lakh Cr**) represents the aggregate of the 10 fund houses present in the dataset.
   - The wider industry total benchmark (~**₹81 Lakh Cr**) is cited on Page 1 for macro comparison.

---

## 11. Final Deliverables Checklist

- [x] **Relational Database**: `Day-02-Data-Cleaning-SQL/database/bluestock_mf.db` (10 tables, star schema)
- [x] **Analytical Notebooks**:
  - `Day-03-Exploratory-Data-Analysis/notebooks/EDA_Analysis.ipynb`
  - `Day-04-Fund-Performance-Analytics/notebooks/Performance_Analytics.ipynb`
  - `Day-05-Advanced-Risk-Analytics/notebooks/Advanced_Analytics.ipynb`
- [x] **Cleaned Datasets**: `Day-02-Data-Cleaning-SQL/data/processed/*.csv` (10 CSV files)
- [x] **Packaged Tableau Workbook**: `Day-06-PowerBI-Dashboard-Design/tableau/bluestock_mf_dashboard.twbx`
- [x] **Dashboard PDF Export**: `Day-06-PowerBI-Dashboard-Design/tableau/Dashboard.pdf`
- [x] **Dashboard Screenshots**:
  - `Day-06-PowerBI-Dashboard-Design/tableau/P1_Industry_Overview.png`
  - `Day-06-PowerBI-Dashboard-Design/tableau/P2_Fund_Performance.png`
  - `Day-06-PowerBI-Dashboard-Design/tableau/P3_Investor_Analytics.png`
  - `Day-06-PowerBI-Dashboard-Design/tableau/P4_SIP_Market_Trends.png`

---

## 12. Author

**Prepared by:** Shubham Sharma  
**Project:** Bluestock Mutual Fund Analytics Capstone  
**Date:** August 2026

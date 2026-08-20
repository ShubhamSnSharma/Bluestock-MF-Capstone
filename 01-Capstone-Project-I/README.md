# Bluestock Mutual Fund Analytics Platform
## End-to-End Data Engineering, Quantitative Analytics & Interactive BI Dashboard

[![Python](https://img.shields.io/badge/Python-3.11%2B%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%203-lightgrey.svg)](https://www.sqlite.org/)
[![BI Platform](https://img.shields.io/badge/BI%20Platform-Tableau-E97627.svg)](https://www.tableau.com/)

---

## 1. Project Overview

The **Bluestock Mutual Fund Analytics Platform** is an end-to-end data engineering and financial analytics project developed for Bluestock Fintech. The platform ingests, cleans, validates, and analyzes Indian mutual fund data across 40 schemes, 10 AMC fund houses, and 5,000 investors over a multi-year timeline (2022–2026).

### Analytical Pipeline Stages
1. **Raw Data Ingestion & Profiling**: Automated ingestion of 10 raw CSV datasets, data type auditing, and live NAV API connectivity (`mfapi.in`).
2. **Data Cleaning & Transformation**: Multi-stage data cleaning pipelines handling date standardization, outlier winsorization, missing value imputation, and validation.
3. **Relational Modeling & SQL Storage**: A star-schema database in SQLite (`bluestock_mf.db`) with 10 tables, referential integrity constraints, and an analytical query suite.
4. **Exploratory Data Analysis (EDA)**: Statistical profiling, distribution analysis, AUM concentration across fund houses, and demographic transaction patterns.
5. **Fund Performance & Multi-Factor Ranking**: Annualized CAGR (1Y, 3Y, 5Y), Volatility, Sharpe Ratio, Sortino Ratio, Benchmark Alpha/Beta (OLS Regression vs NIFTY 100/50), Max Drawdown, and a 5-factor composite scorecard.
6. **Advanced Risk & Behavioral Analytics**: Historical Value at Risk (VaR 95%), Conditional VaR (CVaR 95%), rolling 90-day Sharpe ratios, Herfindahl-Hirschman Index (HHI) for sector concentration, investor cohort retention, and SIP continuity gap detection (>35 days).
7. **Executive BI Dashboard**: A 4-page interactive dashboard delivered in Tableau covering Industry Overview, Fund Performance, Investor Analytics, and SIP & Market Trends.

---

## 2. Project Objectives

- **O1 — Automated Data Pipeline**: Ingest, standardize, and clean multi-source mutual fund datasets with automated validation checks.
- **O2 — Relational Data Modeling**: Design and implement a normalized relational star-schema database in SQLite.
- **O3 — Exploratory Data Analysis**: Analyze industry-scale growth, SIP inflows, AUM distribution across top AMCs, and investor transaction patterns.
- **O4 — Quantitative Risk & Return Analytics**: Implement quantitative financial algorithms for risk-adjusted returns (Sharpe, Sortino), market sensitivity (Alpha, Beta), tail risk (VaR, CVaR), and multi-factor ranking.
- **O5 — Executive Dashboard Design**: Develop a 4-page interactive BI dashboard in Tableau with dynamic filtering, normalized benchmark comparison, and dual-axis time series.
- **O6 — Investor Retention & Behavior Modeling**: Track investor onboarding cohorts, transaction frequency, and detect at-risk investors with SIP gaps exceeding 35 days.
- **O7 — Comprehensive Documentation & Reproducibility**: Deliver reproducible scripts, verified Jupyter Notebooks, analytical markdown reports, executive presentation deck, and PDF exports.

---

## 3. Dataset Inventory

The project utilizes 10 core datasets covering fund master metadata, daily NAVs, AUM, SIP trends, folios, transactions, holdings, and benchmark indices:

| # | Dataset File (`data/processed/`) | Rows | Description | Key Fields |
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

- **Programming & Analytics**: Python 3.11+ / 3.13 (Pandas, NumPy, SciPy, Statsmodels, Matplotlib, Seaborn, Plotly)
- **Database & Query Engine**: SQLite 3, SQLAlchemy, SQL (DDL, DML, Window Functions, Aggregate Joins)
- **Interactive Computing**: Jupyter Notebooks (`.ipynb`)
- **Business Intelligence**: Tableau Desktop / Tableau Public (`.twbx`, `.twb`, Hyper API extracts)
- **Documentation & Reporting**: Python-pptx, PyPDF, Markdown
- **Version Control**: Git, GitHub

---

## 5. Repository Structure

```text
Bluestock-MF-Capstone/
├── README.md                                   # Master project documentation
├── .gitignore                                  # Git exclusion rules
├── run_pipeline.py                             # Master execution pipeline script
├── requirements.txt                            # Consolidated Python dependencies
│
├── data/
│   ├── raw/                                    # 10 raw CSV source files
│   ├── processed/                              # 10 cleaned & validated CSV datasets
│   ├── database/
│   │   └── bluestock_mf.db                     # Canonical SQLite relational star-schema database
│   └── api/                                    # Live NAV API cached responses
│
├── sql/
│   ├── schema.sql                              # DDL table creation & star-schema scripts
│   └── queries.sql                             # 10 analytical business SQL queries
│
├── scripts/
│   ├── data_ingestion.py                       # Ingestion and profiling script
│   ├── live_nav_fetch.py                       # Live NAV API connector (mfapi.in)
│   ├── run_cleaning_pipeline.py                # Master data cleaning execution runner
│   ├── build_database.py                       # Database builder and table loader
│   ├── execute_queries.py                      # SQL query suite executor
│   ├── performance_metrics.py                  # Core return/volatility/scorecard engine
│   ├── advanced_metrics.py                     # VaR/CVaR, rolling Sharpe & HHI engine
│   ├── cohort_analysis.py                      # Investor cohort analysis engine
│   ├── sip_analysis.py                         # SIP continuity & gap detection engine
│   ├── recommender.py                          # Risk-grade scheme recommender
│   ├── insight_engine.py                       # Automated narrative insight generator
│   ├── eda_utils.py                            # EDA plotting helper utilities
│   ├── verify_data_cleaning.py                 # Data cleaning validation runner
│   ├── verify_eda.py                           # EDA verification runner
│   ├── verify_performance.py                   # Performance analytics verification runner
│   └── verify_risk.py                          # Risk analytics verification runner
│
├── notebooks/
│   ├── EDA_Analysis.ipynb                      # Exploratory Data Analysis & visual profiling
│   ├── Performance_Analytics.ipynb             # Fund performance, CAGR, Sharpe & scorecard
│   └── Advanced_Analytics.ipynb                # Tail risk (VaR/CVaR), cohorts & SIP gaps
│
├── outputs/                                    # Exported analytical metric CSVs
│   ├── alpha_beta.csv                          # Alpha & Beta regression metrics
│   ├── cagr_comparison.csv                     # 1Y, 3Y, and available CAGR returns
│   ├── daily_returns.csv                       # Historical daily return matrix
│   ├── drawdown_summary.csv                    # Max drawdowns & recovery timelines
│   ├── fund_scorecard.csv                      # Multi-factor composite scorecard & rankings
│   ├── risk_metrics.csv                        # Consolidated risk metrics table
│   ├── sharpe_ratio.csv                        # Annualized Sharpe ratios & ranks
│   ├── sortino_ratio.csv                       # Annualized Sortino ratios & ranks
│   └── var_cvar_report.csv                     # Historical VaR (95%) & CVaR (95%)
│
├── charts/
│   ├── eda/                                    # EDA charts (PNG & interactive HTML)
│   ├── performance/                            # Fund performance & scorecard charts (PNG)
│   └── risk/                                   # Rolling Sharpe & SIP gap charts (PNG)
│
├── reports/
│   ├── Final_Report.pdf                        # 16-page comprehensive executive project report
│   ├── Bluestock_MF_Presentation.pptx          # 12-slide executive presentation slide deck
│   └── validation/                             # Technical audit & validation checklists
│
└── dashboard/
    ├── bluestock_mf_dashboard.twbx             # Packaged Tableau workbook (4 pages, embedded Hyper data)
    ├── Dashboard.pdf                           # 4-page exported dashboard PDF
    ├── P1_Industry_Overview.png                # Page 1 high-resolution screenshot
    ├── P2_Fund_Performance.png                 # Page 2 high-resolution screenshot
    ├── P3_Investor_Analytics.png               # Page 3 high-resolution screenshot
    ├── P4_SIP_Market_Trends.png                # Page 4 high-resolution screenshot
    └── documentation/                          # Theme, visual specifications, DAX dictionary
```

---

## 6. Setup & Installation Instructions

### Prerequisites
- **Python**: Version 3.11 or higher
- **Tableau**: Tableau Desktop or Tableau Public (to open `.twbx`)
- **SQLite**: SQLite 3 (or DB Browser for SQLite)

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
   pip install -r requirements.txt
   ```

---

## 7. How to Run the Pipeline & Analytics

### Recommended: Run the Complete Master Pipeline
To execute the entire multi-stage data engineering, cleaning, database generation, and analytical verification pipeline in sequence with a single command:

```bash
python run_pipeline.py
```

`run_pipeline.py` orchestrates the complete project workflow sequentially:
1. **Raw Data Ingestion & Profiling** (`scripts/data_ingestion.py`)
2. **Automated Data Cleaning & Transformation** (`scripts/run_cleaning_pipeline.py`)
3. **SQLite Star-Schema Database Build** (`scripts/build_database.py`)
4. **Analytical SQL Query Suite Execution** (`scripts/execute_queries.py`)
5. **Fund Performance & Multi-Factor Scorecard Analytics** (`scripts/verify_performance.py`)
6. **Advanced Risk, Tail Loss (VaR/CVaR) & Investor Analytics** (`scripts/verify_risk.py`)

---

### Alternative: Run Individual Stages Manually
Each stage of the analytics pipeline can also be executed independently via its respective script or explored interactively inside the Jupyter Notebooks.

#### Step 1: Run Data Ingestion & Live NAV Fetching
```bash
python scripts/data_ingestion.py
python scripts/live_nav_fetch.py
```

#### Step 2: Execute Data Cleaning & Build SQLite Database
```bash
# Run data cleaning and export cleaned CSVs to data/processed/
python scripts/run_cleaning_pipeline.py

# Build SQLite database and populate tables in data/database/bluestock_mf.db
python scripts/build_database.py

# Execute 10 analytical SQL queries against the database
python scripts/execute_queries.py
```

#### Step 3: Run Fund Performance & Scorecard Analytics
```bash
python scripts/verify_performance.py
```
*Or open and run `notebooks/Performance_Analytics.ipynb` in Jupyter.*

#### Step 4: Run Advanced Risk, VaR/CVaR, Cohort & SIP Gap Analytics
```bash
python scripts/verify_risk.py
```
*Or open and run `notebooks/Advanced_Analytics.ipynb` in Jupyter.*

---

## 8. Tableau Dashboard Deliverables & Usage

The final executive dashboard is delivered in Tableau and stored in [`dashboard/`](dashboard/).

### How to Open the Dashboard
- **Using Tableau Desktop / Tableau Public**:
  Open the packaged workbook:
  [`dashboard/bluestock_mf_dashboard.twbx`](dashboard/bluestock_mf_dashboard.twbx)
  *Because it is a packaged `.twbx` workbook, all Hyper data extracts are self-contained—no external database connection or file path configuration is required.*
- **Using PDF Reader**:
  Open the exported multi-page document:
  [`dashboard/Dashboard.pdf`](dashboard/Dashboard.pdf)

### Dashboard Pages Breakdown

| Page | Dashboard Name | Key Visuals & Features | Deliverable Screenshot |
|---|---|---|---|
| **Page 1** | `P1_Industry_Overview` | • 4 Executive KPI Cards (Top 10 AMC AUM ₹62.74L Cr, Monthly SIP Inflow ₹31,002 Cr, Folios 26.12 Cr, Top 10 Schemes 1,522)<br>• Industry AUM Growth Area Chart (2022–2026)<br>• AMC AUM Horizontal Bar Chart (Top 10 AMCs) | [`dashboard/P1_Industry_Overview.png`](dashboard/P1_Industry_Overview.png) |
| **Page 2** | `P2_Fund_Performance` | • Interactive Filter Bar (Fund House, Category, Plan, Scheme Name)<br>• Risk vs Return Scatter Plot (Return 3Y vs Std Dev, bubble size by AUM)<br>• 13-Column Sortable Fund Performance Scorecard<br>• Normalized NAV vs Benchmark Tracking (Base = 100) | [`dashboard/P2_Fund_Performance.png`](dashboard/P2_Fund_Performance.png) |
| **Page 3** | `P3_Investor_Analytics` | • State-wise Transaction Amount Bar Chart (Descending by state volume)<br>• Transaction Type Split (Lumpsum 58.5%, Redemption 35.3%, SIP 6.2%)<br>• Age Group vs Average SIP Amount Column Chart<br>• Monthly Transaction Volume Trend | [`dashboard/P3_Investor_Analytics.png`](dashboard/P3_Investor_Analytics.png) |
| **Page 4** | `P4_SIP_Market_Trends` | • SIP YoY Growth KPI Badge (`17.17%` for Dec 2025)<br>• Dual-Axis Time Series Chart (Monthly SIP Inflow Bars + NIFTY 50 Line overlay)<br>• Top 5 Categories by FY25 Net Inflow Bar Chart (Liquid, Sectoral, Flexi Cap, Large & Mid Cap, Short Duration)<br>• $12 \times 12$ Category Net Inflow Heatmap with contrast intensity scaling | [`dashboard/P4_SIP_Market_Trends.png`](dashboard/P4_SIP_Market_Trends.png) |

---

## 9. Final Reports & Presentation Materials

Located in [`reports/`](reports/):
- **Final Project Report ([`reports/Final_Report.pdf`](reports/Final_Report.pdf))**: A 16-page comprehensive executive report covering dataset inventory, ETL architecture, EDA findings, quantitative performance methodology, composite scoring, dashboard walkthroughs, limitations, and recommendations.
- **Executive Presentation ([`reports/Bluestock_MF_Presentation.pptx`](reports/Bluestock_MF_Presentation.pptx))**: A 12-slide executive slide deck detailing project findings, data pipelines, and analytical outcomes.

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

- [x] **Relational Database**: `data/database/bluestock_mf.db` (10 tables, star schema)
- [x] **Analytical Notebooks**:
  - `notebooks/EDA_Analysis.ipynb`
  - `notebooks/Performance_Analytics.ipynb`
  - `notebooks/Advanced_Analytics.ipynb`
- [x] **Cleaned Datasets**: `data/processed/*.csv` (10 CSV files)
- [x] **Raw Datasets**: `data/raw/*.csv` (10 CSV files)
- [x] **SQL Scripts**: `sql/schema.sql` and `sql/queries.sql`
- [x] **Packaged Tableau Workbook**: `dashboard/bluestock_mf_dashboard.twbx`
- [x] **Dashboard PDF Export**: `dashboard/Dashboard.pdf`
- [x] **Dashboard Screenshots**: `dashboard/P[1-4]_*.png` (4 PNG files)
- [x] **Final Project Report**: `reports/Final_Report.pdf` (16 pages)
- [x] **Executive Presentation**: `reports/Bluestock_MF_Presentation.pptx` (12 slides)
- [x] **Master Execution Pipeline**: `run_pipeline.py`

---

## 12. Author

**Prepared by:** Shubham Sharma  
**Project:** Bluestock Mutual Fund Analytics Capstone  
**Date:** August 2026

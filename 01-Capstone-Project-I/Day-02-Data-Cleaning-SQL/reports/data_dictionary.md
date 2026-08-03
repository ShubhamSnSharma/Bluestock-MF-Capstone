# Data Dictionary (Day 02)

**Project:** Bluestock Mutual Fund Capstone — Day 02 Data Cleaning & SQL  
**Generated On:** 2026-08-03  
**Database File:** `database/bluestock_mf.db`  
**Architecture:** Star Schema Dimensional Model + Staging/Auxiliary Tables  

---

## Overview

This Data Dictionary provides a comprehensive technical reference for all **11 tables** created and loaded into the SQLite database `database/bluestock_mf.db`. It details table roles, primary keys, foreign keys, storage data types, business definitions, and data lineage mapping back to the raw/processed CSV datasets.

---

## Table Inventory Summary

| Table Name | Architecture Role | Entity Purpose | Source Dataset | Primary Key | Foreign Key(s) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `dim_fund` | Dimension | Mutual Fund Scheme Metadata | `01_fund_master_cleaned.csv` | `amfi_code` | None |
| `dim_date` | Dimension | Calendar Date Dimension | Generated | `date_key` | None |
| `fact_nav` | Fact Table | Daily Net Asset Value (NAV) | `02_nav_history_cleaned.csv` | `(amfi_code, date_key)` | `amfi_code`, `date_key` |
| `fact_transactions` | Fact Table | Retail Investor Transactions | `08_investor_transactions_cleaned.csv` | `transaction_id` | `amfi_code`, `date_key` |
| `fact_performance` | Fact Table | Returns & Risk Metrics | `07_scheme_performance_cleaned.csv` | `amfi_code` | `amfi_code` |
| `fact_aum` | Fact Table | Quarterly AUM by AMC | `03_aum_by_fund_house_cleaned.csv` | `(fund_house, date_key)` | `date_key` |
| `stg_monthly_sip_inflows` | Supporting | Monthly Industry SIP Inflows | `04_monthly_sip_inflows_cleaned.csv` | `month` | None |
| `stg_category_inflows` | Supporting | Category Net Capital Inflows | `05_category_inflows_cleaned.csv` | `(month, category)` | None |
| `stg_industry_folio_count` | Supporting | Category Folio Counts | `06_industry_folio_count_cleaned.csv` | `month` | None |
| `stg_portfolio_holdings` | Supporting | Stock Holdings & Sectors | `09_portfolio_holdings_cleaned.csv` | `(amfi_code, stock_symbol)` | `amfi_code` |
| `stg_benchmark_indices` | Supporting | Daily Benchmark Index Levels | `10_benchmark_indices_cleaned.csv` | `(date, index_name)` | None |

---

## Detailed Table Specifications & Data Dictionaries

### 1. Dimension Tables

#### 1.1 `dim_fund`
- **Purpose:** Central dimension table containing all descriptive metadata, AMC details, SEBI classifications, and plan policies for mutual fund schemes.
- **Source Dataset:** `01_fund_master_cleaned.csv`
- **Primary Key:** `amfi_code`
- **Foreign Keys:** None

| Column Name | SQLite Type | Description | Business Meaning | Source Dataset |
| :--- | :--- | :--- | :--- | :--- |
| `amfi_code` | `INTEGER` | Unique 6-digit AMFI Scheme Code | Primary Key identifying the mutual fund scheme | `01_fund_master_cleaned.csv` |
| `fund_house` | `TEXT` | Asset Management Company (AMC) name | Name of the fund management institution | `01_fund_master_cleaned.csv` |
| `scheme_name` | `TEXT` | Full Mutual Fund Scheme Name | Official public name of the mutual fund scheme | `01_fund_master_cleaned.csv` |
| `category` | `TEXT` | Asset Class Category | Broad asset category (e.g., Equity, Debt, Hybrid) | `01_fund_master_cleaned.csv` |
| `sub_category` | `TEXT` | SEBI Sub-Category | Granular classification (e.g., Large Cap, Flexi Cap) | `01_fund_master_cleaned.csv` |
| `plan` | `TEXT` | Plan Option Type | Distribution channel plan (Direct vs Regular) | `01_fund_master_cleaned.csv` |
| `launch_date` | `TEXT` | Fund Inception Date | Date the fund was officially launched (YYYY-MM-DD) | `01_fund_master_cleaned.csv` |
| `benchmark` | `TEXT` | Benchmark Index Name | Benchmark market index used for performance tracking | `01_fund_master_cleaned.csv` |
| `expense_ratio_pct` | `REAL` | Total Expense Ratio (%) | Annualized expense ratio percentage charged by AMC | `01_fund_master_cleaned.csv` |
| `exit_load_pct` | `REAL` | Exit Load Percentage | Penalty percentage charged for premature redemption | `01_fund_master_cleaned.csv` |
| `min_sip_amount` | `INTEGER` | Minimum SIP Amount (INR) | Minimum recurring SIP installment amount | `01_fund_master_cleaned.csv` |
| `min_lumpsum_amount` | `INTEGER` | Minimum Lumpsum Amount (INR) | Minimum one-time lumpsum investment amount | `01_fund_master_cleaned.csv` |
| `fund_manager` | `TEXT` | Portfolio Manager(s) | Designated financial professional managing fund assets | `01_fund_master_cleaned.csv` |
| `risk_category` | `TEXT` | SEBI Riskometer Rating | Risk level (Very High, High, Moderate, Low to Moderate) | `01_fund_master_cleaned.csv` |
| `sebi_category_code` | `TEXT` | SEBI Categorization Code | Regulatory classification code assigned by SEBI | `01_fund_master_cleaned.csv` |

---

#### 1.2 `dim_date`
- **Purpose:** Conformed calendar dimension table enabling temporal aggregation (daily, monthly, quarterly, yearly, YoY, MoM).
- **Source Dataset:** Generated from all unique dataset dates
- **Primary Key:** `date_key`
- **Foreign Keys:** None

| Column Name | SQLite Type | Description | Business Meaning | Source Dataset |
| :--- | :--- | :--- | :--- | :--- |
| `date_key` | `INTEGER` | Surrogate Date Key | Integer surrogate key formatted as YYYYMMDD | Generated |
| `full_date` | `TEXT` | ISO Standard Date String | Standard ISO date representation (YYYY-MM-DD) | Generated |
| `year` | `INTEGER` | Calendar Year | Four-digit calendar year (e.g., 2024) | Generated |
| `quarter` | `INTEGER` | Calendar Quarter | Calendar quarter number (1, 2, 3, or 4) | Generated |
| `month` | `INTEGER` | Month Number | Calendar month number (1 to 12) | Generated |
| `month_name` | `TEXT` | Month Name | Full English month name (January, February, etc.) | Generated |
| `week` | `INTEGER` | ISO Week Number | ISO week number of the year (1 to 53) | Generated |
| `day` | `INTEGER` | Day of Month | Day number within month (1 to 31) | Generated |
| `day_name` | `TEXT` | Day Name | Name of the day of the week (Monday, Tuesday, etc.) | Generated |
| `is_weekend` | `INTEGER` | Weekend Flag | 1 if Saturday or Sunday; 0 if Weekday | Generated |

---

### 2. Fact Tables

#### 2.1 `fact_nav`
- **Purpose:** High-frequency transaction fact table recording daily Net Asset Values for performance calculation and valuation.
- **Source Dataset:** `02_nav_history_cleaned.csv`
- **Primary Key:** Composite Key `(amfi_code, date_key)`
- **Foreign Keys:** `amfi_code` → `dim_fund(amfi_code)`, `date_key` → `dim_date(date_key)`

| Column Name | SQLite Type | Description | Business Meaning | Source Dataset |
| :--- | :--- | :--- | :--- | :--- |
| `amfi_code` | `INTEGER` | Foreign Key to `dim_fund` | AMFI code referencing mutual fund scheme | `02_nav_history_cleaned.csv` |
| `date_key` | `INTEGER` | Foreign Key to `dim_date` | Date key referencing trading date | `02_nav_history_cleaned.csv` |
| `nav` | `REAL` | Net Asset Value (INR) | Daily per-unit valuation price of the scheme | `02_nav_history_cleaned.csv` |

---

#### 2.2 `fact_transactions`
- **Purpose:** Granular retail transaction event table recording investment flows, demographics, and payment modes.
- **Source Dataset:** `08_investor_transactions_cleaned.csv`
- **Primary Key:** `transaction_id` (`AUTOINCREMENT`)
- **Foreign Keys:** `amfi_code` → `dim_fund(amfi_code)`, `date_key` → `dim_date(date_key)`

| Column Name | SQLite Type | Description | Business Meaning | Source Dataset |
| :--- | :--- | :--- | :--- | :--- |
| `transaction_id` | `INTEGER` | Primary Key | Auto-incrementing transaction sequence ID | Generated |
| `investor_id` | `TEXT` | Investor Unique Identifier | Anonymized investor profile ID | `08_investor_transactions_cleaned.csv` |
| `amfi_code` | `INTEGER` | Foreign Key to `dim_fund` | Target scheme AMFI code | `08_investor_transactions_cleaned.csv` |
| `date_key` | `INTEGER` | Foreign Key to `dim_date` | Date key referencing transaction execution date | `08_investor_transactions_cleaned.csv` |
| `transaction_type` | `TEXT` | Transaction Category | Mode of order (SIP, Lumpsum, Redemption) | `08_investor_transactions_cleaned.csv` |
| `amount_inr` | `REAL` | Transaction Value (INR) | Monetary value of the order in INR | `08_investor_transactions_cleaned.csv` |
| `state` | `TEXT` | Investor State | State location of investor residence | `08_investor_transactions_cleaned.csv` |
| `city` | `TEXT` | Investor City | City location of investor residence | `08_investor_transactions_cleaned.csv` |
| `city_tier` | `TEXT` | City Tier Classification | Tier 1, Tier 2, or Tier 3 demographic classification | `08_investor_transactions_cleaned.csv` |
| `age_group` | `TEXT` | Demographic Age Group | Investor age bracket (e.g., 18-25, 26-35) | `08_investor_transactions_cleaned.csv` |
| `gender` | `TEXT` | Investor Gender | Gender classification (Male, Female) | `08_investor_transactions_cleaned.csv` |
| `annual_income_lakh` | `REAL` | Annual Income (Lakh INR) | Self-declared annual income tier in Lakhs INR | `08_investor_transactions_cleaned.csv` |
| `payment_mode` | `TEXT` | Payment Channel | Payment mode (UPI, NetBanking, NEFT, Mandate) | `08_investor_transactions_cleaned.csv` |
| `kyc_status` | `TEXT` | Regulatory KYC Status | Investor KYC status (Verified, Pending, Rejected) | `08_investor_transactions_cleaned.csv` |

---

#### 2.3 `fact_performance`
- **Purpose:** Scheme performance and risk rating fact table storing annualized returns, volatility indicators, and expense audit flags.
- **Source Dataset:** `07_scheme_performance_cleaned.csv`
- **Primary Key:** `amfi_code`
- **Foreign Keys:** `amfi_code` → `dim_fund(amfi_code)`

| Column Name | SQLite Type | Description | Business Meaning | Source Dataset |
| :--- | :--- | :--- | :--- | :--- |
| `amfi_code` | `INTEGER` | Primary & Foreign Key | AMFI code referencing mutual fund scheme | `07_scheme_performance_cleaned.csv` |
| `return_1yr_pct` | `REAL` | 1-Year Annualized Return (%) | 12-month historical trailing return percentage | `07_scheme_performance_cleaned.csv` |
| `return_3yr_pct` | `REAL` | 3-Year Annualized Return (%) | 36-month annualized trailing return percentage | `07_scheme_performance_cleaned.csv` |
| `return_5yr_pct` | `REAL` | 5-Year Annualized Return (%) | 60-month annualized trailing return percentage | `07_scheme_performance_cleaned.csv` |
| `benchmark_3yr_pct` | `REAL` | Benchmark 3-Year Return (%) | 3-year annualized return percentage of benchmark | `07_scheme_performance_cleaned.csv` |
| `alpha` | `REAL` | Jensen's Alpha | Outperformance risk-adjusted metric vs benchmark | `07_scheme_performance_cleaned.csv` |
| `beta` | `REAL` | Systematic Volatility Beta | Relative volatility measure compared to market index | `07_scheme_performance_cleaned.csv` |
| `sharpe_ratio` | `REAL` | Sharpe Ratio | Risk-adjusted return ratio over risk-free rate | `07_scheme_performance_cleaned.csv` |
| `sortino_ratio` | `REAL` | Sortino Ratio | Downside risk-adjusted return ratio | `07_scheme_performance_cleaned.csv` |
| `std_dev_ann_pct` | `REAL` | Annualized Standard Deviation | Volatility standard deviation percentage | `07_scheme_performance_cleaned.csv` |
| `max_drawdown_pct` | `REAL` | Maximum Drawdown (%) | Peak-to-trough historical decline percentage | `07_scheme_performance_cleaned.csv` |
| `aum_crore` | `REAL` | Scheme AUM (Crore INR) | Asset size managed under this specific scheme | `07_scheme_performance_cleaned.csv` |
| `expense_ratio_pct` | `REAL` | Total Expense Ratio (%) | Scheme total expense ratio percentage | `07_scheme_performance_cleaned.csv` |
| `expense_ratio_flag` | `INTEGER` | Expense Ratio Audit Flag | 1 if TER outside [0.1%, 2.5%], 0 if inside valid range | `07_scheme_performance_cleaned.csv` |
| `morningstar_rating` | `INTEGER` | Morningstar Star Rating | Quantitative rating stars (1 to 5 stars) | `07_scheme_performance_cleaned.csv` |
| `risk_grade` | `TEXT` | Riskometer Category Grade | Categorical risk grade (Below Average, Low, High, etc.) | `07_scheme_performance_cleaned.csv` |

---

#### 2.4 `fact_aum`
- **Purpose:** Macro-level quarterly fund house asset table capturing total AUM and active scheme counts per AMC over time.
- **Source Dataset:** `03_aum_by_fund_house_cleaned.csv`
- **Primary Key:** Composite Key `(fund_house, date_key)`
- **Foreign Keys:** `date_key` → `dim_date(date_key)`

| Column Name | SQLite Type | Description | Business Meaning | Source Dataset |
| :--- | :--- | :--- | :--- | :--- |
| `fund_house` | `TEXT` | Fund House Name | Primary Key component identifying AMC | `03_aum_by_fund_house_cleaned.csv` |
| `date_key` | `INTEGER` | Foreign Key to `dim_date` | Primary Key component identifying quarterly date | `03_aum_by_fund_house_cleaned.csv` |
| `aum_lakh_crore` | `REAL` | Total AUM (Lakh Crore INR) | AMC total assets under management in Lakh Crore | `03_aum_by_fund_house_cleaned.csv` |
| `aum_crore` | `INTEGER` | Total AUM (Crore INR) | AMC total assets under management in Crore INR | `03_aum_by_fund_house_cleaned.csv` |
| `num_schemes` | `INTEGER` | Active Scheme Count | Total active schemes managed by the fund house | `03_aum_by_fund_house_cleaned.csv` |

---

### 3. Supporting / Staging Tables

#### 3.1 `stg_monthly_sip_inflows`
- **Purpose:** Industry-wide monthly SIP inflows, active account counts, new registrations, and YoY growth.
- **Source Dataset:** `04_monthly_sip_inflows_cleaned.csv`
- **Primary Key:** `month`
- **Foreign Keys:** None

| Column Name | SQLite Type | Description | Business Meaning | Source Dataset |
| :--- | :--- | :--- | :--- | :--- |
| `month` | `TEXT` | Month (YYYY-MM) | Calendar month string identifier | `04_monthly_sip_inflows_cleaned.csv` |
| `sip_inflow_crore` | `INTEGER` | Monthly SIP Inflow (Crore INR) | Total monthly SIP capital inflow in Crore INR | `04_monthly_sip_inflows_cleaned.csv` |
| `active_sip_accounts_crore` | `REAL` | Active SIP Accounts (Crore) | Total active SIP accounts registered in industry | `04_monthly_sip_inflows_cleaned.csv` |
| `new_sip_accounts_lakh` | `REAL` | New SIP Registrations (Lakh) | Monthly newly opened SIP accounts in Lakh | `04_monthly_sip_inflows_cleaned.csv` |
| `sip_aum_lakh_crore` | `REAL` | Total SIP AUM (Lakh Crore INR) | Industry total assets accumulated via SIP | `04_monthly_sip_inflows_cleaned.csv` |
| `yoy_growth_pct` | `REAL` | YoY Growth Percentage (%) | Year-over-Year growth percentage rate | `04_monthly_sip_inflows_cleaned.csv` |

---

#### 3.2 `stg_category_inflows`
- **Purpose:** Monthly net capital inflows across asset sub-categories.
- **Source Dataset:** `05_category_inflows_cleaned.csv`
- **Primary Key:** Composite Key `(month, category)`
- **Foreign Keys:** None

| Column Name | SQLite Type | Description | Business Meaning | Source Dataset |
| :--- | :--- | :--- | :--- | :--- |
| `month` | `TEXT` | Month (YYYY-MM) | Calendar month string identifier | `05_category_inflows_cleaned.csv` |
| `category` | `TEXT` | Asset Sub-Category | Sub-category name (Small Cap, Sectoral, Overnight, etc.) | `05_category_inflows_cleaned.csv` |
| `net_inflow_crore` | `REAL` | Net Inflow (Crore INR) | Monthly net capital flow (negative indicates net outflow) | `05_category_inflows_cleaned.csv` |

---

#### 3.3 `stg_industry_folio_count`
- **Purpose:** Industry-wide investor folio counts categorized by equity, debt, hybrid, and other categories.
- **Source Dataset:** `06_industry_folio_count_cleaned.csv`
- **Primary Key:** `month`
- **Foreign Keys:** None

| Column Name | SQLite Type | Description | Business Meaning | Source Dataset |
| :--- | :--- | :--- | :--- | :--- |
| `month` | `TEXT` | Month (YYYY-MM) | Calendar month string identifier | `06_industry_folio_count_cleaned.csv` |
| `total_folios_crore` | `REAL` | Total Folios (Crore) | Industry total investor mutual fund folios | `06_industry_folio_count_cleaned.csv` |
| `equity_folios_crore` | `REAL` | Equity Folios (Crore) | Active investor folios in Equity schemes | `06_industry_folio_count_cleaned.csv` |
| `debt_folios_crore` | `REAL` | Debt Folios (Crore) | Active investor folios in Debt schemes | `06_industry_folio_count_cleaned.csv` |
| `hybrid_folios_crore` | `REAL` | Hybrid Folios (Crore) | Active investor folios in Hybrid schemes | `06_industry_folio_count_cleaned.csv` |
| `others_folios_crore` | `REAL` | Other Folios (Crore) | Active investor folios in Solution/Passive schemes | `06_industry_folio_count_cleaned.csv` |

---

#### 3.4 `stg_portfolio_holdings`
- **Purpose:** Mutual fund portfolio stock holdings, market values, and sector weights.
- **Source Dataset:** `09_portfolio_holdings_cleaned.csv`
- **Primary Key:** Composite Key `(amfi_code, stock_symbol)`
- **Foreign Keys:** `amfi_code` → `dim_fund(amfi_code)`

| Column Name | SQLite Type | Description | Business Meaning | Source Dataset |
| :--- | :--- | :--- | :--- | :--- |
| `amfi_code` | `INTEGER` | Scheme AMFI Code | Foreign key referencing scheme in `dim_fund` | `09_portfolio_holdings_cleaned.csv` |
| `stock_symbol` | `TEXT` | Stock Ticker Symbol | NSE/BSE equity ticker symbol (e.g., RELIANCE, HDFCBANK) | `09_portfolio_holdings_cleaned.csv` |
| `stock_name` | `TEXT` | Full Stock Name | Company equity security name | `09_portfolio_holdings_cleaned.csv` |
| `sector` | `TEXT` | Industry Sector | Industry sector classification (IT, Banking, Energy, etc.) | `09_portfolio_holdings_cleaned.csv` |
| `weight_pct` | `REAL` | Portfolio Weight (%) | Allocation percentage of stock in scheme portfolio | `09_portfolio_holdings_cleaned.csv` |
| `market_value_cr` | `REAL` | Market Value (Crore INR) | Total holding value in Crore INR | `09_portfolio_holdings_cleaned.csv` |
| `current_price_inr` | `REAL` | Stock Price (INR) | Current market trading price per share in INR | `09_portfolio_holdings_cleaned.csv` |
| `portfolio_date` | `TEXT` | Portfolio Date | Portfolio holding snapshot date (YYYY-MM-DD) | `09_portfolio_holdings_cleaned.csv` |

---

#### 3.5 `stg_benchmark_indices`
- **Purpose:** Daily closing values for benchmark market indices.
- **Source Dataset:** `10_benchmark_indices_cleaned.csv`
- **Primary Key:** Composite Key `(date, index_name)`
- **Foreign Keys:** None

| Column Name | SQLite Type | Description | Business Meaning | Source Dataset |
| :--- | :--- | :--- | :--- | :--- |
| `date` | `TEXT` | Trading Date (YYYY-MM-DD) | Benchmark trading date string | `10_benchmark_indices_cleaned.csv` |
| `index_name` | `TEXT` | Benchmark Index Name | Market index name (e.g., NIFTY_50, BSE_SENSEX) | `10_benchmark_indices_cleaned.csv` |
| `close_value` | `REAL` | Index Closing Price | Daily closing level value of the index | `10_benchmark_indices_cleaned.csv` |

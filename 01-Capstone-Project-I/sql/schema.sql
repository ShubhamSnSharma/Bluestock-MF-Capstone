-- ==============================================================================
-- Bluestock Mutual Fund Capstone Project - Day 02
-- Star Schema Database Definition (SQLite syntax)
-- ==============================================================================
-- Architecture: Star Schema (Central Fact Tables surrounding Dimension Tables)
-- Engine: SQLite 3
-- Author: Data Engineering Team
-- ==============================================================================

-- Enable Foreign Key Constraints in SQLite
PRAGMA foreign_keys = ON;

-- ==============================================================================
-- 1. DIMENSION TABLES
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Table: dim_fund
-- Description: Mutual Fund Scheme Dimension containing descriptive metadata.
-- Source: 01_fund_master_cleaned.csv
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_fund;
CREATE TABLE dim_fund (
    amfi_code INTEGER PRIMARY KEY,          -- Unique AMFI Scheme Code (Primary Key)
    fund_house TEXT NOT NULL,               -- Asset Management Company (AMC) / Fund House Name
    scheme_name TEXT NOT NULL,              -- Full Mutual Fund Scheme Name
    category TEXT NOT NULL,                 -- Asset Category (Equity, Debt, Hybrid, Solution Oriented, etc.)
    sub_category TEXT NOT NULL,             -- SEBI Sub-Category (Large Cap, Mid Cap, Small Cap, etc.)
    plan TEXT NOT NULL,                     -- Plan Type (Direct, Regular)
    launch_date TEXT NOT NULL,              -- Fund Inception Date (YYYY-MM-DD)
    benchmark TEXT NOT NULL,                -- Target Benchmark Index Name
    expense_ratio_pct REAL NOT NULL,        -- Total Expense Ratio (TER %)
    exit_load_pct REAL NOT NULL,            -- Exit Load Percentage
    min_sip_amount INTEGER NOT NULL,        -- Minimum SIP Investment Amount (INR)
    min_lumpsum_amount INTEGER NOT NULL,    -- Minimum Lumpsum Investment Amount (INR)
    fund_manager TEXT NOT NULL,             -- Designated Portfolio Fund Manager(s)
    risk_category TEXT NOT NULL,            -- Riskometer Grade (Very High, High, Moderate, etc.)
    sebi_category_code TEXT NOT NULL        -- SEBI Categorization Code
);

-- ------------------------------------------------------------------------------
-- Table: dim_date
-- Description: Calendar Date Dimension table covering all dataset time periods.
-- Purpose: Enables temporal slicing, trend analysis, YoY, QoQ, and MoM reporting.
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,           -- Surrogate Key (Format: YYYYMMDD, e.g., 20240101)
    full_date TEXT NOT NULL UNIQUE,         -- Standard ISO Date String (YYYY-MM-DD)
    year INTEGER NOT NULL,                  -- Calendar Year (e.g., 2024)
    quarter INTEGER NOT NULL,               -- Calendar Quarter (1 to 4)
    month INTEGER NOT NULL,                 -- Month Number (1 to 12)
    month_name TEXT NOT NULL,               -- Full Month Name (January, February, etc.)
    week INTEGER NOT NULL,                  -- ISO Week Number of the Year (1 to 53)
    day INTEGER NOT NULL,                   -- Day of the Month (1 to 31)
    day_name TEXT NOT NULL,                 -- Day Name (Monday, Tuesday, etc.)
    is_weekend INTEGER NOT NULL CHECK (is_weekend IN (0, 1)) -- Flag: 1 if Saturday/Sunday, 0 if Weekday
);


-- ==============================================================================
-- 2. FACT TABLES
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Table: fact_nav
-- Description: High-frequency daily Net Asset Value (NAV) fact table.
-- Source: 02_nav_history_cleaned.csv
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_nav;
CREATE TABLE fact_nav (
    amfi_code INTEGER NOT NULL,             -- Foreign Key referencing dim_fund
    date_key INTEGER NOT NULL,              -- Foreign Key referencing dim_date
    nav REAL NOT NULL CHECK (nav > 0),      -- Daily Net Asset Value (INR)
    
    PRIMARY KEY (amfi_code, date_key),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE,
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key) ON DELETE CASCADE
);

-- ------------------------------------------------------------------------------
-- Table: fact_transactions
-- Description: Retail investor transaction history fact table.
-- Source: 08_investor_transactions_cleaned.csv
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_transactions;
CREATE TABLE fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Surrogate Primary Key
    investor_id TEXT NOT NULL,              -- Investor Identification Hash
    amfi_code INTEGER NOT NULL,             -- Foreign Key referencing dim_fund
    date_key INTEGER NOT NULL,              -- Foreign Key referencing dim_date
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr REAL NOT NULL CHECK (amount_inr > 0), -- Transaction Amount in INR
    state TEXT NOT NULL,                    -- Investor State
    city TEXT NOT NULL,                     -- Investor City
    city_tier TEXT NOT NULL,                -- City Tier Classification (Tier 1, Tier 2, Tier 3)
    age_group TEXT NOT NULL,                -- Investor Age Group Category
    gender TEXT NOT NULL,                   -- Investor Gender
    annual_income_lakh REAL NOT NULL,       -- Annual Income in Lakhs INR
    payment_mode TEXT NOT NULL,             -- Payment Gateway / Channel (UPI, NetBanking, NEFT, Mandate)
    kyc_status TEXT NOT NULL CHECK (kyc_status IN ('Verified', 'Pending', 'Rejected')),
    
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE,
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key) ON DELETE CASCADE
);

-- ------------------------------------------------------------------------------
-- Table: fact_performance
-- Description: Scheme performance metrics and risk-adjusted return ratios.
-- Source: 07_scheme_performance_cleaned.csv
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_performance;
CREATE TABLE fact_performance (
    amfi_code INTEGER PRIMARY KEY,          -- Primary Key & Foreign Key referencing dim_fund
    return_1yr_pct REAL NOT NULL,           -- 1-Year Annualized Return (%)
    return_3yr_pct REAL NOT NULL,           -- 3-Year Annualized Return (%)
    return_5yr_pct REAL NOT NULL,           -- 5-Year Annualized Return (%)
    benchmark_3yr_pct REAL NOT NULL,        -- Benchmark 3-Year Annualized Return (%)
    alpha REAL NOT NULL,                    -- Jensen's Alpha (Outperformance vs Benchmark)
    beta REAL NOT NULL,                     -- Beta (Systematic Market Volatility Risk)
    sharpe_ratio REAL NOT NULL,             -- Sharpe Ratio (Risk-Adjusted Return)
    sortino_ratio REAL NOT NULL,            -- Sortino Ratio (Downside Risk-Adjusted Return)
    std_dev_ann_pct REAL NOT NULL,          -- Annualized Standard Deviation (%)
    max_drawdown_pct REAL NOT NULL,         -- Maximum Historical Peak-to-Trough Drawdown (%)
    aum_crore REAL NOT NULL,                -- Asset Under Management (Crore INR)
    expense_ratio_pct REAL NOT NULL,        -- Total Expense Ratio (%)
    expense_ratio_flag INTEGER NOT NULL CHECK (expense_ratio_flag IN (0, 1)), -- Flag: 1 if outside [0.1, 2.5]
    morningstar_rating INTEGER NOT NULL,    -- Morningstar Star Rating (1 to 5)
    risk_grade TEXT NOT NULL,               -- Quantitative Risk Grade
    
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE
);

-- ------------------------------------------------------------------------------
-- Table: fact_aum
-- Description: Quarterly Assets Under Management (AUM) by Fund House.
-- Source: 03_aum_by_fund_house_cleaned.csv
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_aum;
CREATE TABLE fact_aum (
    fund_house TEXT NOT NULL,               -- Fund House / AMC Name
    date_key INTEGER NOT NULL,              -- Foreign Key referencing dim_date
    aum_lakh_crore REAL NOT NULL,           -- AUM in Lakh Crore INR
    aum_crore INTEGER NOT NULL,             -- AUM in Crore INR
    num_schemes INTEGER NOT NULL,           -- Total Active Mutual Fund Schemes
    
    PRIMARY KEY (fund_house, date_key),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key) ON DELETE CASCADE
);


-- ==============================================================================
-- 3. AUXILIARY / SUPPORTING DATASET TABLES
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Table: stg_monthly_sip_inflows
-- Description: Monthly industry-wide SIP inflows, active SIP accounts & YoY growth.
-- Source: 04_monthly_sip_inflows_cleaned.csv
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS stg_monthly_sip_inflows;
CREATE TABLE stg_monthly_sip_inflows (
    month TEXT PRIMARY KEY,                 -- Month (YYYY-MM)
    sip_inflow_crore INTEGER NOT NULL,      -- Monthly SIP Inflow in Crore INR
    active_sip_accounts_crore REAL NOT NULL, -- Active SIP Accounts in Crore
    new_sip_accounts_lakh REAL NOT NULL,    -- New Registered SIP Accounts in Lakh
    sip_aum_lakh_crore REAL NOT NULL,       -- Total SIP AUM in Lakh Crore INR
    yoy_growth_pct REAL                     -- Year-over-Year Growth % (Null for first 12 months)
);

-- ------------------------------------------------------------------------------
-- Table: stg_category_inflows
-- Description: Monthly net capital inflows across asset sub-categories.
-- Source: 05_category_inflows_cleaned.csv
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS stg_category_inflows;
CREATE TABLE stg_category_inflows (
    month TEXT NOT NULL,                    -- Month (YYYY-MM)
    category TEXT NOT NULL,                 -- Asset Sub-Category Name
    net_inflow_crore REAL NOT NULL,         -- Net Monthly Inflow in Crore INR
    PRIMARY KEY (month, category)
);

-- ------------------------------------------------------------------------------
-- Table: stg_industry_folio_count
-- Description: Total mutual fund investor folios broken down by asset category.
-- Source: 06_industry_folio_count_cleaned.csv
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS stg_industry_folio_count;
CREATE TABLE stg_industry_folio_count (
    month TEXT PRIMARY KEY,                 -- Month (YYYY-MM)
    total_folios_crore REAL NOT NULL,       -- Total Industry Folios in Crore
    equity_folios_crore REAL NOT NULL,      -- Equity Category Folios in Crore
    debt_folios_crore REAL NOT NULL,        -- Debt Category Folios in Crore
    hybrid_folios_crore REAL NOT NULL,      -- Hybrid Category Folios in Crore
    others_folios_crore REAL NOT NULL       -- Other Category Folios in Crore
);

-- ------------------------------------------------------------------------------
-- Table: stg_portfolio_holdings
-- Description: Fund portfolio stock holdings, market values, and sector weights.
-- Source: 09_portfolio_holdings_cleaned.csv
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS stg_portfolio_holdings;
CREATE TABLE stg_portfolio_holdings (
    amfi_code INTEGER NOT NULL,             -- Scheme AMFI Code
    stock_symbol TEXT NOT NULL,             -- Equity Stock Ticker Symbol
    stock_name TEXT NOT NULL,               -- Full Stock Name
    sector TEXT NOT NULL,                   -- Industry Sector
    weight_pct REAL NOT NULL,               -- Portfolio Weight (%)
    market_value_cr REAL NOT NULL,          -- Holding Market Value in Crore INR
    current_price_inr REAL NOT NULL,        -- Stock Current Market Price in INR
    portfolio_date TEXT NOT NULL,           -- Portfolio Snapshot Date (YYYY-MM-DD)
    PRIMARY KEY (amfi_code, stock_symbol),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE
);

-- ------------------------------------------------------------------------------
-- Table: stg_benchmark_indices
-- Description: Daily closing values for benchmark market indices.
-- Source: 10_benchmark_indices_cleaned.csv
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS stg_benchmark_indices;
CREATE TABLE stg_benchmark_indices (
    date TEXT NOT NULL,                     -- Trading Date (YYYY-MM-DD)
    index_name TEXT NOT NULL,               -- Benchmark Index Name
    close_value REAL NOT NULL,              -- Closing Value
    PRIMARY KEY (date, index_name)
);


-- ==============================================================================
-- 4. PERFORMANCE INDEXES
-- ==============================================================================
-- Indexes optimized for dimensional join performance, time-series querying,
-- and analytical aggregations in SQLite.

-- Index optimizations for fact_nav
CREATE INDEX idx_nav_date ON fact_nav(date_key);
CREATE INDEX idx_nav_fund ON fact_nav(amfi_code);

-- Index optimizations for fact_transactions
CREATE INDEX idx_txn_date ON fact_transactions(date_key);
CREATE INDEX idx_txn_fund ON fact_transactions(amfi_code);

-- Index optimizations for fact_aum
CREATE INDEX idx_aum_date ON fact_aum(date_key);
CREATE INDEX idx_aum_fund_house ON fact_aum(fund_house);

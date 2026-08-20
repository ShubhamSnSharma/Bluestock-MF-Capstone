-- ==============================================================================
-- Bluestock Mutual Fund Capstone Project - Day 02
-- Analytical SQL Queries (SQLite syntax)
-- ==============================================================================
-- Target Database: database/bluestock_mf.db
-- Author: Data Engineering Team
-- ==============================================================================


-- ------------------------------------------------------------------------------
-- QUERY 1: Top 5 Mutual Funds (AMCs) by Latest Available AUM
-- Business Purpose: Identify the top 5 Asset Management Companies (fund houses)
--                   by total Assets Under Management (AUM) in the most recent quarter.
-- ------------------------------------------------------------------------------
SELECT 
    fund_house,
    aum_crore AS latest_aum_crore,
    num_schemes AS active_schemes
FROM fact_aum
WHERE date_key = (SELECT MAX(date_key) FROM fact_aum)
ORDER BY aum_crore DESC
LIMIT 5;


-- ------------------------------------------------------------------------------
-- QUERY 2: Average Monthly NAV Trend Across All Schemes
-- Business Purpose: Compute monthly average Net Asset Value (NAV) across all mutual
--                   fund schemes by joining fact_nav with dim_date.
-- ------------------------------------------------------------------------------
SELECT 
    d.year,
    d.month,
    d.month_name,
    ROUND(AVG(f.nav), 2) AS average_nav
FROM fact_nav f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year ASC, d.month ASC;


-- ------------------------------------------------------------------------------
-- QUERY 3: Year-over-Year (YoY) SIP Growth Trend
-- Business Purpose: Calculate average monthly SIP inflows and YoY growth rate
--                   per year to analyze retail investment expansion.
-- ------------------------------------------------------------------------------
SELECT 
    SUBSTR(month, 1, 4) AS year,
    ROUND(AVG(sip_inflow_crore), 2) AS average_monthly_sip_crore,
    ROUND(AVG(yoy_growth_pct), 2) AS average_yoy_growth_pct
FROM stg_monthly_sip_inflows
GROUP BY SUBSTR(month, 1, 4)
ORDER BY year ASC;


-- ------------------------------------------------------------------------------
-- QUERY 4: Investor Transactions Aggregated by State
-- Business Purpose: Analyze geographic distribution of retail investments to determine
--                   states generating the highest capital flows and transaction volumes.
-- ------------------------------------------------------------------------------
SELECT 
    state,
    COUNT(transaction_id) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;


-- ------------------------------------------------------------------------------
-- QUERY 5: Mutual Fund Schemes with Expense Ratio Below 1.0%
-- Business Purpose: Filter low-cost, cost-efficient mutual fund schemes with TER < 1.0%.
-- ------------------------------------------------------------------------------
SELECT 
    scheme_name AS fund_name,
    fund_house,
    expense_ratio_pct AS expense_ratio
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;


-- ------------------------------------------------------------------------------
-- QUERY 6: Top 10 Mutual Fund Schemes by Historical Average NAV
-- Business Purpose: Rank the top 10 schemes with the highest average daily unit values.
-- ------------------------------------------------------------------------------
SELECT 
    d.amfi_code,
    d.scheme_name,
    d.fund_house,
    ROUND(AVG(n.nav), 2) AS average_nav
FROM fact_nav n
JOIN dim_fund d ON n.amfi_code = d.amfi_code
GROUP BY d.amfi_code, d.scheme_name, d.fund_house
ORDER BY average_nav DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUERY 7: Highest Performing Mutual Fund Schemes Based on 5-Year Return (%)
-- Business Purpose: Identify long-term wealth generators based on 5-year annualized returns.
-- ------------------------------------------------------------------------------
SELECT 
    d.amfi_code,
    d.scheme_name,
    d.fund_house,
    d.category,
    p.return_5yr_pct
FROM fact_performance p
JOIN dim_fund d ON p.amfi_code = d.amfi_code
ORDER BY p.return_5yr_pct DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUERY 8: Monthly Retail Investor Transaction Volume & Capital Flow Trend
-- Business Purpose: Track monthly transaction counts and monetary volumes by transaction type.
-- ------------------------------------------------------------------------------
SELECT 
    dt.year,
    dt.month,
    dt.month_name,
    t.transaction_type,
    COUNT(t.transaction_id) AS transaction_count,
    ROUND(SUM(t.amount_inr), 2) AS total_volume_inr
FROM fact_transactions t
JOIN dim_date dt ON t.date_key = dt.date_key
GROUP BY dt.year, dt.month, dt.month_name, t.transaction_type
ORDER BY dt.year ASC, dt.month ASC, t.transaction_type ASC;


-- ------------------------------------------------------------------------------
-- QUERY 9: Average Transaction Amount by Investment Type (SIP vs Lumpsum vs Redemption)
-- Business Purpose: Compare ticket sizes across investment modes (SIP vs Lumpsum vs Redemption).
-- ------------------------------------------------------------------------------
SELECT 
    transaction_type,
    COUNT(transaction_id) AS transaction_count,
    ROUND(AVG(amount_inr), 2) AS average_amount_inr,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY transaction_type
ORDER BY average_amount_inr DESC;


-- ------------------------------------------------------------------------------
-- QUERY 10: Top Benchmark Indices by Historical Average Closing Value
-- Business Purpose: Compare market benchmark performance and index levels.
-- ------------------------------------------------------------------------------
SELECT 
    index_name,
    ROUND(AVG(close_value), 2) AS average_close_value,
    ROUND(MIN(close_value), 2) AS min_close_value,
    ROUND(MAX(close_value), 2) AS max_close_value
FROM stg_benchmark_indices
GROUP BY index_name
ORDER BY average_close_value DESC;

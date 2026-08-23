-- =============================================================================
-- N100 Financial Intelligence Platform — Exploratory Business Analytics Queries
-- Module: Sprint 1 (Day 07 Exploratory Analysis)
-- Database Target: SQLite (nifty100.db)
-- =============================================================================

-- Query 1: Top 10 Companies by FY 2024 Market Capitalization
SELECT
    c.id AS ticker,
    c.company_name,
    s.broad_sector,
    mc.market_cap_crore,
    mc.enterprise_value_crore,
    mc.pe_ratio,
    mc.pb_ratio
FROM market_cap mc
JOIN companies c ON mc.company_id = c.id
JOIN sectors s ON c.id = s.company_id
WHERE mc.year = '2024'
ORDER BY mc.market_cap_crore DESC
LIMIT 10;

-- Query 2: Broad Sector Breakdown & Weight Distribution
SELECT
    s.broad_sector,
    COUNT(c.id) AS company_count,
    ROUND(SUM(s.index_weight_pct), 2) AS aggregate_weight_pct,
    ROUND(AVG(c.roe_percentage), 2) AS avg_roe_pct,
    ROUND(AVG(c.roce_percentage), 2) AS avg_roce_pct
FROM sectors s
JOIN companies c ON s.company_id = c.id
GROUP BY s.broad_sector
ORDER BY aggregate_weight_pct DESC;

-- Query 3: Top 10 Revenue Generators in FY 2024 (P&L Operations)
SELECT
    c.id AS ticker,
    c.company_name,
    pnl.sales AS revenue_fy24_cr,
    pnl.operating_profit AS ebitda_fy24_cr,
    pnl.opm_percentage AS opm_pct,
    pnl.net_profit AS pat_fy24_cr,
    pnl.eps AS eps_fy24
FROM profitandloss pnl
JOIN companies c ON pnl.company_id = c.id
WHERE pnl.year = '2024'
ORDER BY pnl.sales DESC
LIMIT 10;

-- Query 4: Top 10 Highest Operating Profit Margin (OPM) Companies in FY 2024
SELECT
    c.id AS ticker,
    c.company_name,
    s.broad_sector,
    pnl.sales AS revenue_cr,
    pnl.operating_profit AS ebitda_cr,
    pnl.opm_percentage AS opm_pct
FROM profitandloss pnl
JOIN companies c ON pnl.company_id = c.id
JOIN sectors s ON c.id = s.company_id
WHERE pnl.year = '2024' AND pnl.sales > 1000
ORDER BY pnl.opm_percentage DESC
LIMIT 10;

-- Query 5: Capital Structure & Solvency Analysis (FY 2024)
SELECT
    c.id AS ticker,
    c.company_name,
    bs.equity_capital,
    bs.reserves,
    bs.borrowings,
    bs.total_assets,
    ROUND(CAST(bs.borrowings AS REAL) / NULLIF(bs.equity_capital + bs.reserves, 0), 2) AS debt_to_equity_calc
FROM balancesheet bs
JOIN companies c ON bs.company_id = c.id
WHERE bs.year = '2024'
ORDER BY bs.borrowings DESC
LIMIT 10;

-- Query 6: Cash Flow Quality & Cash Conversion (FY 2024)
SELECT
    c.id AS ticker,
    c.company_name,
    cf.operating_activity AS cfo_cr,
    pnl.net_profit AS pat_cr,
    ROUND(CAST(cf.operating_activity AS REAL) / NULLIF(pnl.net_profit, 0) * 100, 2) AS cash_conversion_pct,
    cf.investing_activity AS cfi_cr,
    cf.financing_activity AS cff_cr,
    cf.net_cash_flow AS net_cash_change_cr
FROM cashflow cf
JOIN profitandloss pnl ON cf.company_id = pnl.company_id AND cf.year = pnl.year
JOIN companies c ON cf.company_id = c.id
WHERE cf.year = '2024' AND pnl.net_profit > 500
ORDER BY cf.operating_activity DESC
LIMIT 10;

-- Query 7: Valuation Multiples & Dividend Yield by Sector (FY 2024)
SELECT
    s.broad_sector,
    COUNT(c.id) AS num_companies,
    ROUND(AVG(mc.pe_ratio), 2) AS avg_pe,
    ROUND(AVG(mc.pb_ratio), 2) AS avg_pb,
    ROUND(AVG(mc.ev_ebitda), 2) AS avg_ev_ebitda,
    ROUND(AVG(mc.dividend_yield_pct), 2) AS avg_dividend_yield_pct
FROM market_cap mc
JOIN sectors s ON mc.company_id = s.company_id
JOIN companies c ON mc.company_id = c.id
WHERE mc.year = '2024'
GROUP BY s.broad_sector
ORDER BY avg_pe DESC;

-- Query 8: Historical Multi-Year Growth Metrics
SELECT
    c.id AS ticker,
    c.company_name,
    a.compounded_sales_growth,
    a.compounded_profit_growth,
    a.stock_price_cagr,
    a.roe
FROM analysis a
JOIN companies c ON a.company_id = c.id
ORDER BY c.id;

-- Query 9: Regulatory Filings Coverage per Company
SELECT
    c.id AS ticker,
    c.company_name,
    COUNT(d.id) AS filing_count,
    MIN(d.year) AS earliest_filing,
    MAX(d.year) AS latest_filing
FROM documents d
JOIN companies c ON d.company_id = c.id
GROUP BY c.id, c.company_name
ORDER BY filing_count DESC
LIMIT 10;

-- Query 10: Stock Price Performance & Volume Statistics (2024 Average)
SELECT
    c.id AS ticker,
    c.company_name,
    ROUND(AVG(sp.close_price), 2) AS avg_close_2024,
    ROUND(MIN(sp.low_price), 2) AS min_low_2024,
    ROUND(MAX(sp.high_price), 2) AS max_high_2024,
    ROUND(AVG(sp.volume), 0) AS avg_monthly_volume
FROM stock_prices sp
JOIN companies c ON sp.company_id = c.id
WHERE sp.date LIKE '2024%'
GROUP BY c.id, c.company_name
ORDER BY avg_monthly_volume DESC
LIMIT 10;

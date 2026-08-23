-- ==============================================================================
-- N100 FINANCIAL INTELLIGENCE PLATFORM — SPRINT 2 RATIO ENGINE VALIDATION SQL
-- Database: nifty100.db (12 Normalized Tables)
-- ==============================================================================

-- 1. Total Row Count Validation (Must be >= 1,100 rows)
SELECT '1. Total Row Count' AS check_name, COUNT(*) AS metric_value, '>= 1100' AS expected
FROM financial_ratios;

-- 2. Total Distinct Companies Count (Must be 92 companies)
SELECT '2. Distinct Companies' AS check_name, COUNT(DISTINCT company_id) AS metric_value, '92' AS expected
FROM financial_ratios;

-- 3. Duplicate Company-Year Check (Must be 0 rows)
SELECT company_id, year, COUNT(*) AS duplicate_count
FROM financial_ratios
GROUP BY company_id, year
HAVING COUNT(*) > 1;

-- 4. Null-Only Columns Check (Confirm all 14+ KPI columns have populated values)
SELECT
    COUNT(*) AS total_rows,
    COUNT(net_profit_margin_pct) AS non_null_npm,
    COUNT(operating_profit_margin_pct) AS non_null_opm,
    COUNT(return_on_equity_pct) AS non_null_roe,
    COUNT(return_on_capital_employed_pct) AS non_null_roce,
    COUNT(return_on_assets_pct) AS non_null_roa,
    COUNT(debt_to_equity) AS non_null_de,
    COUNT(interest_coverage) AS non_null_icr,
    COUNT(free_cash_flow_cr) AS non_null_fcf,
    COUNT(cfo_quality_score) AS non_null_cfo_quality,
    COUNT(capex_intensity_pct) AS non_null_capex_intensity,
    COUNT(revenue_cagr_5yr) AS non_null_rev_cagr_5yr,
    COUNT(pat_cagr_5yr) AS non_null_pat_cagr_5yr,
    COUNT(eps_cagr_5yr) AS non_null_eps_cagr_5yr,
    COUNT(composite_quality_score) AS non_null_quality_score
FROM financial_ratios;

-- 5. Financials Sector Count & Leverage Carve-Out Verification
SELECT
    s.broad_sector,
    COUNT(DISTINCT fr.company_id) AS companies_count,
    SUM(fr.high_leverage_flag) AS high_leverage_flagged_rows
FROM financial_ratios fr
JOIN sectors s ON fr.company_id = s.company_id
WHERE fr.year = '2024'
GROUP BY s.broad_sector;

-- 6. Top 10 High ROE Companies in FY 2024 (Excluding Outliers)
SELECT
    fr.company_id,
    c.company_name,
    s.broad_sector,
    ROUND(fr.return_on_equity_pct, 2) AS roe_pct,
    ROUND(fr.debt_to_equity, 2) AS de_ratio,
    ROUND(fr.revenue_cagr_5yr, 2) AS rev_cagr_5yr_pct
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.id
JOIN sectors s ON fr.company_id = s.company_id
WHERE fr.year = '2024' AND fr.return_on_equity_pct BETWEEN 15.0 AND 150.0
ORDER BY fr.return_on_equity_pct DESC
LIMIT 10;

-- 7. Top 10 ROCE Companies in FY 2024
SELECT
    fr.company_id,
    c.company_name,
    s.broad_sector,
    ROUND(fr.return_on_capital_employed_pct, 2) AS roce_pct,
    ROUND(fr.operating_profit_margin_pct, 2) AS opm_pct
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.id
JOIN sectors s ON fr.company_id = s.company_id
WHERE fr.year = '2024' AND fr.return_on_capital_employed_pct IS NOT NULL
ORDER BY fr.return_on_capital_employed_pct DESC
LIMIT 10;

-- 8. Debt-Free Companies with High Interest Coverage in FY 2024
SELECT
    fr.company_id,
    c.company_name,
    fr.icr_label,
    fr.debt_to_equity,
    fr.interest_coverage
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.id
WHERE fr.year = '2024' AND (fr.debt_to_equity = 0.0 OR fr.icr_label = 'Debt Free')
ORDER BY fr.company_id
LIMIT 10;

-- 9. Top 10 5-Year Revenue Growth Leaders (CAGR 2019-2024)
SELECT
    fr.company_id,
    c.company_name,
    s.broad_sector,
    ROUND(fr.revenue_cagr_5yr, 2) AS revenue_cagr_5yr_pct,
    fr.revenue_cagr_5yr_flag
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.id
JOIN sectors s ON fr.company_id = s.company_id
WHERE fr.year = '2024' AND fr.revenue_cagr_5yr IS NOT NULL
ORDER BY fr.revenue_cagr_5yr DESC
LIMIT 10;

-- 10. Top Free Cash Flow (FCF) Generators in FY 2024
SELECT
    fr.company_id,
    c.company_name,
    ROUND(fr.cash_from_operations_cr, 2) AS cfo_cr,
    ROUND(fr.capex_cr, 2) AS capex_cr,
    ROUND(fr.free_cash_flow_cr, 2) AS fcf_cr,
    fr.cfo_quality_label,
    fr.capex_intensity_label
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.id
WHERE fr.year = '2024' AND fr.free_cash_flow_cr IS NOT NULL
ORDER BY fr.free_cash_flow_cr DESC
LIMIT 10;

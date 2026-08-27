-- ==============================================================================
-- N100 FINANCIAL INTELLIGENCE PLATFORM — SPRINT 3 SCREENER & PEER VALIDATION SQL
-- Database: nifty100.db (12 Normalized Tables + peer_percentiles)
-- ==============================================================================

-- 1. Top 10 Highest Composite Quality Scores
SELECT
    fr.company_id,
    c.company_name,
    s.broad_sector,
    ROUND(fr.composite_quality_score, 2) AS composite_quality_score,
    ROUND(fr.return_on_equity_pct, 2) AS roe_pct,
    ROUND(fr.debt_to_equity, 2) AS de_ratio,
    ROUND(fr.revenue_cagr_5yr, 2) AS rev_cagr_5yr_pct,
    ROUND(fr.cfo_quality_score, 2) AS cfo_quality
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.id
LEFT JOIN sectors s ON fr.company_id = s.company_id
WHERE fr.year = '2024'
ORDER BY fr.composite_quality_score DESC
LIMIT 10;

-- 2. Quality Compounder Preset Validation (ROE > 15%, D/E < 1.0 or Financials, FCF > 0, Rev CAGR 5yr > 10%)
SELECT
    fr.company_id,
    c.company_name,
    s.broad_sector,
    ROUND(fr.return_on_equity_pct, 2) AS roe_pct,
    ROUND(fr.debt_to_equity, 2) AS de_ratio,
    ROUND(fr.free_cash_flow_cr, 2) AS fcf_cr,
    ROUND(fr.revenue_cagr_5yr, 2) AS rev_cagr_5yr_pct,
    ROUND(fr.composite_quality_score, 2) AS composite_score
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.id
LEFT JOIN sectors s ON fr.company_id = s.company_id
WHERE fr.year = '2024'
  AND fr.return_on_equity_pct > 15.0
  AND (fr.debt_to_equity < 1.0 OR s.broad_sector = 'Financials')
  AND fr.free_cash_flow_cr > 0
  AND fr.revenue_cagr_5yr > 10.0
ORDER BY fr.composite_quality_score DESC;

-- 3. Value Pick Preset Validation (P/E < 20, P/B < 3.0, D/E < 2.0 or Financials, Div Yield > 1%)
SELECT
    fr.company_id,
    c.company_name,
    s.broad_sector,
    ROUND(mc.pe_ratio, 2) AS pe_ratio,
    ROUND(mc.pb_ratio, 2) AS pb_ratio,
    ROUND(fr.debt_to_equity, 2) AS de_ratio,
    ROUND(mc.dividend_yield_pct, 2) AS div_yield_pct,
    ROUND(fr.composite_quality_score, 2) AS composite_score
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.id
LEFT JOIN sectors s ON fr.company_id = s.company_id
LEFT JOIN market_cap mc ON fr.company_id = mc.company_id AND fr.year = mc.year
WHERE fr.year = '2024'
  AND mc.pe_ratio < 20.0
  AND mc.pb_ratio < 3.0
  AND (fr.debt_to_equity < 2.0 OR s.broad_sector = 'Financials')
  AND mc.dividend_yield_pct > 1.0
ORDER BY fr.composite_quality_score DESC;

-- 4. Growth Accelerator Preset Validation (PAT CAGR 5yr > 20%, Rev CAGR 5yr > 15%, D/E < 2.0 or Financials)
SELECT
    fr.company_id,
    c.company_name,
    s.broad_sector,
    ROUND(fr.pat_cagr_5yr, 2) AS pat_cagr_5yr_pct,
    ROUND(fr.revenue_cagr_5yr, 2) AS rev_cagr_5yr_pct,
    ROUND(fr.debt_to_equity, 2) AS de_ratio,
    ROUND(fr.composite_quality_score, 2) AS composite_score
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.id
LEFT JOIN sectors s ON fr.company_id = s.company_id
WHERE fr.year = '2024'
  AND fr.pat_cagr_5yr > 20.0
  AND fr.revenue_cagr_5yr > 15.0
  AND (fr.debt_to_equity < 2.0 OR s.broad_sector = 'Financials')
ORDER BY fr.composite_quality_score DESC;

-- 5. Dividend Champion Preset Validation (Div Yield > 2%, Div Payout < 80%, FCF > 0)
SELECT
    fr.company_id,
    c.company_name,
    s.broad_sector,
    ROUND(mc.dividend_yield_pct, 2) AS div_yield_pct,
    ROUND(fr.dividend_payout_ratio_pct, 2) AS payout_pct,
    ROUND(fr.free_cash_flow_cr, 2) AS fcf_cr,
    ROUND(fr.composite_quality_score, 2) AS composite_score
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.id
LEFT JOIN sectors s ON fr.company_id = s.company_id
LEFT JOIN market_cap mc ON fr.company_id = mc.company_id AND fr.year = mc.year
WHERE fr.year = '2024'
  AND mc.dividend_yield_pct > 2.0
  AND fr.dividend_payout_ratio_pct < 80.0
  AND fr.free_cash_flow_cr > 0
ORDER BY fr.composite_quality_score DESC;

-- 6. Debt-Free Blue Chip Preset Validation (D/E <= 0.05, ROE > 12%, Sales > ₹5000 Cr)
SELECT
    fr.company_id,
    c.company_name,
    ROUND(fr.debt_to_equity, 2) AS de_ratio,
    fr.icr_label,
    ROUND(fr.return_on_equity_pct, 2) AS roe_pct,
    ROUND(pnl.sales, 2) AS sales_cr,
    ROUND(fr.composite_quality_score, 2) AS composite_score
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.id
LEFT JOIN profitandloss pnl ON fr.company_id = pnl.company_id AND fr.year = pnl.year
WHERE fr.year = '2024'
  AND (fr.debt_to_equity <= 0.05 OR fr.icr_label = 'Debt Free')
  AND fr.return_on_equity_pct > 12.0
  AND pnl.sales > 5000.0
ORDER BY fr.composite_quality_score DESC;

-- 7. Turnaround Watch Preset Validation (Rev CAGR 3yr > 10%, FCF > 0, D/E 2024 < D/E 2023)
SELECT
    fr24.company_id,
    c.company_name,
    ROUND(fr24.revenue_cagr_3yr, 2) AS rev_cagr_3yr_pct,
    ROUND(fr24.free_cash_flow_cr, 2) AS fcf_2024_cr,
    ROUND(fr23.debt_to_equity, 2) AS de_2023,
    ROUND(fr24.debt_to_equity, 2) AS de_2024,
    ROUND(fr24.composite_quality_score, 2) AS composite_score
FROM financial_ratios fr24
JOIN financial_ratios fr23 ON fr24.company_id = fr23.company_id AND fr23.year = '2023'
JOIN companies c ON fr24.company_id = c.id
WHERE fr24.year = '2024'
  AND fr24.revenue_cagr_3yr > 10.0
  AND fr24.free_cash_flow_cr > 0
  AND fr24.debt_to_equity < fr23.debt_to_equity
ORDER BY fr24.composite_quality_score DESC;

-- 8. Peer Percentiles Table Record Count & Group Summary
SELECT
    peer_group_name,
    COUNT(DISTINCT company_id) AS companies_count,
    COUNT(DISTINCT metric) AS metrics_count,
    COUNT(*) AS total_percentile_records
FROM peer_percentiles
WHERE year = '2024'
GROUP BY peer_group_name
ORDER BY peer_group_name;

-- 9. IT Services Peer Group ROE Percentile Ranking Validation
SELECT
    pp.company_id,
    c.company_name,
    ROUND(pp.value, 2) AS roe_pct,
    ROUND(pp.percentile_rank, 2) AS roe_percentile_rank
FROM peer_percentiles pp
JOIN companies c ON pp.company_id = c.id
WHERE pp.peer_group_name = 'IT Services' AND pp.metric = 'roe' AND pp.year = '2024'
ORDER BY pp.percentile_rank DESC;

-- 10. FMCG Peer Group Valuation & Percentiles
SELECT
    pp.company_id,
    c.company_name,
    pp.metric,
    ROUND(pp.value, 2) AS metric_value,
    ROUND(pp.percentile_rank, 2) AS percentile_rank
FROM peer_percentiles pp
JOIN companies c ON pp.company_id = c.id
WHERE pp.peer_group_name = 'FMCG' AND pp.year = '2024' AND pp.metric IN ('roe', 'roce', 'npm', 'de')
ORDER BY pp.company_id, pp.metric;

-- 11. D/E Inverted Percentile Ranking Validation (Lower D/E = Higher Percentile)
SELECT
    pp.company_id,
    pp.peer_group_name,
    ROUND(pp.value, 3) AS de_ratio,
    ROUND(pp.percentile_rank, 2) AS inverted_de_percentile
FROM peer_percentiles pp
WHERE pp.metric = 'de' AND pp.year = '2024' AND pp.peer_group_name = 'Automobiles'
ORDER BY pp.percentile_rank DESC;

-- 12. Peer Groups Overview vs Benchmark Companies
SELECT
    pg.peer_group_name,
    COUNT(pg.company_id) AS total_peers,
    MAX(CASE WHEN pg.is_benchmark = 1 THEN pg.company_id ELSE NULL END) AS benchmark_company_id,
    MAX(CASE WHEN pg.is_benchmark = 1 THEN c.company_name ELSE NULL END) AS benchmark_company_name
FROM peer_groups pg
LEFT JOIN companies c ON pg.company_id = c.id
GROUP BY pg.peer_group_name
ORDER BY pg.peer_group_name;

# Database Load & Verification Report (Day 02)

**Project:** Bluestock Mutual Fund Capstone — Day 02 Data Cleaning & SQL  
**Generated On:** 2026-08-03  
**Database File:** `database/bluestock_mf.db`  
**Status:** ✅ Successfully Populated & Verified (All 10 Datasets Loaded)  

---

## Executive Summary

The SQLite database `database/bluestock_mf.db` has been fully populated with all **10 cleaned datasets**. It implements a hybrid architecture:
1. **Core Star Schema Tables**: `dim_fund`, `dim_date`, `fact_nav`, `fact_transactions`, `fact_performance`, `fact_aum`.
2. **Auxiliary Dataset Tables**: `stg_monthly_sip_inflows`, `stg_category_inflows`, `stg_industry_folio_count`, `stg_portfolio_holdings`, `stg_benchmark_indices`.

All foreign key constraints were strictly enabled and verified. Zero foreign key violations were returned by `PRAGMA foreign_key_check;`.

---

## Row Count Comparison & Verification Table

| Table Name | Source CSV / Origin | Expected Rows | Inserted DB Rows | Variance | FK Violations | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `dim_fund` | `01_fund_master_cleaned.csv` | 40 | 40 | 0 | 0 | **✅ MATCH** |
| `dim_date` | `Generated from all dataset dates` | 1,340 | 1,340 | 0 | 0 | **✅ MATCH** |
| `fact_nav` | `02_nav_history_cleaned.csv` | 46,000 | 46,000 | 0 | 0 | **✅ MATCH** |
| `fact_transactions` | `08_investor_transactions_cleaned.csv` | 32,778 | 32,778 | 0 | 0 | **✅ MATCH** |
| `fact_performance` | `07_scheme_performance_cleaned.csv` | 40 | 40 | 0 | 0 | **✅ MATCH** |
| `fact_aum` | `03_aum_by_fund_house_cleaned.csv` | 90 | 90 | 0 | 0 | **✅ MATCH** |
| `stg_monthly_sip_inflows` | `04_monthly_sip_inflows_cleaned.csv` | 48 | 48 | 0 | 0 | **✅ MATCH** |
| `stg_category_inflows` | `05_category_inflows_cleaned.csv` | 144 | 144 | 0 | 0 | **✅ MATCH** |
| `stg_industry_folio_count` | `06_industry_folio_count_cleaned.csv` | 21 | 21 | 0 | 0 | **✅ MATCH** |
| `stg_portfolio_holdings` | `09_portfolio_holdings_cleaned.csv` | 322 | 322 | 0 | 0 | **✅ MATCH** |
| `stg_benchmark_indices` | `10_benchmark_indices_cleaned.csv` | 8,050 | 8,050 | 0 | 0 | **✅ MATCH** |

---

## Foreign Key Integrity Verification

- **Command Executed:** `PRAGMA foreign_key_check;`
- **Violations Returned:** `0`
- **Verification Result:** ✅ **100% Referential Integrity Confirmed**.

---

## Table-by-Table Database Loading Summary

- `dim_fund`: 40 rows
- `dim_date`: 1,340 rows
- `fact_nav`: 46,000 rows
- `fact_transactions`: 32,778 rows
- `fact_performance`: 40 rows
- `fact_aum`: 90 rows
- `stg_monthly_sip_inflows`: 48 rows
- `stg_category_inflows`: 144 rows
- `stg_industry_folio_count`: 21 rows
- `stg_portfolio_holdings`: 322 rows
- `stg_benchmark_indices`: 8,050 rows

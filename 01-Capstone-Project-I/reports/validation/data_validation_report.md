# Data Validation Report (Day 02)

**Project:** Bluestock Mutual Fund Capstone — Day 02 Data Cleaning & SQL  
**Generated On:** 2026-08-03  
**Overall Validation Status:** ✅ PASS — READY FOR SQLITE LOADING & STAR SCHEMA IMPLEMENTATION  

---

## Executive Summary

A comprehensive post-cleaning data validation was conducted across all **10 processed datasets** located in `data/processed/`. Every dataset was subjected to structural checks, string whitespace analysis, datatype verifications, key constraint checks, and dataset-specific business logic rules.

### 🚀 Database Readiness Declaration
All 10 cleaned datasets have passed 100% of data quality, referential integrity, and domain constraint checks. The datasets are strictly validated and **READY FOR SQLITE LOADING AND STAR SCHEMA IMPLEMENTATION**.

---

## Overall Validation Summary Table

| Dataset File Name | File Readable | Rows (Raw -> Cleaned) | Duplicates | PK Unique | Dates Valid | Numerics Valid | Whitespace Clean | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `01_fund_master_cleaned.csv` | Yes | 40 -> 40 | 0 | Yes | Yes | Yes | Yes | **✅ PASS** |
| `02_nav_history_cleaned.csv` | Yes | 46,000 -> 46,000 | 0 | Yes | Yes | Yes | Yes | **✅ PASS** |
| `03_aum_by_fund_house_cleaned.csv` | Yes | 90 -> 90 | 0 | Yes | Yes | Yes | Yes | **✅ PASS** |
| `04_monthly_sip_inflows_cleaned.csv` | Yes | 48 -> 48 | 0 | Yes | Yes | Yes | Yes | **✅ PASS** |
| `05_category_inflows_cleaned.csv` | Yes | 144 -> 144 | 0 | Yes | Yes | Yes | Yes | **✅ PASS** |
| `06_industry_folio_count_cleaned.csv` | Yes | 21 -> 21 | 0 | Yes | Yes | Yes | Yes | **✅ PASS** |
| `07_scheme_performance_cleaned.csv` | Yes | 40 -> 40 | 0 | Yes | Yes | Yes | Yes | **✅ PASS** |
| `08_investor_transactions_cleaned.csv` | Yes | 32,778 -> 32,778 | 0 | Yes | Yes | Yes | Yes | **✅ PASS** |
| `09_portfolio_holdings_cleaned.csv` | Yes | 322 -> 322 | 0 | Yes | Yes | Yes | Yes | **✅ PASS** |
| `10_benchmark_indices_cleaned.csv` | Yes | 8,050 -> 8,050 | 0 | Yes | Yes | Yes | Yes | **✅ PASS** |

---

## Dataset-Specific Validation Details

### 1. `01_fund_master_cleaned.csv` — Status: **PASS**

- **Original Raw Rows:** 40
- **Cleaned Processed Rows:** 40
- **Rows Removed:** 0 (Explanation: No invalid/corrupt rows found; 100% valid records retained)
- **Duplicate Rows:** 0
- **Column Naming Standard:** Lowercase with underscores (`snake_case`)

**Specific Rules & Checks Passed:**
- ✅ All structural and data quality checks passed cleanly.

---

### 2. `02_nav_history_cleaned.csv` — Status: **PASS**

- **Original Raw Rows:** 46,000
- **Cleaned Processed Rows:** 46,000
- **Rows Removed:** 0 (Explanation: No invalid/corrupt rows found; 100% valid records retained)
- **Duplicate Rows:** 0
- **Column Naming Standard:** Lowercase with underscores (`snake_case`)

**Specific Rules & Checks Passed:**
- ✅ nav > 0 check PASSED
- ✅ No duplicate (amfi_code, date) check PASSED
- ✅ Sorted by amfi_code then date check PASSED
- ✅ No missing NAV values after ffill check PASSED
- ✅ All structural and data quality checks passed cleanly.

---

### 3. `03_aum_by_fund_house_cleaned.csv` — Status: **PASS**

- **Original Raw Rows:** 90
- **Cleaned Processed Rows:** 90
- **Rows Removed:** 0 (Explanation: No invalid/corrupt rows found; 100% valid records retained)
- **Duplicate Rows:** 0
- **Column Naming Standard:** Lowercase with underscores (`snake_case`)

**Specific Rules & Checks Passed:**
- ✅ All structural and data quality checks passed cleanly.

---

### 4. `04_monthly_sip_inflows_cleaned.csv` — Status: **PASS**

- **Original Raw Rows:** 48
- **Cleaned Processed Rows:** 48
- **Rows Removed:** 0 (Explanation: No invalid/corrupt rows found; 100% valid records retained)
- **Duplicate Rows:** 0
- **Column Naming Standard:** Lowercase with underscores (`snake_case`)

**Specific Rules & Checks Passed:**
- ✅ All structural and data quality checks passed cleanly.

---

### 5. `05_category_inflows_cleaned.csv` — Status: **PASS**

- **Original Raw Rows:** 144
- **Cleaned Processed Rows:** 144
- **Rows Removed:** 0 (Explanation: No invalid/corrupt rows found; 100% valid records retained)
- **Duplicate Rows:** 0
- **Column Naming Standard:** Lowercase with underscores (`snake_case`)

**Specific Rules & Checks Passed:**
- ✅ All structural and data quality checks passed cleanly.

---

### 6. `06_industry_folio_count_cleaned.csv` — Status: **PASS**

- **Original Raw Rows:** 21
- **Cleaned Processed Rows:** 21
- **Rows Removed:** 0 (Explanation: No invalid/corrupt rows found; 100% valid records retained)
- **Duplicate Rows:** 0
- **Column Naming Standard:** Lowercase with underscores (`snake_case`)

**Specific Rules & Checks Passed:**
- ✅ All structural and data quality checks passed cleanly.

---

### 7. `07_scheme_performance_cleaned.csv` — Status: **PASS**

- **Original Raw Rows:** 40
- **Cleaned Processed Rows:** 40
- **Rows Removed:** 0 (Explanation: No invalid/corrupt rows found; 100% valid records retained)
- **Duplicate Rows:** 0
- **Column Naming Standard:** Lowercase with underscores (`snake_case`)

**Specific Rules & Checks Passed:**
- ✅ All return columns numeric check PASSED
- ✅ Risk metrics numeric check PASSED
- ✅ expense_ratio_pct numeric check PASSED
- ✅ expense_ratio_flag exists (Flagged rows count: 0)
- ✅ All structural and data quality checks passed cleanly.

---

### 8. `08_investor_transactions_cleaned.csv` — Status: **PASS**

- **Original Raw Rows:** 32,778
- **Cleaned Processed Rows:** 32,778
- **Rows Removed:** 0 (Explanation: No invalid/corrupt rows found; 100% valid records retained)
- **Duplicate Rows:** 0
- **Column Naming Standard:** Lowercase with underscores (`snake_case`)

**Specific Rules & Checks Passed:**
- ✅ transaction_type contains ONLY ['SIP', 'Lumpsum', 'Redemption'] check PASSED
- ✅ kyc_status contains ONLY ['Verified', 'Pending', 'Rejected'] check PASSED
- ✅ amount_inr > 0 check PASSED
- ✅ transaction_date is valid datetime check PASSED
- ✅ All structural and data quality checks passed cleanly.

---

### 9. `09_portfolio_holdings_cleaned.csv` — Status: **PASS**

- **Original Raw Rows:** 322
- **Cleaned Processed Rows:** 322
- **Rows Removed:** 0 (Explanation: No invalid/corrupt rows found; 100% valid records retained)
- **Duplicate Rows:** 0
- **Column Naming Standard:** Lowercase with underscores (`snake_case`)

**Specific Rules & Checks Passed:**
- ✅ All structural and data quality checks passed cleanly.

---

### 10. `10_benchmark_indices_cleaned.csv` — Status: **PASS**

- **Original Raw Rows:** 8,050
- **Cleaned Processed Rows:** 8,050
- **Rows Removed:** 0 (Explanation: No invalid/corrupt rows found; 100% valid records retained)
- **Duplicate Rows:** 0
- **Column Naming Standard:** Lowercase with underscores (`snake_case`)

**Specific Rules & Checks Passed:**
- ✅ All structural and data quality checks passed cleanly.

---

## Remaining Anomalies & Notes
1. **`04_monthly_sip_inflows_cleaned.csv`**: Contains 12 expected missing values in `yoy_growth_pct` (representing the initial 12 months in 2022 where 2021 historical baseline data was unavailable).
2. **`07_scheme_performance_cleaned.csv`**: `expense_ratio_flag` contains 0 flagged rows (all expense ratios lie within the valid `[0.1, 2.5]` percentage range). `max_drawdown_pct` contains valid negative float values representing drawdown percentage.
3. **`05_category_inflows_cleaned.csv`**: `net_inflow_crore` contains valid negative floats representing net monthly capital outflows.

---

## Recommendations Before Database Loading
1. **SQLite Type Mapping**: Map `int64` to `INTEGER`, `float64` to `REAL`, ISO date strings (`YYYY-MM-DD`) to `TEXT` (or SQLite `DATE` functions), and string columns to `TEXT`.
2. **Primary & Foreign Key Constraints**:
   - Assign `amfi_code` as Primary Key in `01_fund_master`.
   - Set up Composite Keys `(amfi_code, date)` for `02_nav_history`.
   - Generate an auto-incrementing `transaction_id INTEGER PRIMARY KEY` when staging `08_investor_transactions` into SQLite.
3. **Star Schema Architecture**: Use `01_fund_master` and `10_benchmark_indices` as Dimension tables, with `02_nav_history`, `07_scheme_performance`, `08_investor_transactions`, and `09_portfolio_holdings` acting as Fact tables.

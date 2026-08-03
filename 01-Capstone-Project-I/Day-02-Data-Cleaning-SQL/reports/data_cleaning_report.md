# Data Cleaning Summary Report (Day 02)

**Project:** Bluestock Mutual Fund Capstone — Day 02 Data Cleaning & SQL  
**Generated On:** 2026-08-03  
**Status:** Pipeline Execution Complete  

---

## Executive Summary

The automated data cleaning pipeline processed all **10 raw CSV datasets** from `data/raw/` and exported cleaned, normalized versions to `data/processed/`. 

- **Total Original Records Processed:** 87,533
- **Total Cleaned Records Exported:** 87,533
- **Total Invalid / Duplicate Records Removed:** 0
- **Referential Integrity & Schema Readiness:** 100% Verified

---

## Overall Summary Matrix

| Dataset Name | Output File | Original Rows | Cleaned Rows | Rows Removed | Missing Before | Missing After | Duplicates Removed |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `01_fund_master.csv` | `01_fund_master_cleaned.csv` | 40 | 40 | 0 | 0 | 0 | 0 |
| `02_nav_history.csv` | `02_nav_history_cleaned.csv` | 46,000 | 46,000 | 0 | 0 | 0 | 0 |
| `03_aum_by_fund_house.csv` | `03_aum_by_fund_house_cleaned.csv` | 90 | 90 | 0 | 0 | 0 | 0 |
| `04_monthly_sip_inflows.csv` | `04_monthly_sip_inflows_cleaned.csv` | 48 | 48 | 0 | 12 | 12 | 0 |
| `05_category_inflows.csv` | `05_category_inflows_cleaned.csv` | 144 | 144 | 0 | 0 | 0 | 0 |
| `06_industry_folio_count.csv` | `06_industry_folio_count_cleaned.csv` | 21 | 21 | 0 | 0 | 0 | 0 |
| `07_scheme_performance.csv` | `07_scheme_performance_cleaned.csv` | 40 | 40 | 0 | 0 | 0 | 0 |
| `08_investor_transactions.csv` | `08_investor_transactions_cleaned.csv` | 32,778 | 32,778 | 0 | 0 | 0 | 0 |
| `09_portfolio_holdings.csv` | `09_portfolio_holdings_cleaned.csv` | 322 | 322 | 0 | 0 | 0 | 0 |
| `10_benchmark_indices.csv` | `10_benchmark_indices_cleaned.csv` | 8,050 | 8,050 | 0 | 0 | 0 | 0 |

---

## Detailed Cleaning Logs per Dataset

### Dataset 1: `01_fund_master.csv`

- **Target Output:** `data/processed/01_fund_master_cleaned.csv`
- **Original Row Count:** 40
- **Cleaned Row Count:** 40
- **Rows Removed:** 0
- **Missing Values (Before -> After):** 0 -> 0
- **Duplicate Rows Removed:** 0

#### Data Type Conversions Performed:
- Parsed date/month columns: ['launch_date']

#### Validation Checks Passed:
- Standardized column names to lowercase with underscores
- Trimmed leading/trailing whitespace across string columns
- Removed duplicate rows
- Preserved all valid data records

#### Anomalies Flagged / Handled:
- None (0 anomalies flagged)

---

### Dataset 2: `02_nav_history.csv`

- **Target Output:** `data/processed/02_nav_history_cleaned.csv`
- **Original Row Count:** 46,000
- **Cleaned Row Count:** 46,000
- **Rows Removed:** 0
- **Missing Values (Before -> After):** 0 -> 0
- **Duplicate Rows Removed:** 0

#### Data Type Conversions Performed:
- date -> datetime64[ns] -> YYYY-MM-DD

#### Validation Checks Passed:
- nav > 0 validated (invalid count: 0)
- Sorted by amfi_code, date
- Forward-filled missing NAV per amfi_code
- Composite key (amfi_code, date) uniqueness enforced (duplicate keys removed: 0)

#### Anomalies Flagged / Handled:
- None (0 anomalies flagged)

---

### Dataset 3: `03_aum_by_fund_house.csv`

- **Target Output:** `data/processed/03_aum_by_fund_house_cleaned.csv`
- **Original Row Count:** 90
- **Cleaned Row Count:** 90
- **Rows Removed:** 0
- **Missing Values (Before -> After):** 0 -> 0
- **Duplicate Rows Removed:** 0

#### Data Type Conversions Performed:
- Parsed date/month columns: ['date']

#### Validation Checks Passed:
- Standardized column names to lowercase with underscores
- Trimmed leading/trailing whitespace across string columns
- Removed duplicate rows
- Preserved all valid data records

#### Anomalies Flagged / Handled:
- None (0 anomalies flagged)

---

### Dataset 4: `04_monthly_sip_inflows.csv`

- **Target Output:** `data/processed/04_monthly_sip_inflows_cleaned.csv`
- **Original Row Count:** 48
- **Cleaned Row Count:** 48
- **Rows Removed:** 0
- **Missing Values (Before -> After):** 12 -> 12
- **Duplicate Rows Removed:** 0

#### Data Type Conversions Performed:
- Parsed date/month columns: ['month']

#### Validation Checks Passed:
- Standardized column names to lowercase with underscores
- Trimmed leading/trailing whitespace across string columns
- Removed duplicate rows
- Preserved all valid data records

#### Anomalies Flagged / Handled:
- None (0 anomalies flagged)

---

### Dataset 5: `05_category_inflows.csv`

- **Target Output:** `data/processed/05_category_inflows_cleaned.csv`
- **Original Row Count:** 144
- **Cleaned Row Count:** 144
- **Rows Removed:** 0
- **Missing Values (Before -> After):** 0 -> 0
- **Duplicate Rows Removed:** 0

#### Data Type Conversions Performed:
- Parsed date/month columns: ['month']

#### Validation Checks Passed:
- Standardized column names to lowercase with underscores
- Trimmed leading/trailing whitespace across string columns
- Removed duplicate rows
- Preserved all valid data records

#### Anomalies Flagged / Handled:
- None (0 anomalies flagged)

---

### Dataset 6: `06_industry_folio_count.csv`

- **Target Output:** `data/processed/06_industry_folio_count_cleaned.csv`
- **Original Row Count:** 21
- **Cleaned Row Count:** 21
- **Rows Removed:** 0
- **Missing Values (Before -> After):** 0 -> 0
- **Duplicate Rows Removed:** 0

#### Data Type Conversions Performed:
- Parsed date/month columns: ['month']

#### Validation Checks Passed:
- Standardized column names to lowercase with underscores
- Trimmed leading/trailing whitespace across string columns
- Removed duplicate rows
- Preserved all valid data records

#### Anomalies Flagged / Handled:
- None (0 anomalies flagged)

---

### Dataset 7: `07_scheme_performance.csv`

- **Target Output:** `data/processed/07_scheme_performance_cleaned.csv`
- **Original Row Count:** 40
- **Cleaned Row Count:** 40
- **Rows Removed:** 0
- **Missing Values (Before -> After):** 0 -> 0
- **Duplicate Rows Removed:** 0

#### Data Type Conversions Performed:
- Converted 13 return and risk metric columns to numeric float/int types

#### Validation Checks Passed:
- Validated expense_ratio_pct range [0.1, 2.5]
- Added expense_ratio_flag column without deleting anomalous rows
- Validated risk metric columns (Alpha, Beta, Sharpe, Sortino, Std Dev) as numeric

#### Anomalies Flagged / Handled:
- Expense ratio outside [0.1, 2.5] range count: 0

---

### Dataset 8: `08_investor_transactions.csv`

- **Target Output:** `data/processed/08_investor_transactions_cleaned.csv`
- **Original Row Count:** 32,778
- **Cleaned Row Count:** 32,778
- **Rows Removed:** 0
- **Missing Values (Before -> After):** 0 -> 0
- **Duplicate Rows Removed:** 0

#### Data Type Conversions Performed:
- transaction_date -> datetime64[ns] -> YYYY-MM-DD

#### Validation Checks Passed:
- Standardized transaction_type to exact set: ['SIP', 'Lumpsum', 'Redemption']
- Validated amount_inr > 0 (invalid amount count: 0)
- Validated KYC status to exact set: ['Verified', 'Pending', 'Rejected'] (invalid count: 0)
- Trimmed leading/trailing whitespace across string columns

#### Anomalies Flagged / Handled:
- None (0 anomalies flagged)

---

### Dataset 9: `09_portfolio_holdings.csv`

- **Target Output:** `data/processed/09_portfolio_holdings_cleaned.csv`
- **Original Row Count:** 322
- **Cleaned Row Count:** 322
- **Rows Removed:** 0
- **Missing Values (Before -> After):** 0 -> 0
- **Duplicate Rows Removed:** 0

#### Data Type Conversions Performed:
- Parsed date/month columns: ['portfolio_date']

#### Validation Checks Passed:
- Standardized column names to lowercase with underscores
- Trimmed leading/trailing whitespace across string columns
- Removed duplicate rows
- Preserved all valid data records

#### Anomalies Flagged / Handled:
- None (0 anomalies flagged)

---

### Dataset 10: `10_benchmark_indices.csv`

- **Target Output:** `data/processed/10_benchmark_indices_cleaned.csv`
- **Original Row Count:** 8,050
- **Cleaned Row Count:** 8,050
- **Rows Removed:** 0
- **Missing Values (Before -> After):** 0 -> 0
- **Duplicate Rows Removed:** 0

#### Data Type Conversions Performed:
- Parsed date/month columns: ['date']

#### Validation Checks Passed:
- Standardized column names to lowercase with underscores
- Trimmed leading/trailing whitespace across string columns
- Removed duplicate rows
- Preserved all valid data records

#### Anomalies Flagged / Handled:
- None (0 anomalies flagged)

---


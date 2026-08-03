# Data Profiling & Data Quality Report (Day 02)

**Project:** Bluestock Mutual Fund Capstone — Day 02 Data Cleaning & SQL  
**Generated On:** 2026-08-03  
**Target Directory:** `01-Capstone-Project-I/Day-02-Data-Cleaning-SQL/data/raw/`  

---

## Executive Summary

An automated data profiling scan was conducted on all **10 raw CSV datasets** detected in `data/raw/`. Across all datasets, a total of **87,513 records** were inspected. The data overall exhibits high integrity with zero duplicate rows and strong referential integrity (`amfi_code` matches `01_fund_master.csv` across all relational tables). Key data quality issues identified include:
1. **Date Types Stored as Strings**: All date and month columns (`launch_date`, `date`, `month`, `transaction_date`, `portfolio_date`) are currently stored as `object`/`string` types instead of standard SQL `DATE` / `TIMESTAMP` types.
2. **Missing Values**: `04_monthly_sip_inflows.csv` contains 12 missing values in `yoy_growth_pct` (representing the initial 12 months where prior 12-month historical baseline data was unavailable).
3. **Negative Values Context**: `05_category_inflows.csv` contains negative values in `net_inflow_crore` (valid indicator of net monthly capital outflow), and `07_scheme_performance.csv` contains negative values in `max_drawdown_pct` (valid indicator of maximum historical drawdown percentage).
4. **Primary Key Constraints**: Time-series and transaction datasets require composite primary keys or surrogate keys for SQL table design.

---

## Dataset 1: `01_fund_master.csv`

### 1. Metadata & Structure
- **Dataset Name:** `01_fund_master.csv`
- **Shape:** 40 rows × 15 columns
- **Columns & Data Types:**
  | Column Name | Data Type | Missing Count | Unique Values |
  | :--- | :--- | :--- | :--- |
  | `amfi_code` | `int64` | 0 | 40 |
  | `fund_house` | `object` (string) | 0 | 10 |
  | `scheme_name` | `object` (string) | 0 | 40 |
  | `category` | `object` (string) | 0 | 2 |
  | `sub_category` | `object` (string) | 0 | 12 |
  | `plan` | `object` (string) | 0 | 2 |
  | `launch_date` | `object` (string) | 0 | 34 |
  | `benchmark` | `object` (string) | 0 | 10 |
  | `expense_ratio_pct` | `float64` | 0 | 31 |
  | `exit_load_pct` | `float64` | 0 | 3 |
  | `min_sip_amount` | `int64` | 0 | 1 |
  | `min_lumpsum_amount` | `int64` | 0 | 3 |
  | `fund_manager` | `object` (string) | 0 | 29 |
  | `risk_category` | `object` (string) | 0 | 5 |
  | `sebi_category_code` | `object` (string) | 0 | 9 |

- **Duplicate Rows:** 0
- **Candidate Primary Key(s):** `amfi_code` (Unique 40/40), `scheme_name` (Unique 40/40)
- **Candidate Foreign Key(s):** Referenced by `02_nav_history`, `07_scheme_performance`, `08_investor_transactions`, and `09_portfolio_holdings` on `amfi_code`.

### 2. Data Quality Issues Identified
- **Date Format:** `launch_date` is formatted as string (`YYYY-MM-DD`) instead of SQL `DATE`.
- **Low Variance Columns:** `min_sip_amount` is constant (`₹500` across all 40 schemes).

### 3. Recommended Cleaning Actions
- Convert `launch_date` to `DATE` type.
- Enforce `amfi_code` as Primary Key with `NOT NULL UNIQUE` constraint.
- Normalize `fund_house`, `category`, and `risk_category` string encodings.

---

## Dataset 2: `02_nav_history.csv`

### 1. Metadata & Structure
- **Dataset Name:** `02_nav_history.csv`
- **Shape:** 46,000 rows × 3 columns
- **Columns & Data Types:**
  | Column Name | Data Type | Missing Count | Unique Values |
  | :--- | :--- | :--- | :--- |
  | `amfi_code` | `int64` | 0 | 40 |
  | `date` | `object` (string) | 0 | 1,150 |
  | `nav` | `float64` | 0 | 45,594 |

- **Duplicate Rows:** 0
- **Candidate Primary Key(s):** Composite Key (`amfi_code`, `date`)
- **Candidate Foreign Key(s):** `amfi_code` -> `01_fund_master(amfi_code)` (100% referential integrity verified)

### 2. Data Quality Issues Identified
- **Date Format:** `date` column stored as string (`YYYY-MM-DD`), ranging from `2022-01-03` to `2026-05-29`.
- **High Volume:** 46,000 daily historical NAV records across 40 mutual fund schemes (1,150 trading days per scheme).

### 3. Recommended Cleaning Actions
- Cast `date` to SQL `DATE` data type.
- Index composite key (`amfi_code`, `date`) for high-performance time-series lookup.
- Validate `nav > 0` non-negative constraint.

---

## Dataset 3: `03_aum_by_fund_house.csv`

### 1. Metadata & Structure
- **Dataset Name:** `03_aum_by_fund_house.csv`
- **Shape:** 90 rows × 5 columns
- **Columns & Data Types:**
  | Column Name | Data Type | Missing Count | Unique Values |
  | :--- | :--- | :--- | :--- |
  | `date` | `object` (string) | 0 | 9 |
  | `fund_house` | `object` (string) | 0 | 10 |
  | `aum_lakh_crore` | `float64` | 0 | 82 |
  | `aum_crore` | `int64` | 0 | 82 |
  | `num_schemes` | `int64` | 0 | 10 |

- **Duplicate Rows:** 0
- **Candidate Primary Key(s):** Composite Key (`date`, `fund_house`)
- **Candidate Foreign Key(s):** `fund_house` -> `01_fund_master(fund_house)`

### 2. Data Quality Issues Identified
- **Date Format:** `date` stored as string (`YYYY-MM-DD` quarterly snapshot date).
- **Redundant Columns:** `aum_lakh_crore` and `aum_crore` contain redundant info (`aum_crore = aum_lakh_crore * 100,000`).

### 3. Recommended Cleaning Actions
- Convert `date` column to `DATE` type.
- Keep `aum_crore` as primary numeric metric or standardize units.

---

## Dataset 4: `04_monthly_sip_inflows.csv`

### 1. Metadata & Structure
- **Dataset Name:** `04_monthly_sip_inflows.csv`
- **Shape:** 48 rows × 6 columns
- **Columns & Data Types:**
  | Column Name | Data Type | Missing Count | Unique Values |
  | :--- | :--- | :--- | :--- |
  | `month` | `object` (string) | 0 | 48 |
  | `sip_inflow_crore` | `int64` | 0 | 45 |
  | `active_sip_accounts_crore` | `float64` | 0 | 44 |
  | `new_sip_accounts_lakh` | `float64` | 0 | 29 |
  | `sip_aum_lakh_crore` | `float64` | 0 | 48 |
  | `yoy_growth_pct` | `float64` | 12 | 36 |

- **Duplicate Rows:** 0
- **Candidate Primary Key(s):** `month` (Unique 48/48, formatted `YYYY-MM`)
- **Candidate Foreign Key(s):** None (Macro-level industry time-series)

### 2. Data Quality Issues Identified
- **Missing Values:** 12 nulls in `yoy_growth_pct` for months `2022-01` through `2022-12` (due to missing 2021 historical baseline for YoY calculation).
- **Date Format:** `month` formatted as `YYYY-MM` string.

### 3. Recommended Cleaning Actions
- Handle `yoy_growth_pct` missing values explicitly (impute using calculated YoY formula once historical baseline exists or mark as NULL in database schema).
- Convert `month` to standard `DATE` representation (e.g., first day of month `YYYY-MM-01`).

---

## Dataset 5: `05_category_inflows.csv`

### 1. Metadata & Structure
- **Dataset Name:** `05_category_inflows.csv`
- **Shape:** 144 rows × 3 columns
- **Columns & Data Types:**
  | Column Name | Data Type | Missing Count | Unique Values |
  | :--- | :--- | :--- | :--- |
  | `month` | `object` (string) | 0 | 12 |
  | `category` | `object` (string) | 0 | 12 |
  | `net_inflow_crore` | `float64` | 0 | 142 |

- **Duplicate Rows:** 0
- **Candidate Primary Key(s):** Composite Key (`month`, `category`)
- **Candidate Foreign Key(s):** `category` -> `01_fund_master(sub_category)`

### 2. Data Quality Issues Identified
- **Negative Values:** Contains negative numbers in `net_inflow_crore` (valid representations of monthly net capital redemptions/outflows for debt/hybrid categories).
- **Date Format:** `month` stored as `YYYY-MM` string.

### 3. Recommended Cleaning Actions
- Retain negative values for financial accounting accuracy.
- Cast `month` to SQL `DATE`.

---

## Dataset 6: `06_industry_folio_count.csv`

### 1. Metadata & Structure
- **Dataset Name:** `06_industry_folio_count.csv`
- **Shape:** 21 rows × 6 columns
- **Columns & Data Types:**
  | Column Name | Data Type | Missing Count | Unique Values |
  | :--- | :--- | :--- | :--- |
  | `month` | `object` (string) | 0 | 21 |
  | `total_folios_crore` | `float64` | 0 | 21 |
  | `equity_folios_crore` | `float64` | 0 | 21 |
  | `debt_folios_crore` | `float64` | 0 | 21 |
  | `hybrid_folios_crore` | `float64` | 0 | 20 |
  | `others_folios_crore` | `float64` | 0 | 21 |

- **Duplicate Rows:** 0
- **Candidate Primary Key(s):** `month` (Unique 21/21)
- **Candidate Foreign Key(s):** None

### 2. Data Quality Issues Identified
- **Date Format:** `month` stored as `YYYY-MM` string.

### 3. Recommended Cleaning Actions
- Standardize `month` to `DATE`.
- Verify total folios integrity check (`total = equity + debt + hybrid + others`).

---

## Dataset 7: `07_scheme_performance.csv`

### 1. Metadata & Structure
- **Dataset Name:** `07_scheme_performance.csv`
- **Shape:** 40 rows × 19 columns
- **Columns & Data Types:**
  | Column Name | Data Type | Missing Count | Unique Values |
  | :--- | :--- | :--- | :--- |
  | `amfi_code` | `int64` | 0 | 40 |
  | `scheme_name` | `object` (string) | 0 | 40 |
  | `fund_house` | `object` (string) | 0 | 10 |
  | `category` | `object` (string) | 0 | 12 |
  | `plan` | `object` (string) | 0 | 2 |
  | `return_1yr_pct` | `float64` | 0 | 39 |
  | `return_3yr_pct` | `float64` | 0 | 40 |
  | `return_5yr_pct` | `float64` | 0 | 40 |
  | `benchmark_3yr_pct` | `float64` | 0 | 40 |
  | `alpha` | `float64` | 0 | 36 |
  | `beta` | `float64` | 0 | 22 |
  | `sharpe_ratio` | `float64` | 0 | 24 |
  | `sortino_ratio` | `float64` | 0 | 34 |
  | `std_dev_ann_pct` | `float64` | 0 | 9 |
  | `max_drawdown_pct` | `float64` | 0 | 39 |
  | `aum_crore` | `int64` | 0 | 40 |
  | `expense_ratio_pct` | `float64` | 0 | 31 |
  | `morningstar_rating` | `int64` | 0 | 3 |
  | `risk_grade` | `object` (string) | 0 | 5 |

- **Duplicate Rows:** 0
- **Candidate Primary Key(s):** `amfi_code` (Unique 40/40)
- **Candidate Foreign Key(s):** `amfi_code` -> `01_fund_master(amfi_code)` (100% referential integrity verified)

### 2. Data Quality Issues Identified
- **Negative Values:** `max_drawdown_pct` values are negative floats (e.g. -12.4%), representing peak-to-trough decline.

### 3. Recommended Cleaning Actions
- Maintain `amfi_code` as Primary/Foreign Key.
- Ensure risk and return metrics conform to float precision in database tables.

---

## Dataset 8: `08_investor_transactions.csv`

### 1. Metadata & Structure
- **Dataset Name:** `08_investor_transactions.csv`
- **Shape:** 32,778 rows × 13 columns
- **Columns & Data Types:**
  | Column Name | Data Type | Missing Count | Unique Values |
  | :--- | :--- | :--- | :--- |
  | `investor_id` | `object` (string) | 0 | 5,000 |
  | `transaction_date` | `object` (string) | 0 | 516 |
  | `amfi_code` | `int64` | 0 | 40 |
  | `transaction_type` | `object` (string) | 0 | 3 |
  | `amount_inr` | `int64` | 0 | 23,822 |
  | `state` | `object` (string) | 0 | 12 |
  | `city` | `object` (string) | 0 | 24 |
  | `city_tier` | `object` (string) | 0 | 2 |
  | `age_group` | `object` (string) | 0 | 5 |
  | `gender` | `object` (string) | 0 | 2 |
  | `annual_income_lakh` | `float64` | 0 | 804 |
  | `payment_mode` | `object` (string) | 0 | 4 |
  | `kyc_status` | `object` (string) | 0 | 2 |

- **Duplicate Rows:** 0
- **Candidate Primary Key(s):** Requires Auto-Increment Surrogate Key (`transaction_id`)
- **Candidate Foreign Key(s):** `amfi_code` -> `01_fund_master(amfi_code)`

### 2. Data Quality Issues Identified
- **Date Format:** `transaction_date` stored as string (`YYYY-MM-DD`).
- **High Cardinality:** 5,000 unique `investor_id`s across 32,778 transaction records.

### 3. Recommended Cleaning Actions
- Add auto-incrementing `transaction_id` INTEGER PRIMARY KEY for SQL schema.
- Convert `transaction_date` to `DATE`.

---

## Dataset 9: `09_portfolio_holdings.csv`

### 1. Metadata & Structure
- **Dataset Name:** `09_portfolio_holdings.csv`
- **Shape:** 322 rows × 8 columns
- **Columns & Data Types:**
  | Column Name | Data Type | Missing Count | Unique Values |
  | :--- | :--- | :--- | :--- |
  | `amfi_code` | `int64` | 0 | 34 |
  | `stock_symbol` | `object` (string) | 0 | 30 |
  | `stock_name` | `object` (string) | 0 | 30 |
  | `sector` | `object` (string) | 0 | 14 |
  | `weight_pct` | `float64` | 0 | 295 |
  | `market_value_cr` | `float64` | 0 | 322 |
  | `current_price_inr` | `float64` | 0 | 322 |
  | `portfolio_date` | `object` (string) | 0 | 1 |

- **Duplicate Rows:** 0
- **Candidate Primary Key(s):** Composite Key (`amfi_code`, `stock_symbol`)
- **Candidate Foreign Key(s):** `amfi_code` -> `01_fund_master(amfi_code)`

### 2. Data Quality Issues Identified
- **Floating Point Rounding:** Portfolio weight sums per fund exhibit slight rounding discrepancies (e.g., 99.99% or 100.01%).
- **Date Format:** `portfolio_date` stored as `YYYY-MM-DD` string (`2025-12-31`).

### 3. Recommended Cleaning Actions
- Cast `portfolio_date` to SQL `DATE`.
- Verify weight distribution per scheme.

---

## Dataset 10: `10_benchmark_indices.csv`

### 1. Metadata & Structure
- **Dataset Name:** `10_benchmark_indices.csv`
- **Shape:** 8,050 rows × 3 columns
- **Columns & Data Types:**
  | Column Name | Data Type | Missing Count | Unique Values |
  | :--- | :--- | :--- | :--- |
  | `date` | `object` (string) | 0 | 1,150 |
  | `index_name` | `object` (string) | 0 | 7 |
  | `close_value` | `float64` | 0 | 8,027 |

- **Duplicate Rows:** 0
- **Candidate Primary Key(s):** Composite Key (`date`, `index_name`)
- **Candidate Foreign Key(s):** `index_name` -> `01_fund_master(benchmark)`

### 2. Data Quality Issues Identified
- **Date Format:** `date` stored as string (`YYYY-MM-DD`).

### 3. Recommended Cleaning Actions
- Convert `date` to `DATE`.
- Build composite primary key on (`date`, `index_name`).

---

## Overall Summary Matrix of Data Quality Checks

| Dataset Name | Total Rows | Total Cols | Missing Values | Duplicates | Date Cols stored as Str | Key Issues & Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `01_fund_master.csv` | 40 | 15 | 0 | 0 | `launch_date` | Clean master table; `amfi_code` PK |
| `02_nav_history.csv` | 46,000 | 3 | 0 | 0 | `date` | Large time series; FK verified |
| `03_aum_by_fund_house.csv` | 90 | 5 | 0 | 0 | `date` | Quarterly snapshots; redundant AUM col |
| `04_monthly_sip_inflows.csv` | 48 | 6 | 12 | 0 | `month` | 12 nulls in `yoy_growth_pct` (missing 2021 baseline) |
| `05_category_inflows.csv` | 144 | 3 | 0 | 0 | `month` | Valid negative net inflows (outflows) |
| `06_industry_folio_count.csv` | 21 | 6 | 0 | 0 | `month` | Monthly industry folios breakdown |
| `07_scheme_performance.csv` | 40 | 19 | 0 | 0 | None | Max drawdown is negative float |
| `08_investor_transactions.csv` | 32,778 | 13 | 0 | 0 | `transaction_date` | Needs surrogate `transaction_id` PK |
| `09_portfolio_holdings.csv` | 322 | 8 | 0 | 0 | `portfolio_date` | Stock holding weights ~100% |
| `10_benchmark_indices.csv` | 8,050 | 3 | 0 | 0 | `date` | Benchmark index daily closing levels |

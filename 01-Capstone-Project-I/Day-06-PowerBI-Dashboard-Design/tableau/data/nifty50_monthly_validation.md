# NIFTY 50 Monthly Close Dataset Validation Report

- **Generation Timestamp**: 2026-08-19  
- **Source File**: [`Day-02-Data-Cleaning-SQL/data/processed/10_benchmark_indices_cleaned.csv`](file:///Users/shubham/Documents/Bluestock/01-Capstone-Project-I/Day-02-Data-Cleaning-SQL/data/processed/10_benchmark_indices_cleaned.csv)  
- **Output File**: [`Day-06-PowerBI-Dashboard-Design/tableau/data/10_nifty50_monthly_close.csv`](file:///Users/shubham/Documents/Bluestock/01-Capstone-Project-I/Day-06-PowerBI-Dashboard-Design/tableau/data/10_nifty50_monthly_close.csv)  
- **Status**: **PASSED (100% VALIDATED)**

---

## 1. Executive Validation Checklist

| Check Item | Requirement | Actual Value / Result | Status |
|---|---|---|---|
| **Index Filtering** | `index_name == 'NIFTY50'` | Only NIFTY50 records ingested | **PASS** |
| **Date Horizon** | `2022-01` to `2025-12` | Exactly 48 calendar months | **PASS** |
| **Row Count** | Exactly 48 rows (1 per month) | 48 data rows | **PASS** |
| **Month-End Date Rule** | Last active trading date per month | Verified for all 48 months | **PASS** |
| **Duplicate Months** | 0 duplicate months | 0 duplicates found | **PASS** |
| **Missing / Null Values** | 0 null values across all columns | 0 nulls found | **PASS** |
| **First Record** | `2022-01` (Jan 31, 2022) | `2022-01-31` \| Close: `18615.38` | **PASS** |
| **Last Record** | `2025-12` (Dec 31, 2025) | `2025-12-31` \| Close: `18654.07` | **PASS** |
| **December 2025 Target** | `18654.07` | `18654.07` | **EXACT MATCH** |

---

## 2. Sample Data Audit

### First 5 Rows (2022)
```text
month,last_trading_date,nifty50_month_end_close
2022-01,2022-01-31,18615.38
2022-02,2022-02-28,18865.93
2022-03,2022-03-31,19775.28
2022-04,2022-04-29,19985.01
2022-05,2022-05-31,18935.90
```

### Last 5 Rows (2025)
```text
month,last_trading_date,nifty50_month_end_close
2025-08,2025-08-29,20633.24
2025-09,2025-09-30,20031.45
2025-10,2025-10-31,19634.35
2025-11,2025-11-28,19187.01
2025-12,2025-12-31,18654.07
```

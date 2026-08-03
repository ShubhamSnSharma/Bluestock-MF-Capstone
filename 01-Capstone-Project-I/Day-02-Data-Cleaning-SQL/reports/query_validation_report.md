# Analytical Query Validation Report (Day 02)

**Project:** Bluestock Mutual Fund Capstone — Day 02 Data Cleaning & SQL  
**Generated On:** 2026-08-03  
**Target Database:** `database/bluestock_mf.db`  
**Overall Query Validation Status:** ✅ PASS — ALL 10 QUERIES EXECUTED SUCCESSFULLY  

---

## Executive Summary

All **10 analytical SQL queries** from `sql/queries.sql` were executed directly against `database/bluestock_mf.db`. Every query returned expected data results without syntax errors or runtime exceptions.

---

## Query Execution Summary Table

| Query # | Title / Business Question | Execution Status | Rows Returned | Target Tables |
| :---: | :--- | :---: | :---: | :--- |
| 1 | Top 5 Mutual Funds (AMCs) by Latest Available AUM | **✅ PASS** | 5 | `bluestock_mf.db` | 
| 2 | Average Monthly NAV Trend Across All Schemes | **✅ PASS** | 53 | `bluestock_mf.db` | 
| 3 | Year-over-Year (YoY) SIP Growth Trend | **✅ PASS** | 4 | `bluestock_mf.db` | 
| 4 | Investor Transactions Aggregated by State | **✅ PASS** | 12 | `bluestock_mf.db` | 
| 5 | Mutual Fund Schemes with Expense Ratio Below 1.0% | **✅ PASS** | 14 | `bluestock_mf.db` | 
| 6 | Top 10 Mutual Fund Schemes by Historical Average NAV | **✅ PASS** | 10 | `bluestock_mf.db` | 
| 7 | Highest Performing Mutual Fund Schemes Based on 5-Year Return (%) | **✅ PASS** | 10 | `bluestock_mf.db` | 
| 8 | Monthly Retail Investor Transaction Volume & Capital Flow Trend | **✅ PASS** | 51 | `bluestock_mf.db` | 
| 9 | Average Transaction Amount by Investment Type (SIP vs Lumpsum vs Redemption) | **✅ PASS** | 3 | `bluestock_mf.db` | 
| 10 | Top Benchmark Indices by Historical Average Closing Value | **✅ PASS** | 7 | `bluestock_mf.db` | 

---

## Detailed Query Validation & Sample Results

### Query 1: Top 5 Mutual Funds (AMCs) by Latest Available AUM

- **Business Purpose:** Identify the top 5 Asset Management Companies (fund houses)
- **Execution Status:** **PASS**
- **Rows Returned:** 5

```sql
SELECT 
    fund_house,
    aum_crore AS latest_aum_crore,
    num_schemes AS active_schemes
FROM fact_aum
WHERE date_key = (SELECT MAX(date_key) FROM fact_aum)
ORDER BY aum_crore DESC
LIMIT 5
```

**Sample Output Record:**
```json
{
  "fund_house": "SBI Mutual Fund",
  "latest_aum_crore": 1250000,
  "active_schemes": 186
}
```

---

### Query 2: Average Monthly NAV Trend Across All Schemes

- **Business Purpose:** Compute monthly average Net Asset Value (NAV) across all mutual
- **Execution Status:** **PASS**
- **Rows Returned:** 53

```sql
SELECT 
    d.year,
    d.month,
    d.month_name,
    ROUND(AVG(f.nav), 2) AS average_nav
FROM fact_nav f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year ASC, d.month ASC
```

**Sample Output Record:**
```json
{
  "year": 2022,
  "month": 1,
  "month_name": "January",
  "average_nav": 207.06
}
```

---

### Query 3: Year-over-Year (YoY) SIP Growth Trend

- **Business Purpose:** Calculate average monthly SIP inflows and YoY growth rate
- **Execution Status:** **PASS**
- **Rows Returned:** 4

```sql
SELECT 
    SUBSTR(month, 1, 4) AS year,
    ROUND(AVG(sip_inflow_crore), 2) AS average_monthly_sip_crore,
    ROUND(AVG(yoy_growth_pct), 2) AS average_yoy_growth_pct
FROM stg_monthly_sip_inflows
GROUP BY SUBSTR(month, 1, 4)
ORDER BY year ASC
```

**Sample Output Record:**
```json
{
  "year": "2022",
  "average_monthly_sip_crore": 12453.08,
  "average_yoy_growth_pct": null
}
```

---

### Query 4: Investor Transactions Aggregated by State

- **Business Purpose:** Analyze geographic distribution of retail investments to determine
- **Execution Status:** **PASS**
- **Rows Returned:** 12

```sql
SELECT 
    state,
    COUNT(transaction_id) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC
```

**Sample Output Record:**
```json
{
  "state": "Punjab",
  "transaction_count": 2965,
  "total_amount_inr": 315780459.0
}
```

---

### Query 5: Mutual Fund Schemes with Expense Ratio Below 1.0%

- **Business Purpose:** Filter low-cost, cost-efficient mutual fund schemes with TER < 1.0%.
- **Execution Status:** **PASS**
- **Rows Returned:** 14

```sql
SELECT 
    scheme_name AS fund_name,
    fund_house,
    expense_ratio_pct AS expense_ratio
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC
```

**Sample Output Record:**
```json
{
  "fund_name": "Nippon India Gilt Securities Fund - Regular - Growth",
  "fund_house": "Nippon India MF",
  "expense_ratio": 0.55
}
```

---

### Query 6: Top 10 Mutual Fund Schemes by Historical Average NAV

- **Business Purpose:** Rank the top 10 schemes with the highest average daily unit values.
- **Execution Status:** **PASS**
- **Rows Returned:** 10

```sql
SELECT 
    d.amfi_code,
    d.scheme_name,
    d.fund_house,
    ROUND(AVG(n.nav), 2) AS average_nav
FROM fact_nav n
JOIN dim_fund d ON n.amfi_code = d.amfi_code
GROUP BY d.amfi_code, d.scheme_name, d.fund_house
ORDER BY average_nav DESC
LIMIT 10
```

**Sample Output Record:**
```json
{
  "amfi_code": 120844,
  "scheme_name": "Kotak Liquid Fund - Regular - Growth",
  "fund_house": "Kotak Mahindra MF",
  "average_nav": 3705.88
}
```

---

### Query 7: Highest Performing Mutual Fund Schemes Based on 5-Year Return (%)

- **Business Purpose:** Identify long-term wealth generators based on 5-year annualized returns.
- **Execution Status:** **PASS**
- **Rows Returned:** 10

```sql
SELECT 
    d.amfi_code,
    d.scheme_name,
    d.fund_house,
    d.category,
    p.return_5yr_pct
FROM fact_performance p
JOIN dim_fund d ON p.amfi_code = d.amfi_code
ORDER BY p.return_5yr_pct DESC
LIMIT 10
```

**Sample Output Record:**
```json
{
  "amfi_code": 101207,
  "scheme_name": "ABSL Small Cap Fund - Regular - Growth",
  "fund_house": "Aditya Birla Sun Life MF",
  "category": "Equity",
  "return_5yr_pct": 23.8
}
```

---

### Query 8: Monthly Retail Investor Transaction Volume & Capital Flow Trend

- **Business Purpose:** Track monthly transaction counts and monetary volumes by transaction type.
- **Execution Status:** **PASS**
- **Rows Returned:** 51

```sql
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
ORDER BY dt.year ASC, dt.month ASC, t.transaction_type ASC
```

**Sample Output Record:**
```json
{
  "year": 2024,
  "month": 1,
  "month_name": "January",
  "transaction_type": "Lumpsum",
  "transaction_count": 492,
  "total_volume_inr": 125509831.0
}
```

---

### Query 9: Average Transaction Amount by Investment Type (SIP vs Lumpsum vs Redemption)

- **Business Purpose:** Compare ticket sizes across investment modes (SIP vs Lumpsum vs Redemption).
- **Execution Status:** **PASS**
- **Rows Returned:** 3

```sql
SELECT 
    transaction_type,
    COUNT(transaction_id) AS transaction_count,
    ROUND(AVG(amount_inr), 2) AS average_amount_inr,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY transaction_type
ORDER BY average_amount_inr DESC
```

**Sample Output Record:**
```json
{
  "transaction_type": "Lumpsum",
  "transaction_count": 8095,
  "average_amount_inr": 254456.02,
  "total_amount_inr": 2059821448.0
}
```

---

### Query 10: Top Benchmark Indices by Historical Average Closing Value

- **Business Purpose:** Compare market benchmark performance and index levels.
- **Execution Status:** **PASS**
- **Rows Returned:** 7

```sql
SELECT 
    index_name,
    ROUND(AVG(close_value), 2) AS average_close_value,
    ROUND(MIN(close_value), 2) AS min_close_value,
    ROUND(MAX(close_value), 2) AS max_close_value
FROM stg_benchmark_indices
GROUP BY index_name
ORDER BY average_close_value DESC
```

**Sample Output Record:**
```json
{
  "index_name": "BSE_SMALLCAP",
  "average_close_value": 39375.03,
  "min_close_value": 23592.64,
  "max_close_value": 79075.39
}
```

---


# Tableau Calculated Fields & KPI Formulas Reference

This document provides the complete syntax for all Tableau calculated fields, Level of Detail (LOD) expressions, and percentage transformations required across the 4 dashboard pages.

---

## 1. Page 1: Industry Overview Calculated Fields

### 1.1 Latest Top-10 AMC AUM (Lakh Crore)
- **Data Source**: `03_aum_by_fund_house_cleaned.csv`
- **Formula**:
  ```tableau
  // Field Name: [Latest Top 10 AMC AUM (Lakh Cr)]
  { FIXED : SUM(IF [date] = {FIXED : MAX([date])} THEN [aum_lakh_crore] END) }
  ```
- **Format**: `Number (Custom)`: Prefix `₹`, Suffix `L Cr`, 2 Decimals (Result: `₹62.74L Cr`).
- **Dashboard Labeling**:
  - Primary Card Value: **₹62.74L Cr**
  - Card Title: **Top 10 AMC AUM**
  - Subtitle / Note: *Assignment benchmark: ~₹81L Cr industry-wide*

### 1.2 Latest Monthly SIP Inflow (Crore)
- **Data Source**: `04_monthly_sip_inflows_cleaned.csv`
- **Formula**:
  ```tableau
  // Field Name: [Latest Monthly SIP Inflow (Cr)]
  { FIXED : SUM(IF [month] = {FIXED : MAX([month])} THEN [sip_inflow_crore] END) }
  ```
- **Format**: `Number (Custom)`: Prefix `₹`, Suffix ` Cr`, 0 Decimals (Result: `₹31,002 Cr` / `₹31.0K Cr`).
- **Card Title**: **Monthly SIP Inflow (Dec 2025)**

### 1.3 Latest Total Folio Count (Crore)
- **Data Source**: `06_industry_folio_count_cleaned.csv`
- **Formula**:
  ```tableau
  // Field Name: [Latest Total Folios (Cr)]
  { FIXED : SUM(IF [month] = {FIXED : MAX([month])} THEN [total_folios_crore] END) }
  ```
- **Format**: `Number (Custom)`: Suffix ` Cr`, 2 Decimals (Result: `26.12 Cr`).
- **Card Title**: **Industry Folios (Dec 2025)**

### 1.4 Industry Schemes Count
- **Data Source**: `03_aum_by_fund_house_cleaned.csv`
- **Formula**:
  ```tableau
  // Field Name: [Total Schemes (Top 10 AMC)]
  { FIXED : SUM(IF [date] = {FIXED : MAX([date])} THEN [num_schemes] END) }
  ```
- **Format**: `Number (Standard)`: `#,##0` (Result: `1,522`).
- **Dashboard Labeling**:
  - Primary Card Value: **1,522**
  - Card Title: **Top 10 AMC Schemes**
  - Subtitle / Note: *Assignment benchmark: 1,908 industry-wide (Portfolio sample: 40)*

---

## 2. Page 2: Fund Performance Calculated Fields

### 2.1 Return (3-Year CAGR %)
- **Data Source**: `07_scheme_performance_cleaned.csv`
- **Formula**:
  ```tableau
  // Field Name: [Return 3Y (%)]
  [return_3yr_pct] / 100.0
  ```
- **Format**: `Percentage` (2 Decimals, e.g. `12.36%`).

### 2.2 Annualized Risk (Volatility / Std Dev %)
- **Data Source**: `07_scheme_performance_cleaned.csv`
- **Formula**:
  ```tableau
  // Field Name: [Volatility StdDev (%)]
  [std_dev_ann_pct] / 100.0
  ```
- **Format**: `Percentage` (2 Decimals, e.g. `14.50%`).

### 2.3 Alpha (%)
- **Data Source**: `07_scheme_performance_cleaned.csv`
- **Formula**:
  ```tableau
  // Field Name: [Alpha (%)]
  [alpha] / 100.0
  ```
- **Format**: `Percentage` (2 Decimals, e.g. `0.87%`).

### 2.4 Max Drawdown (%)
- **Data Source**: `07_scheme_performance_cleaned.csv`
- **Formula**:
  ```tableau
  // Field Name: [Max Drawdown (%)]
  [max_drawdown_pct] / 100.0
  ```
- **Format**: `Percentage` (2 Decimals, e.g. `-21.70%`).

### 2.5 Sharpe Ratio & Sortino Ratio
- **Data Source**: `07_scheme_performance_cleaned.csv`
- **Formulas**:
  ```tableau
  // Field Name: [Sharpe Ratio]
  [sharpe_ratio]

  // Field Name: [Sortino Ratio]
  [sortino_ratio]
  ```
- **Format**: `Number (Custom)` (2 Decimals).

---

## 3. Page 3: Investor Analytics Calculated Fields

### 3.1 Average SIP Amount (INR)
- **Data Source**: `08_investor_transactions_cleaned.csv`
- **Formula**:
  ```tableau
  // Field Name: [Average SIP Amount (INR)]
  AVG(IF UPPER(TRIM([transaction_type])) = 'SIP' THEN [amount_inr] END)
  ```
- **Format**: `Currency (Custom)`: Prefix `₹`, 0 Decimals.

### 3.2 Total Investment Amount
- **Data Source**: `08_investor_transactions_cleaned.csv`
- **Formula**:
  ```tableau
  // Field Name: [Total Amount (INR)]
  SUM([amount_inr])
  ```
- **Format**: `Currency (Custom)`: Prefix `₹`, in Crores or Lakhs.

### 3.3 Transaction Type Percentage Share
- **Data Source**: `08_investor_transactions_cleaned.csv`
- **Formula**:
  ```tableau
  // Field Name: [Transaction Amount Share (%)]
  SUM([amount_inr]) / TOTAL(SUM([amount_inr]))
  ```
- **Format**: `Percentage` (1 Decimal, e.g. `58.4%`).

### 3.4 Monthly Transaction Volume
- **Data Source**: `08_investor_transactions_cleaned.csv`
- **Formula**:
  ```tableau
  // Field Name: [Transaction Volume]
  COUNT([investor_id])
  ```

---

## 4. Page 4: SIP & Market Trends Calculated Fields

### 4.1 Month-Date Conversion
- **Data Source**: `04_monthly_sip_inflows_cleaned.csv`, `05_category_inflows_cleaned.csv`
- **Formula**:
  ```tableau
  // Field Name: [Month Date]
  DATE(DATEPARSE('yyyy-MM', [month]))
  ```

### 4.2 NIFTY 50 Actual Month-End Close (Corrected LOD)
- **Data Source**: `10_benchmark_indices_cleaned.csv`
- **Description**: Returns the **actual closing price on the last available trading day of each month**, rather than an average of daily closes.
- **Formula**:
  ```tableau
  // Field Name: [NIFTY 50 Month-End Close]
  { FIXED DATETRUNC('month', [date]) : 
      MAX(IF [index_name] = 'NIFTY50' AND [date] = { FIXED DATETRUNC('month', [date]), [index_name] : MAX([date]) } THEN [close_value] END)
  }
  ```
- **Format**: `Number (Custom)`: `#,##0.00` (e.g. `18,654.07` on Dec 31, 2025).

### 4.3 FY25 Category Net Inflow (INR Crore)
- **Data Source**: `05_category_inflows_cleaned.csv`
- **Description**: Evaluates total net inflows at the category level specifically for Fiscal Year 2025 (April 2024 to March 2025).
- **Formula**:
  ```tableau
  // Field Name: [FY25 Category Net Inflow (Cr)]
  { FIXED [category] : 
      SUM(IF [month] >= '2024-04' AND [month] <= '2025-03' THEN [net_inflow_crore] ELSE 0 END)
  }
  ```
- **Format**: `Number (Custom)`: Prefix `₹`, Suffix ` Cr`, 0 Decimals.

### 4.4 Top 5 Categories Rank Filter (FY25)
- **Data Source**: `05_category_inflows_cleaned.csv`
- **Formula**:
  ```tableau
  // Field Name: [Is Top 5 Category FY25]
  RANK_UNIQUE([FY25 Category Net Inflow (Cr)], 'desc') <= 5
  ```
- **Usage**: Apply as Filter on the Category bar chart, selecting `True`.

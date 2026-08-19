# Tableau Semantic Data Model & Architecture Specification

---

## 1. Overview & Architecture Strategy

In Tableau Desktop / Tableau Public, connecting multiple fact tables of differing temporal and dimensional granularities via **physical joins** causes severe row multiplication and Cartesian aggregation errors (e.g. joining daily NAV records to quarterly AUM or transaction logs).

To prevent data inflation and ensure optimal workbook performance, this implementation uses **Tableau Logical Layer Relationships (Noodles)** and separate clean Data Sources tailored to the visual requirements of each dashboard page.

```text
Tableau Data Model Architecture
├── Data Source 1: Fund Performance & NAV (Pages 2 & Drillthrough)
│   ├── Dim_FundMaster (Root Logical Table)
│   ├── Dim_SchemePerformance (Related 1:1 on amfi_code)
│   └── Fact_NAVHistory (Related 1:N on amfi_code)
│
├── Data Source 2: Investor Analytics (Page 3)
│   ├── Fact_InvestorTransactions (Root Logical Table)
│   └── Dim_FundMaster (Related N:1 on amfi_code)
│
├── Data Source 3: Industry Overview & AUM (Page 1)
│   ├── Fact_AUMByFundHouse (Root Logical Table)
│   ├── Fact_MonthlySIPInflows (Independent Table / Relationship)
│   └── Fact_IndustryFolioCount (Independent Table / Relationship)
│
└── Data Source 4: SIP & Market Trends (Page 4)
    ├── Fact_MonthlySIPInflows (Root Logical Table)
    ├── Fact_CategoryInflows (Related on month)
    └── Fact_BenchmarkIndices_Monthly (Related on month)
```

---

## 2. Table Specifications & Granularity Matrix

| Ingested Table | Source CSV Filename | Granularity (Grain) | Key Dimensional Roles | Keys |
|---|---|---|---|---|
| `Dim_FundMaster` | `01_fund_master_cleaned.csv` | 1 row per scheme | Fund House, Scheme Name, Category, Plan, Benchmark | `amfi_code` (PK) |
| `Dim_SchemePerformance` | `07_scheme_performance_cleaned.csv` | 1 row per scheme | Returns (1Y, 3Y, 5Y), Alpha, Beta, Sharpe, Sortino, Drawdown | `amfi_code` (PK/FK) |
| `Fact_NAVHistory` | `02_nav_history_cleaned.csv` | 1 row per Scheme per Date | NAV, Date | `amfi_code` (FK), `date` (Date) |
| `Fact_InvestorTransactions` | `08_investor_transactions_cleaned.csv` | 1 row per Transaction | Transaction Type, State, City, City Tier, Age Group, Gender | `investor_id`, `amfi_code`, `transaction_date` |
| `Fact_AUMByFundHouse` | `03_aum_by_fund_house_cleaned.csv` | 1 row per AMC per Date | Fund House, AUM (Lakh Cr & Cr), Schemes Count | `fund_house`, `date` |
| `Fact_MonthlySIPInflows` | `04_monthly_sip_inflows_cleaned.csv` | 1 row per Month | Monthly SIP Inflows (Cr), Active SIP Accounts (Cr) | `month` (`YYYY-MM`) |
| `Fact_CategoryInflows` | `05_category_inflows_cleaned.csv` | 1 row per Category per Month | Category, Net Inflow (Cr) | `month`, `category` |
| `Fact_IndustryFolioCount` | `06_industry_folio_count_cleaned.csv` | 1 row per Month | Total Folios (Cr), Equity/Debt/Hybrid Folios | `month` (`YYYY-MM`) |
| `Fact_BenchmarkIndices` | `10_benchmark_indices_cleaned.csv` | 1 row per Index per Date | Index Name (NIFTY50, etc.), Close Value | `index_name`, `date` |

---

## 3. Detailed Logical Relationship Specifications

### Data Source 1: Fund Performance & Scorecard (For Page 2)
- **Root Table**: `01_fund_master_cleaned.csv` (`Dim_FundMaster`)
- **Relationship 1**: Link to `07_scheme_performance_cleaned.csv` (`Dim_SchemePerformance`)
  - Join Clause: `Dim_FundMaster.amfi_code = Dim_SchemePerformance.amfi_code`
  - Cardinality: $1 : 1$
- **Relationship 2**: Link to `02_nav_history_cleaned.csv` (`Fact_NAVHistory`)
  - Join Clause: `Dim_FundMaster.amfi_code = Fact_NAVHistory.amfi_code`
  - Cardinality: $1 : N$
- **Relationship 3 (Optional for Benchmark Line)**: Link to `10_benchmark_indices_cleaned.csv`
  - Join Clause: `Fact_NAVHistory.date = Fact_BenchmarkIndices.date`
  - Filter / Condition: `Fact_BenchmarkIndices.index_name = 'NIFTY50'` (or matching benchmark)

### Data Source 2: Investor Transactions & Demographics (For Page 3)
- **Root Table**: `08_investor_transactions_cleaned.csv` (`Fact_InvestorTransactions`)
- **Relationship 1**: Link to `01_fund_master_cleaned.csv` (`Dim_FundMaster`)
  - Join Clause: `Fact_InvestorTransactions.amfi_code = Dim_FundMaster.amfi_code`
  - Cardinality: $N : 1$

### Data Source 3: Industry Macro & AUM (For Page 1)
- **Root Table**: `03_aum_by_fund_house_cleaned.csv` (`Fact_AUMByFundHouse`)
  - Provides AMC-level AUM rankings and industry trend over 2022–2025.
- **Supplemental Tables**:
  - `04_monthly_sip_inflows_cleaned.csv` (Provides monthly SIP peak ₹31,002 Cr)
  - `06_industry_folio_count_cleaned.csv` (Provides latest industry folio count 26.12 Cr)

### Data Source 4: SIP & Market Trends (For Page 4)
- **Root Table**: `04_monthly_sip_inflows_cleaned.csv` (`Fact_MonthlySIPInflows`)
- **Relationship 1**: Link to `05_category_inflows_cleaned.csv` (`Fact_CategoryInflows`)
  - Join Clause: `Fact_MonthlySIPInflows.month = Fact_CategoryInflows.month`
  - Cardinality: $1 : N$
- **Relationship 2**: Link to `10_benchmark_indices_cleaned.csv` (Monthly Aggregated)
  - Date Alignment: Link `Month_Date` of SIP inflows to `Month_Date` of NIFTY 50 benchmark prices.

---

## 4. Date Transformations & Alignment Strategy

Several source files store monthly dates as strings formatted as `YYYY-MM` (e.g. `2024-04` or `2025-12`), while transaction and NAV tables store ISO dates `YYYY-MM-DD`.

### Standardized Date Parse Formulas:

1. **Monthly String to True Date (`04_monthly_sip_inflows`, `05_category_inflows`, `06_industry_folio_count`)**:
   ```tableau
   // Field Name: [Month Date]
   DATE(DATEPARSE('yyyy-MM', [month]))
   ```

2. **Daily Date to Month-Level Date (`10_benchmark_indices`, `02_nav_history`, `08_investor_transactions`)**:
   ```tableau
   // Field Name: [Date Month Level]
   DATETRUNC('month', [date])
   ```

3. **Financial Year FY25 Filter**:
   ```tableau
   // Field Name: [Is FY25]
   [Month Date] >= #2024-04-01# AND [Month Date] <= #2025-03-31#
   ```

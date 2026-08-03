# Bluestock Mutual Fund Capstone
## Day 02: Data Cleaning & SQLite Database Design

This project builds an end-to-end ETL pipeline for mutual fund data analysis. Raw financial and investor datasets are profiled, cleaned, and validated using Python and Pandas. The processed data is loaded into a SQLite star schema database and analyzed through 10 analytical SQL queries.

---

## Objectives

- Profile raw datasets to detect missing values, duplicates, and data type anomalies.
- Clean and standardize data using modular Python Pandas scripts.
- Validate data quality and enforce 100% referential integrity.
- Design an OLAP SQLite star schema database.
- Load cleaned data into SQLite (`bluestock_mf.db`).
- Perform analytical SQL queries for business insights.

---

## Project Workflow

```text
Raw CSV Files
      │
      ▼
Data Profiling
      │
      ▼
Data Cleaning
      │
      ▼
Data Validation
      │
      ▼
SQLite Star Schema
      │
      ▼
Analytical SQL Queries
      │
      ▼
Reports
```

---

## Project Structure

```text
Day-02-Data-Cleaning-SQL/
├── data/
│   ├── raw/               # Raw input CSV datasets
│   └── processed/         # Cleaned CSV datasets
├── database/
│   └── bluestock_mf.db    # SQLite star schema database
├── notebooks/             # Exploratory analysis notebooks
├── reports/               # Documentation & validation reports
├── scripts/               # Python ETL & validation scripts
├── sql/
│   ├── schema.sql         # Database schema DDL
│   └── queries.sql        # 10 Analytical SQL queries
├── README.md              # Project documentation
└── requirements.txt       # Python dependencies
```

---

## Datasets

| Dataset | Purpose |
|---------|---------|
| Fund Master | Mutual fund scheme metadata |
| NAV History | Daily historical NAV values |
| AUM by Fund House | Quarterly fund house AUM metrics |
| Monthly SIP Inflows | Industry monthly SIP inflows & YoY growth |
| Category Inflows | Monthly category net inflows/outflows |
| Industry Folio Count | Industry investor folio counts |
| Scheme Performance | Return metrics & risk ratios |
| Investor Transactions | Retail investor transaction history |
| Portfolio Holdings | Fund constituent stock holdings |
| Benchmark Indices | Daily benchmark index closing levels |

---

## Star Schema

The analytical database follows a star schema architecture composed of two dimension tables (`dim_fund`, `dim_date`) and four fact tables (`fact_nav`, `fact_transactions`, `fact_performance`, `fact_aum`). Supporting staging tables store auxiliary macro metrics and benchmark series.

```text
                             dim_date (Calendar Dimension)
                                 │
       ┌─────────────────────────┼─────────────────────────┐
       │                         │                         │
   fact_nav             fact_transactions              fact_aum
  (Daily NAV)          (Investor Transactions)      (Quarterly AUM)
       │                         │                         │
       └─────────────────────────┼─────────────────────────┘
                                 │
                             dim_fund (Fund Master Dimension)
                                 │
                          fact_performance
                      (Returns & Risk Metrics)
```

---

## How to Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run cleaning pipeline:
   ```bash
   python scripts/run_cleaning_pipeline.py
   ```

3. Validate cleaned data:
   ```bash
   python scripts/validate_cleaned_data.py
   ```

4. Build SQLite database:
   ```bash
   python scripts/build_database.py
   ```

5. Execute SQL queries:
   ```bash
   python scripts/execute_queries.py
   ```

6. Run final verification:
   ```bash
   python scripts/run_final_verification.py
   ```

---

## Deliverables

- 10 cleaned CSV datasets (`data/processed/`)
- SQLite database (`database/bluestock_mf.db`)
- Star schema DDL (`sql/schema.sql`)
- Analytical SQL queries (`sql/queries.sql`)
- Data dictionary (`reports/data_dictionary.md`)
- Validation reports (`reports/`)

---

## Technologies

- Python
- Pandas
- NumPy
- SQLite
- SQLAlchemy
- SQL
- Git

---

## Results

- 10 datasets cleaned and validated
- SQLite star schema successfully implemented
- Zero foreign key violations (`PRAGMA foreign_key_check = 0`)
- 10 analytical SQL queries executed successfully
- End-to-end ETL pipeline completed

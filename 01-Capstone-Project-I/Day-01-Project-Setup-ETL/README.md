# Bluestock Mutual Fund Analytics Capstone – Day 1

This directory contains the **Day 1: Project Setup & Data Ingestion (ETL)** pipeline for the **Bluestock Fintech Mutual Fund Analytics Capstone** as part of the Bluestock internship program.

The project focuses on building a data-driven mutual fund analytics pipeline using Python. Day 1 establishes the core ETL environment, raw data validation, and live NAV data integration.

## Day 1 Progress & Achievements

- Configured the development environment and installed required dependencies.
- Ingested and explored all 10 raw mutual fund market datasets.
- Performed data quality checks:
  - Missing value audits
  - Duplicate record detection
  - Schema and data type validations
- Explored fund master data and verified AMFI scheme codes against NAV history.
- Retrieved live NAV data directly via the MFAPI REST API.
- Stored API-fetched NAV datasets in `data/api/` for downstream processing.

## Project Structure

```text
Day-01-Project-Setup-ETL/
├── data/
│   ├── api/          # Live NAV data fetched from MFAPI
│   └── raw/          # Original market datasets
├── data_ingestion.py # Data ingestion & validation script
├── live_nav_fetch.py # Live NAV fetcher script (MFAPI REST API)
├── requirements.txt  # Python package dependencies
└── README.md         # Day 1 project documentation
```

## Technologies Used

- **Python**
- **Pandas** & **NumPy**
- **Requests** (MFAPI REST Integration)
- **SQLAlchemy**
- **Jupyter Notebook**

## Execution & Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

Run data ingestion and live NAV fetching scripts:
```bash
python data_ingestion.py
python live_nav_fetch.py
```

---

*This milestone forms the data foundation for subsequent Capstone analytics deliverables.*
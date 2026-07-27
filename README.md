# Bluestock Mutual Fund Analytics Capstone

This repository contains my work for the **Bluestock Fintech Mutual Fund Analytics Capstone** as part of the Bluestock internship program.

The project focuses on building a data-driven mutual fund analytics pipeline using Python. Throughout the internship, the project will cover data ingestion, validation, SQL, exploratory data analysis, dashboards, and financial insights.

## Day 1 Progress

- Created the project structure
- Configured the development environment and dependencies
- Loaded and explored all provided datasets
- Performed basic data quality checks
  - Missing values
  - Duplicate records
  - Data types
- Explored the fund master dataset
- Validated AMFI scheme codes against NAV history
- Retrieved live NAV data using the MFAPI
- Saved API-fetched NAV datasets for further analysis

## Project Structure

```
Bluestock-MF-Capstone/
├── dashboard/
├── data/
│   ├── api/          # NAV data fetched from MFAPI
│   ├── processed/    # Cleaned datasets
│   └── raw/          # Original datasets
├── notebooks/
├── reports/
├── sql/
├── data_ingestion.py
├── live_nav_fetch.py
├── requirements.txt
└── README.md
```

## Technologies Used

- Python
- Pandas
- NumPy
- Requests
- SQLAlchemy
- Jupyter Notebook
- Matplotlib
- Plotly

---

*This repository will be updated as new milestones of the Bluestock Mutual Fund Analytics Capstone are completed.*
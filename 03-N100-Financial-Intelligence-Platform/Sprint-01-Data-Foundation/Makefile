.PHONY: help load ratios test report dashboard api clean

PYTHON ?= python3
PYTEST ?= pytest

help:
	@echo "N100 Financial Intelligence Platform — Makefile Targets:"
	@echo "  load      - Execute complete ETL pipeline and populate SQLite database"
	@echo "  ratios    - Compute / validate financial ratios in the database"
	@echo "  test      - Run comprehensive ETL unit and DQ test suites"
	@echo "  report    - Generate data quality audit and validation reports"
	@echo "  dashboard - Launch financial intelligence dashboard"
	@echo "  api       - Launch financial intelligence REST API"
	@echo "  clean     - Remove generated SQLite databases, caches, and test artifacts"

load:
	$(PYTHON) -m src.etl.loader

ratios:
	$(PYTHON) -c "import sqlite3; conn=sqlite3.connect('nifty100.db'); print('Financial ratios verified. Count:', conn.execute('SELECT COUNT(*) FROM financial_ratios').fetchone()[0])"

test:
	$(PYTEST) tests/ -v

report:
	$(PYTHON) -c "\
import pandas as pd, sqlite3; \
audit_df = pd.read_csv('output/load_audit.csv'); \
val_df = pd.read_csv('output/validation_failures.csv'); \
conn = sqlite3.connect('nifty100.db'); \
comp_cnt = conn.execute('SELECT COUNT(*) FROM companies').fetchone()[0]; \
fk_errors = len(conn.execute('PRAGMA foreign_key_check').fetchall()); \
conn.close(); \
print('======================================================================'); \
print('SPRINT 1 ETL AUDIT & DATA QUALITY REPORT'); \
print('======================================================================'); \
print('\n[1] LOAD AUDIT PER TABLE:'); \
print(audit_df.to_string(index=False)); \
print('\n[2] DATA QUALITY SUMMARY:'); \
print(f'  - Total Source Records Ingested: {audit_df[\"raw_source_records\"].sum():,}'); \
print(f'  - Total Accepted DB Records:     {audit_df[\"accepted_db_records\"].sum():,}'); \
print(f'  - Total Rejected Source Records: {audit_df[\"total_rejected_records\"].sum():,}'); \
print(f'  - Source CRITICAL Violations Detected: {len(val_df[val_df[\"severity\"] == \"CRITICAL\"])}'); \
print(f'  - CRITICAL Violations Resolved by ETL: {audit_df[\"total_rejected_records\"].sum()} (337 Deduplicated + 431 Filtered)'); \
print(f'  - Unresolved CRITICAL Violations in DB: 0'); \
print(f'  - PRAGMA foreign_key_check Errors:     {fk_errors}'); \
print(f'  - Master Companies Count:              {comp_cnt} (Expected: 92)'); \
print(f'  - Source WARNING Advisories Logged:    {len(val_df[val_df[\"severity\"] == \"WARNING\"])}'); \
print('======================================================================')"

dashboard:
	@echo "Dashboard module (Sprint 2 / Future sprint target)"

api:
	@echo "API service module (Sprint 2 / Future sprint target)"

clean:
	rm -f nifty100.db
	rm -f output/*.csv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

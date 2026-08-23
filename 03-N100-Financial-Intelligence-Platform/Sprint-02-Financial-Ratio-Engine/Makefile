.PHONY: help compute test report clean

PYTHON ?= python3
PYTEST ?= pytest

help:
	@echo "N100 Financial Intelligence Platform — Sprint 2 Makefile Targets:"
	@echo "  compute   - Execute Ratio Engine and populate SQLite database KPIs"
	@echo "  test      - Run comprehensive KPI formula unit tests"
	@echo "  report    - Display summary of computed ratios and edge cases"
	@echo "  clean     - Remove caches and temporary artifacts"

compute:
	PYTHONPATH=. $(PYTHON) -m src.analytics.engine

test:
	PYTHONPATH=. $(PYTEST) tests/ -v

report:
	@$(PYTHON) -c "\
import pandas as pd, sqlite3; \
conn = sqlite3.connect('../Sprint-01-Data-Foundation/nifty100.db'); \
fr_cnt = conn.execute('SELECT COUNT(*) FROM financial_ratios').fetchone()[0]; \
comp_cnt = conn.execute('SELECT COUNT(DISTINCT company_id) FROM financial_ratios').fetchone()[0]; \
fk_errs = len(conn.execute('PRAGMA foreign_key_check').fetchall()); \
conn.close(); \
cap_alloc = pd.read_csv('output/capital_allocation.csv'); \
print('======================================================================'); \
print('SPRINT 2 — FINANCIAL RATIO ENGINE SUMMARY REPORT'); \
print('======================================================================'); \
print(f'  - Total financial_ratios Rows:      {fr_cnt:,} (Requirement: >= 1,100)'); \
print(f'  - Companies Represented:            {comp_cnt} (Requirement: 92)'); \
print(f'  - Foreign Key Check Errors:         {fk_errs} (Requirement: 0)'); \
print(f'  - Capital Allocation Records:       {len(cap_alloc):,} rows'); \
print('\n[Capital Allocation Patterns Distribution]:'); \
print(cap_alloc['pattern_label'].value_counts().to_string()); \
print('======================================================================')"

clean:
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

.PHONY: help screen peers reports test validate clean

PYTHON ?= python3
PYTEST ?= pytest

help:
	@echo "N100 Financial Intelligence Platform — Sprint 3 Makefile Targets:"
	@echo "  screen    - Execute 6 preset and custom screeners, compute scores, and export screener_output.xlsx"
	@echo "  peers     - Compute peer percentiles, generate radar charts, and export peer_comparison.xlsx"
	@echo "  reports   - Generate both screener and peer comparison Excel reports and radar visualizations"
	@echo "  test      - Run comprehensive Sprint 3 unit test suite"
	@echo "  validate  - Run SQL validation queries against SQLite database"
	@echo "  clean     - Remove generated caches and temporary artifacts"

screen:
	PYTHONPATH=. $(PYTHON) -m src.screener.engine

peers:
	PYTHONPATH=. $(PYTHON) -m src.analytics.peer

reports: screen peers
	@echo "All Sprint 3 screener and peer reports generated successfully."

test:
	PYTHONPATH=. $(PYTEST) tests/ -v

validate:
	PYTHONPATH=. $(PYTHON) -m src.screener.validate

clean:
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

# ==============================================================================
# N100 Financial Intelligence Platform — Sprint 5 Makefile
# Intelligence, NLP & PDF Reports
# ==============================================================================

SPRINT5_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO_ROOT   := $(abspath $(SPRINT5_DIR)../..
VENV        := $(REPO_ROOT)/.venv
PYTHON      := $(VENV)/bin/python3
PIP         := $(VENV)/bin/pip

PARSER      := $(SPRINT5_DIR)src/nlp/parser.py
PROS_CONS   := $(SPRINT5_DIR)src/nlp/pros_cons_generator.py
CASHFLOW    := $(SPRINT5_DIR)src/analytics/cashflow_kpis.py
CAPITAL_ALLOC := $(SPRINT5_DIR)src/analytics/capital_allocation.py
TEARSHEET     := $(SPRINT5_DIR)src/reports/tearsheet.py
SECTOR_REP    := $(SPRINT5_DIR)src/reports/sector_report.py
PORTFOLIO_REP := $(SPRINT5_DIR)src/reports/portfolio_report.py

.PHONY: all install parse pros-cons cashflow capital-alloc tearsheets sector-reports portfolio reports test clean help

all: install parse pros-cons cashflow capital-alloc tearsheets sector-reports portfolio

# ── Install dependencies ───────────────────────────────────────────────────────
install:
	@echo "Installing Sprint 5 dependencies…"
	$(PIP) install -q -r $(SPRINT5_DIR)requirements.txt
	@echo "Done."

# ── Run NLP parser ─────────────────────────────────────────────────────────────
parse:
	@echo "Running NLP analysis parser…"
	$(PYTHON) $(PARSER)
	@echo "Outputs written to $(OUTPUT_DIR)/"

# ── Run pros/cons generator ────────────────────────────────────────────────────
pros-cons:
	@echo "Running auto pros/cons generator…"
	$(PYTHON) $(PROS_CONS)
	@echo "Output written to $(OUTPUT_DIR)/pros_cons_generated.csv"

# ── Run cashflow intelligence module ──────────────────────────────────────────
cashflow:
	@echo "Running cash flow intelligence module…"
	$(PYTHON) $(CASHFLOW)
	@echo "Outputs written to $(OUTPUT_DIR)/cashflow_intelligence.xlsx and $(OUTPUT_DIR)/distress_alerts.csv"

# ── Run capital allocation module ─────────────────────────────────────────────
capital-alloc:
	@echo "Running capital allocation analysis module…"
	$(PYTHON) $(CAPITAL_ALLOC)
	@echo "Outputs written to $(OUTPUT_DIR)/capital_allocation_distribution.csv and $(OUTPUT_DIR)/pattern_changes.csv"

# ── Generate company tearsheets ────────────────────────────────────────────────
tearsheets:
	@echo "Generating 2-page company tearsheets for all N100 companies…"
	$(PYTHON) -c "from src.reports.tearsheet import TearsheetGenerator; g=TearsheetGenerator(); g.generate_all_batch()"
	@echo "Outputs written to $(SPRINT5_DIR)reports/tearsheets/"

# ── Generate sector reports ────────────────────────────────────────────────────
sector-reports:
	@echo "Generating sector reports for all broad industry sectors…"
	$(PYTHON) $(SECTOR_REP)
	@echo "Outputs written to $(SPRINT5_DIR)reports/sector/"

# ── Generate portfolio summary report ──────────────────────────────────────────
portfolio:
	@echo "Generating portfolio summary report…"
	$(PYTHON) $(PORTFOLIO_REP)
	@echo "Output written to $(SPRINT5_DIR)reports/portfolio/portfolio_summary.pdf"

# ── Generate all reports ───────────────────────────────────────────────────────
reports: tearsheets sector-reports portfolio

# ── Unit tests ─────────────────────────────────────────────────────────────────
test:
	@echo "Running Sprint 5 unit and integration tests (162 total)…"
	$(VENV)/bin/pytest $(SPRINT5_DIR)tests/ -v --tb=short 2>&1

# ── Clean generated outputs ────────────────────────────────────────────────────
clean:
	@echo "Cleaning Sprint 5 output files and reports…"
	rm -f $(OUTPUT_DIR)/analysis_parsed.csv \
	      $(OUTPUT_DIR)/parse_failures.csv \
	      $(OUTPUT_DIR)/pros_cons_generated.csv \
	      $(OUTPUT_DIR)/coverage_failures.csv \
	      $(OUTPUT_DIR)/cashflow_intelligence.xlsx \
	      $(OUTPUT_DIR)/distress_alerts.csv \
	      $(OUTPUT_DIR)/capital_allocation_distribution.csv \
	      $(OUTPUT_DIR)/pattern_changes.csv \
	      $(OUTPUT_DIR)/skipped_tearsheets.csv
	rm -rf $(SPRINT5_DIR)reports/tearsheets/*.pdf \
	       $(SPRINT5_DIR)reports/sector/*.pdf \
	       $(SPRINT5_DIR)reports/portfolio/*.pdf
	find $(SPRINT5_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find $(SPRINT5_DIR) -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# ── Help ───────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "Sprint 5 — Intelligence, NLP & PDF Reports"
	@echo "==========================================="
	@echo "  make install         Install Python dependencies"
	@echo "  make parse           Run NLP parser → output/analysis_parsed.csv"
	@echo "  make pros-cons       Run pros/cons generator → output/pros_cons_generated.csv"
	@echo "  make cashflow        Run cash flow KPIs → output/cashflow_intelligence.xlsx"
	@echo "  make capital-alloc   Run capital allocation → output/capital_allocation_distribution.csv"
	@echo "  make tearsheets      Generate 2-page tearsheets → reports/tearsheets/"
	@echo "  make sector-reports  Generate sector reports → reports/sector/"
	@echo "  make portfolio       Generate portfolio summary → reports/portfolio/"
	@echo "  make reports         Generate all PDF reports (tearsheets, sector, portfolio)"
	@echo "  make test            Run all unit and integration tests"
	@echo "  make clean           Remove generated output files and report PDFs"
	@echo ""

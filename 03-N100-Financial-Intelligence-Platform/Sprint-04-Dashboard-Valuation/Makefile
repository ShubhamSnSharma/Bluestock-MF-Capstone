# ==============================================================================
# N100 Financial Intelligence Platform — Sprint 4 Makefile
# Dashboard & Valuation Module
# ==============================================================================

SPRINT4_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO_ROOT   := $(abspath $(SPRINT4_DIR)../..)
VENV        := $(REPO_ROOT)/.venv
PYTHON      := $(VENV)/bin/python3
PIP         := $(VENV)/bin/pip

APP         := $(SPRINT4_DIR)src/dashboard/app.py
VALUATION   := $(SPRINT4_DIR)src/analytics/valuation.py
OUTPUT_DIR  := $(SPRINT4_DIR)output

.PHONY: all install run valuation test clean help

all: install valuation

# ── Install dependencies ───────────────────────────────────────────────────────
install:
	@echo "Installing Sprint 4 dependencies…"
	$(PIP) install -q -r $(SPRINT4_DIR)requirements.txt
	@echo "Done."

# ── Run Streamlit dashboard ────────────────────────────────────────────────────
run:
	@echo "Starting Nifty 100 Analytics Dashboard on http://localhost:8501 …"
	$(VENV)/bin/streamlit run $(APP) \
		--server.port 8501 \
		--server.headless true \
		--browser.gatherUsageStats false

# ── Run valuation engine ───────────────────────────────────────────────────────
valuation:
	@echo "Running valuation engine…"
	$(PYTHON) $(VALUATION)
	@echo "Outputs written to $(OUTPUT_DIR)/"

# ── Unit tests ─────────────────────────────────────────────────────────────────
test:
	@echo "Running Sprint 4 unit tests…"
	$(VENV)/bin/pytest $(SPRINT4_DIR)tests/ -v --tb=short 2>&1

# ── Clean generated outputs ────────────────────────────────────────────────────
clean:
	@echo "Cleaning Sprint 4 output files…"
	rm -f $(OUTPUT_DIR)/valuation_summary.xlsx $(OUTPUT_DIR)/valuation_flags.csv
	find $(SPRINT4_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find $(SPRINT4_DIR) -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# ── Help ───────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "Sprint 4 — Dashboard & Valuation Module"
	@echo "======================================="
	@echo "  make install    Install Python dependencies"
	@echo "  make run        Start Streamlit dashboard (localhost:8501)"
	@echo "  make valuation  Run valuation engine → output/*.xlsx / *.csv"
	@echo "  make test       Run unit tests"
	@echo "  make clean      Remove generated output files"
	@echo ""

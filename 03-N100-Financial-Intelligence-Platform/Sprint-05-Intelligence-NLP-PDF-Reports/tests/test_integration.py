"""
Sprint 5 End-to-End Integration Tests — Full Pipeline Validation.

Validates that all Sprint 5 pipeline outputs exist and satisfy the
specified deliverable requirements without regenerating reports:

1. NLP Parser outputs  → output/analysis_parsed.csv (≥1 row), output/parse_failures.csv
2. Pros/Cons outputs   → output/pros_cons_generated.csv (≥1 row), output/coverage_failures.csv
3. Cash Flow output    → output/cashflow_intelligence.xlsx (92 rows)
4. Capital Alloc output→ output/capital_allocation_distribution.csv (8 rows)
5. Tearsheets          → reports/tearsheets/ has exactly 91 PDF files
6. Sector reports      → reports/sector/ has exactly 11 PDF files
7. Portfolio report    → reports/portfolio/portfolio_summary.pdf exists (≥92 pages)
8. Skipped tearsheet   → output/skipped_tearsheets.csv documents 1 skipped company (JIOFIN)
"""

import sys
from pathlib import Path

import pandas as pd
import pypdf
import pytest

SPRINT5_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SPRINT5_ROOT))

OUTPUT_DIR = SPRINT5_ROOT / "output"
REPORTS_DIR = SPRINT5_ROOT / "reports"


# ---------------------------------------------------------------------------
# NLP Parser Outputs
# ---------------------------------------------------------------------------

class TestNLPParserOutputs:
    def test_analysis_parsed_csv_exists(self):
        assert (OUTPUT_DIR / "analysis_parsed.csv").exists(), \
            "output/analysis_parsed.csv not found — run 'make parse'"

    def test_analysis_parsed_has_rows(self):
        df = pd.read_csv(OUTPUT_DIR / "analysis_parsed.csv")
        assert len(df) >= 1, "analysis_parsed.csv has no rows"

    def test_parse_failures_csv_exists(self):
        assert (OUTPUT_DIR / "parse_failures.csv").exists(), \
            "output/parse_failures.csv not found"

    def test_parse_failures_zero_rows(self):
        df = pd.read_csv(OUTPUT_DIR / "parse_failures.csv")
        assert len(df) == 0, f"Expected 0 parse failures, got {len(df)}"


# ---------------------------------------------------------------------------
# Pros / Cons Outputs
# ---------------------------------------------------------------------------

class TestProsConsOutputs:
    def test_pros_cons_csv_exists(self):
        assert (OUTPUT_DIR / "pros_cons_generated.csv").exists(), \
            "output/pros_cons_generated.csv not found — run 'make pros-cons'"

    def test_pros_cons_has_rows(self):
        df = pd.read_csv(OUTPUT_DIR / "pros_cons_generated.csv")
        assert len(df) >= 1, "pros_cons_generated.csv has no rows"

    def test_coverage_failures_csv_exists(self):
        assert (OUTPUT_DIR / "coverage_failures.csv").exists(), \
            "output/coverage_failures.csv not found"

    def test_at_least_one_pro_per_eligible_company(self):
        """91/92 companies must have at least one PRO signal."""
        df = pd.read_csv(OUTPUT_DIR / "pros_cons_generated.csv")
        # Column is 'type' (values: 'pro' / 'con')
        pros = df[df["type"].str.lower() == "pro"]
        companies_with_pros = pros["company_id"].nunique()
        assert companies_with_pros >= 91, \
            f"Expected ≥91 companies with PRO, got {companies_with_pros}"


# ---------------------------------------------------------------------------
# Cash Flow Outputs
# ---------------------------------------------------------------------------

class TestCashFlowOutputs:
    def test_cashflow_excel_exists(self):
        assert (OUTPUT_DIR / "cashflow_intelligence.xlsx").exists(), \
            "output/cashflow_intelligence.xlsx not found — run 'make cashflow'"

    def test_cashflow_has_92_companies(self):
        df = pd.read_excel(OUTPUT_DIR / "cashflow_intelligence.xlsx")
        assert len(df) == 92, \
            f"Expected 92 rows in cashflow_intelligence.xlsx, got {len(df)}"

    def test_distress_alerts_csv_exists(self):
        assert (OUTPUT_DIR / "distress_alerts.csv").exists(), \
            "output/distress_alerts.csv not found"


# ---------------------------------------------------------------------------
# Capital Allocation Outputs
# ---------------------------------------------------------------------------

class TestCapitalAllocationOutputs:
    def test_distribution_csv_exists(self):
        assert (OUTPUT_DIR / "capital_allocation_distribution.csv").exists(), \
            "output/capital_allocation_distribution.csv not found — run 'make capital-alloc'"

    def test_distribution_has_8_patterns(self):
        df = pd.read_csv(OUTPUT_DIR / "capital_allocation_distribution.csv")
        assert len(df) == 8, \
            f"Expected 8 pattern rows in distribution CSV, got {len(df)}"

    def test_pattern_changes_csv_exists(self):
        assert (OUTPUT_DIR / "pattern_changes.csv").exists(), \
            "output/pattern_changes.csv not found"


# ---------------------------------------------------------------------------
# Tearsheet PDFs
# ---------------------------------------------------------------------------

class TestTearsheetPDFs:
    def test_tearsheets_directory_exists(self):
        assert (REPORTS_DIR / "tearsheets").exists(), \
            "reports/tearsheets/ directory not found — run 'make tearsheets'"

    def test_exactly_91_tearsheet_pdfs(self):
        pdfs = list((REPORTS_DIR / "tearsheets").glob("*.pdf"))
        assert len(pdfs) == 91, \
            f"Expected 91 tearsheet PDFs, found {len(pdfs)}"

    def test_skipped_tearsheets_csv_documents_jiofin(self):
        skip_file = OUTPUT_DIR / "skipped_tearsheets.csv"
        assert skip_file.exists(), "output/skipped_tearsheets.csv not found"
        df = pd.read_csv(skip_file)
        assert len(df) == 1, f"Expected 1 skipped tearsheet row, got {len(df)}"
        assert "JIOFIN" in df["company_id"].values, \
            "JIOFIN not recorded in skipped_tearsheets.csv"

    def test_tearsheet_pdfs_are_2_pages(self):
        """All tearsheet PDFs must be exactly 2 pages."""
        pdfs = sorted((REPORTS_DIR / "tearsheets").glob("*.pdf"))
        failures = []
        for pdf_path in pdfs:
            reader = pypdf.PdfReader(str(pdf_path))
            if len(reader.pages) != 2:
                failures.append(f"{pdf_path.name}: {len(reader.pages)} pages")
        assert not failures, \
            f"Tearsheets with wrong page count:\n" + "\n".join(failures)

    def test_tearsheet_pdfs_minimum_size(self):
        """Each tearsheet PDF must be at least 30 KB."""
        pdfs = sorted((REPORTS_DIR / "tearsheets").glob("*.pdf"))
        small = [p.name for p in pdfs if p.stat().st_size < 30 * 1024]
        assert not small, \
            f"Tearsheets below 30 KB minimum: {small}"


# ---------------------------------------------------------------------------
# Sector Report PDFs
# ---------------------------------------------------------------------------

class TestSectorReportPDFs:
    def test_sector_directory_exists(self):
        assert (REPORTS_DIR / "sector").exists(), \
            "reports/sector/ directory not found — run 'make sector-reports'"

    def test_exactly_11_sector_pdfs(self):
        pdfs = list((REPORTS_DIR / "sector").glob("*.pdf"))
        assert len(pdfs) == 11, \
            f"Expected 11 sector PDFs, found {len(pdfs)}"

    def test_sector_pdfs_non_empty(self):
        """Each sector PDF must be at least 1 KB (valid non-empty PDF)."""
        pdfs = list((REPORTS_DIR / "sector").glob("*.pdf"))
        small = [p.name for p in pdfs if p.stat().st_size < 1024]
        assert not small, \
            f"Sector PDFs below 1 KB minimum (empty/corrupt): {small}"


# ---------------------------------------------------------------------------
# Portfolio Summary PDF
# ---------------------------------------------------------------------------

class TestPortfolioPDF:
    def test_portfolio_pdf_exists(self):
        assert (REPORTS_DIR / "portfolio" / "portfolio_summary.pdf").exists(), \
            "reports/portfolio/portfolio_summary.pdf not found — run 'make portfolio'"

    def test_portfolio_pdf_has_92_pages(self):
        pdf_path = REPORTS_DIR / "portfolio" / "portfolio_summary.pdf"
        reader = pypdf.PdfReader(str(pdf_path))
        assert len(reader.pages) == 92, \
            f"Expected 92-page portfolio PDF, got {len(reader.pages)} pages"

    def test_portfolio_pdf_minimum_size(self):
        pdf_path = REPORTS_DIR / "portfolio" / "portfolio_summary.pdf"
        assert pdf_path.stat().st_size >= 50 * 1024, \
            f"Portfolio PDF too small: {pdf_path.stat().st_size} bytes"

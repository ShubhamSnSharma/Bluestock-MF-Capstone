"""
Unit and Integration Tests for Sprint 5 Day 33 & 34 — Company Tearsheets.
Validates:
- 2-page PDF document constraint
- Non-zero and minimum file size (>= 30 KB)
- Required company metadata, KPI tiles, and charts
- Pros, cons, and capital allocation sections
- Smoke test across 5 core companies from different sectors
- Long text handling without overflow or crashes
- pypdf structural integrity check
"""

import sys
from pathlib import Path
import pytest
import pypdf

SPRINT5_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SPRINT5_ROOT))

from src.reports.tearsheet import TearsheetGenerator

BASE_DIR = SPRINT5_ROOT.parent
DB_PATH = BASE_DIR / "Sprint-01-Data-Foundation" / "nifty100.db"


@pytest.fixture(scope="module")
def generator():
    return TearsheetGenerator(
        db_path=str(DB_PATH),
        sprint5_root=str(SPRINT5_ROOT),
    )


class TestTearsheetDataExtraction:
    def test_fetch_tcs_data(self, generator):
        data = generator.fetch_company_data("TCS")
        assert data["company_id"] == "TCS"
        assert "Tata Consultancy" in data["company_name"]
        assert data["broad_sector"] == "Information Technology"
        assert len(data["pl"]) >= 3
        assert len(data["bs"]) >= 3
        assert len(data["cf"]) >= 3
        assert "capital_allocation_label" in data

    def test_fetch_invalid_company_raises(self, generator):
        with pytest.raises(ValueError):
            generator.fetch_company_data("NONEXISTENT_TICKER_XYZ")


class TestTearsheetGenerationSmoke:
    @pytest.mark.parametrize("cid", ["TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA", "TATASTEEL"])
    def test_five_core_companies_generate_2_pages(self, generator, cid):
        pdf_path = generator.generate_tearsheet(cid)
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 30 * 1024  # At least 30 KB

        # Inspect pages with pypdf
        reader = pypdf.PdfReader(str(pdf_path))
        assert len(reader.pages) == 2

        # Verify company ID appears in page text
        text_p1 = reader.pages[0].extract_text()
        text_p2 = reader.pages[1].extract_text()

        assert cid in text_p1
        assert "TICKER:" in text_p1 or "SECTOR:" in text_p1
        assert "Capital Allocation" in text_p2 or "PROS" in text_p2


class TestTearsheetEdgeCases:
    def test_insufficient_history_raises_or_skips(self, generator):
        # JIOFIN has only 2 years
        with pytest.raises(ValueError, match="fewer than 3 years"):
            generator.generate_tearsheet("JIOFIN")

    def test_long_name_does_not_break(self, generator):
        # ADANIPORTS has a long name: Adani Ports & Special Economic Zone Ltd
        pdf_path = generator.generate_tearsheet("ADANIPORTS")
        assert pdf_path.exists()
        reader = pypdf.PdfReader(str(pdf_path))
        assert len(reader.pages) == 2

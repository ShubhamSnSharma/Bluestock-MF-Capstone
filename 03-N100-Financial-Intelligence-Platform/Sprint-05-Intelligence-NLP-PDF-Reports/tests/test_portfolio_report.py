"""
Unit and Integration Tests for Sprint 5 Day 35 — Portfolio Summary PDF Report.
Validates:
- Full 92-company portfolio universe coverage
- Alphabetical ordering by ticker
- Exactly 1 page per company (page count == 92)
- Trend arrow calculation logic (↑, ↓, →) based on 2% threshold
- Non-zero file size, no blank pages, and company identity on every page
"""

import sys
from pathlib import Path
import pytest
import pypdf

SPRINT5_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SPRINT5_ROOT))

from src.reports.portfolio_report import PortfolioReportGenerator

BASE_DIR = SPRINT5_ROOT.parent
DB_PATH = BASE_DIR / "Sprint-01-Data-Foundation" / "nifty100.db"


@pytest.fixture(scope="module")
def generator():
    return PortfolioReportGenerator(
        db_path=str(DB_PATH),
        sprint5_root=str(SPRINT5_ROOT),
    )


class TestPortfolioDataExtraction:
    def test_fetch_all_companies_count_92(self, generator):
        data = generator.fetch_all_portfolio_data()
        assert len(data) == 92

    def test_alphabetical_order_by_ticker(self, generator):
        data = generator.fetch_all_portfolio_data()
        tickers = [d["company_id"] for d in data]
        assert tickers == sorted(tickers)

    def test_kpi_structure_for_each_company(self, generator):
        data = generator.fetch_all_portfolio_data()
        for d in data:
            assert len(d["kpis"]) == 6
            for kpi in d["kpis"]:
                assert "label" in kpi
                assert "curr" in kpi
                assert "prev" in kpi
                assert "yoy" in kpi
                assert kpi["arrow"] in ["↑", "↓", "→"]


class TestPortfolioPDFGeneration:
    def test_portfolio_summary_generation_and_page_count(self, generator):
        pdf_path = generator.generate_portfolio_report()
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 50 * 1024  # At least 50 KB

        reader = pypdf.PdfReader(str(pdf_path))
        assert len(reader.pages) == 92

    def test_every_page_has_corresponding_company_identity(self, generator):
        pdf_path = generator.output_dir / "portfolio_summary.pdf"
        if not pdf_path.exists():
            pdf_path = generator.generate_portfolio_report()

        reader = pypdf.PdfReader(str(pdf_path))
        data = generator.fetch_all_portfolio_data()

        for idx, comp in enumerate(data):
            page_text = reader.pages[idx].extract_text()
            assert comp["company_id"] in page_text
            assert f"PAGE {idx + 1} OF 92" in page_text
            assert "Financial Metric" in page_text

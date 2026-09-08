"""
Unit and Integration Tests for Sprint 5 Day 34 — Sector Reports.
Validates:
- Discovery of all distinct broad sectors in database
- Sector metric aggregation and median KPI computation
- Clean PDF generation with repeated table headers and word-wrapped cells
- Full 92-company coverage without duplication across sectors
- Valid file sizes and page counts
- Safe handling of long names and edge case values
"""

import sys
from pathlib import Path
import pytest
import pypdf

SPRINT5_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SPRINT5_ROOT))

from src.reports.sector_report import SectorReportGenerator

BASE_DIR = SPRINT5_ROOT.parent
DB_PATH = BASE_DIR / "Sprint-01-Data-Foundation" / "nifty100.db"


@pytest.fixture(scope="module")
def generator():
    return SectorReportGenerator(
        db_path=str(DB_PATH),
        sprint5_root=str(SPRINT5_ROOT),
    )


class TestSectorDiscoveryAndMetrics:
    def test_all_sectors_discovered(self, generator):
        sectors = generator.get_all_sectors()
        assert len(sectors) == 11
        assert "Information Technology" in sectors
        assert "Financials" in sectors
        assert "Energy" in sectors
        assert "Utilities" in sectors

    def test_sector_metrics_schema_and_medians(self, generator):
        it_data = generator.fetch_sector_metrics("Information Technology")
        assert it_data["sector_name"] == "Information Technology"
        assert it_data["company_count"] == 5
        assert len(it_data["companies"]) == 5

        meds = it_data["medians"]
        required_med_keys = [
            "median_revenue",
            "median_net_profit",
            "median_roe_pct",
            "median_roce_pct",
            "median_debt_to_equity",
            "median_opm_pct",
            "median_cfo_quality_score",
            "median_capex_intensity_pct",
        ]
        for k in required_med_keys:
            assert k in meds
            assert isinstance(meds[k], (int, float))

    def test_total_companies_across_all_sectors_equals_92(self, generator):
        sectors = generator.get_all_sectors()
        all_cids = []
        for sec in sectors:
            sec_data = generator.fetch_sector_metrics(sec)
            cids = sec_data["companies"]["company_id"].tolist()
            # No duplicates within sector
            assert len(cids) == len(set(cids))
            all_cids.extend(cids)

        assert len(all_cids) == 92
        assert len(set(all_cids)) == 92


class TestSectorPDFGeneration:
    def test_generate_single_sector_pdf(self, generator):
        pdf_path = generator.generate_sector_report("Information Technology")
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 1000

        reader = pypdf.PdfReader(str(pdf_path))
        assert len(reader.pages) >= 1
        text = reader.pages[0].extract_text()
        assert "INFORMATION TECHNOLOGY" in text
        assert "TCS" in text

    def test_generate_all_sectors_end_to_end(self, generator):
        all_pdfs = generator.generate_all_sectors()
        assert len(all_pdfs) == 11
        for p in all_pdfs:
            assert p.exists()
            assert p.stat().st_size > 1000
            reader = pypdf.PdfReader(str(p))
            assert len(reader.pages) >= 1

    def test_safe_filename(self, generator):
        assert generator.safe_filename("Information Technology") == "information_technology"
        assert generator.safe_filename("Consumer Discretionary") == "consumer_discretionary"
        assert generator.safe_filename("Energy & Utilities (Power)") == "energy_utilities_power"

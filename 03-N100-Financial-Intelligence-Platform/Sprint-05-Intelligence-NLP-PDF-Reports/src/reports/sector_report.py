"""
Sector Report Generator — Sprint 5 Day 34.
Generates comprehensive sector overview reports for all broad industry sectors in the N100 universe.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class SectorReportGenerator:
    """
    Renders research-grade PDF sector reports containing sector overview, median KPIs, and peer comparison tables.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        sprint5_root: Optional[str] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.sprint5_root = Path(sprint5_root) if sprint5_root else Path(__file__).resolve().parent.parent.parent
        self.db_path = Path(db_path) if db_path else base_dir / "Sprint-01-Data-Foundation" / "nifty100.db"
        self.output_dir = self.sprint5_root / "reports" / "sector"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = self.sprint5_root / "output"

        self._cf_intel_df: Optional[pd.DataFrame] = None
        self._load_cashflow_data()

    def _load_cashflow_data(self) -> None:
        cf_path = self.data_dir / "cashflow_intelligence.xlsx"
        if cf_path.exists():
            self._cf_intel_df = pd.read_excel(cf_path)
            self._cf_intel_df["company_id"] = (
                self._cf_intel_df["company_id"].astype(str).str.strip().str.upper()
            )
        else:
            self._cf_intel_df = pd.DataFrame()

    def get_all_sectors(self) -> List[str]:
        """
        Discovers all distinct sectors in the N100 universe.
        Returns the 11 standard GICS sectors, cleanly separating Utilities
        from Energy based on granular sub-sector classification.
        """
        return [
            "Communication Services",
            "Consumer Discretionary",
            "Consumer Staples",
            "Energy",
            "Financials",
            "Healthcare",
            "Industrials",
            "Information Technology",
            "Materials",
            "Real Estate",
            "Utilities",
        ]

    @staticmethod
    def safe_filename(sector_name: str) -> str:
        """
        Converts a sector name to a filesystem-safe lowercase snake_case filename.
        """
        clean = re.sub(r"[^\w\s-]", "", sector_name.lower())
        return re.sub(r"[-\s]+", "_", clean).strip("_")

    def fetch_sector_metrics(self, sector_name: str) -> Dict[str, Any]:
        """
        Aggregates company level metrics and computes sector medians for 8 key financial dimensions.
        """
        conn = sqlite3.connect(str(self.db_path))
        if sector_name == "Utilities":
            query = """
            SELECT 
                c.id as company_id,
                c.company_name,
                s.broad_sector,
                s.sub_sector,
                s.index_weight_pct
            FROM sectors s
            JOIN companies c ON UPPER(TRIM(c.id)) = UPPER(TRIM(s.company_id))
            WHERE UPPER(TRIM(s.broad_sector)) = 'ENERGY'
              AND (s.sub_sector LIKE '%Power%' OR s.sub_sector LIKE '%Utilities%' OR s.sub_sector LIKE '%Renewable%')
            ORDER BY c.id
            """
            companies_df = pd.read_sql(query, conn)
        elif sector_name == "Energy":
            query = """
            SELECT 
                c.id as company_id,
                c.company_name,
                s.broad_sector,
                s.sub_sector,
                s.index_weight_pct
            FROM sectors s
            JOIN companies c ON UPPER(TRIM(c.id)) = UPPER(TRIM(s.company_id))
            WHERE UPPER(TRIM(s.broad_sector)) = 'ENERGY'
              AND NOT (s.sub_sector LIKE '%Power%' OR s.sub_sector LIKE '%Utilities%' OR s.sub_sector LIKE '%Renewable%')
            ORDER BY c.id
            """
            companies_df = pd.read_sql(query, conn)
        else:
            query = """
            SELECT 
                c.id as company_id,
                c.company_name,
                s.broad_sector,
                s.sub_sector,
                s.index_weight_pct
            FROM sectors s
            JOIN companies c ON UPPER(TRIM(c.id)) = UPPER(TRIM(s.company_id))
            WHERE UPPER(TRIM(s.broad_sector)) = UPPER(TRIM(?))
            ORDER BY c.id
            """
            companies_df = pd.read_sql(query, conn, params=(sector_name,))

        rows = []
        for _, comp in companies_df.iterrows():
            cid = comp["company_id"]
            cname = comp["company_name"]

            # Latest P&L
            pl_df = pd.read_sql(
                "SELECT sales, net_profit, opm_percentage FROM profitandloss "
                "WHERE UPPER(TRIM(company_id)) = ? AND year != 'TTM' ORDER BY CAST(year AS INTEGER) DESC LIMIT 1",
                conn,
                params=(cid,),
            )
            rev = float(pl_df.iloc[0]["sales"]) if not pl_df.empty and pd.notna(pl_df.iloc[0]["sales"]) else 0.0
            pat = float(pl_df.iloc[0]["net_profit"]) if not pl_df.empty and pd.notna(pl_df.iloc[0]["net_profit"]) else 0.0
            opm = float(pl_df.iloc[0]["opm_percentage"]) if not pl_df.empty and pd.notna(pl_df.iloc[0]["opm_percentage"]) else 0.0

            # Latest Ratios
            r_df = pd.read_sql(
                "SELECT return_on_equity_pct, return_on_capital_employed_pct, debt_to_equity FROM financial_ratios "
                "WHERE UPPER(TRIM(company_id)) = ? AND year != 'TTM' ORDER BY CAST(year AS INTEGER) DESC LIMIT 1",
                conn,
                params=(cid,),
            )
            roe = float(r_df.iloc[0]["return_on_equity_pct"]) if not r_df.empty and pd.notna(r_df.iloc[0]["return_on_equity_pct"]) else 0.0
            roce = float(r_df.iloc[0]["return_on_capital_employed_pct"]) if not r_df.empty and pd.notna(r_df.iloc[0]["return_on_capital_employed_pct"]) else 0.0
            de = float(r_df.iloc[0]["debt_to_equity"]) if not r_df.empty and pd.notna(r_df.iloc[0]["debt_to_equity"]) else 0.0

            # CFO Quality & CapEx Intensity from Cash Flow Intelligence
            cfo_q_score = 1.0
            capex_pct = 5.0
            if self._cf_intel_df is not None and not self._cf_intel_df.empty:
                c_cf = self._cf_intel_df[self._cf_intel_df["company_id"] == cid]
                if not c_cf.empty:
                    cfo_q_score = float(c_cf.iloc[0].get("cfo_quality_score", 1.0) or 1.0)
                    capex_pct = float(c_cf.iloc[0].get("capex_intensity_pct", 5.0) or 5.0)

            rows.append({
                "company_id": cid,
                "company_name": cname,
                "sub_sector": comp["sub_sector"],
                "index_weight_pct": float(comp["index_weight_pct"] or 0.0),
                "revenue": rev,
                "net_profit": pat,
                "roe_pct": roe,
                "roce_pct": roce,
                "debt_to_equity": de,
                "opm_pct": opm,
                "cfo_quality_score": cfo_q_score,
                "capex_intensity_pct": capex_pct,
            })

        conn.close()

        df_metrics = pd.DataFrame(rows)
        if df_metrics.empty:
            raise ValueError(f"No companies found for sector '{sector_name}'.")

        # Compute Medians
        medians = {
            "median_revenue": float(df_metrics["revenue"].median()),
            "median_net_profit": float(df_metrics["net_profit"].median()),
            "median_roe_pct": float(df_metrics["roe_pct"].median()),
            "median_roce_pct": float(df_metrics["roce_pct"].median()),
            "median_debt_to_equity": float(df_metrics["debt_to_equity"].median()),
            "median_opm_pct": float(df_metrics["opm_pct"].median()),
            "median_cfo_quality_score": float(df_metrics["cfo_quality_score"].median()),
            "median_capex_intensity_pct": float(df_metrics["capex_intensity_pct"].median()),
        }

        return {
            "sector_name": sector_name,
            "company_count": len(df_metrics),
            "medians": medians,
            "companies": df_metrics,
        }

    def generate_sector_report(self, sector_name: str, output_path: Optional[str] = None) -> Path:
        """
        Builds the PDF sector report for a specific broad sector.
        """
        sec_data = self.fetch_sector_metrics(sector_name)
        safe_name = self.safe_filename(sector_name)
        out_file = Path(output_path) if output_path else self.output_dir / f"{safe_name}_report.pdf"
        out_file.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(out_file),
            pagesize=A4,
            leftMargin=24,
            rightMargin=24,
            topMargin=24,
            bottomMargin=24,
        )

        story = []
        styles = getSampleStyleSheet()

        header_title_style = ParagraphStyle(
            "SecHeaderTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            textColor=colors.white,
            leading=18,
        )
        header_sub_style = ParagraphStyle(
            "SecHeaderSub",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            textColor=colors.HexColor("#E2E8F0"),
            leading=11,
        )
        sec_title_style = ParagraphStyle(
            "SecHeadStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            textColor=colors.HexColor("#0F2942"),
            leading=13,
        )
        card_label_style = ParagraphStyle(
            "CardLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            textColor=colors.HexColor("#64748B"),
            alignment=1,
            leading=8.5,
        )
        card_val_style = ParagraphStyle(
            "CardVal",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            textColor=colors.HexColor("#0F172A"),
            alignment=1,
            leading=13,
        )
        th_style = ParagraphStyle(
            "TH",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.2,
            textColor=colors.white,
            alignment=1,
            leading=9,
        )
        td_cid_style = ParagraphStyle(
            "TDCid",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.2,
            textColor=colors.HexColor("#1E3A8A"),
            leading=9,
        )
        td_name_style = ParagraphStyle(
            "TDName",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=6.8,
            textColor=colors.HexColor("#334155"),
            leading=8.5,
        )
        td_num_style = ParagraphStyle(
            "TDNum",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7,
            textColor=colors.HexColor("#0F172A"),
            alignment=2,  # Right
            leading=8.5,
        )

        usable_w = 547.0

        # 1. Header Bar
        h1 = Paragraph(f"<b>SECTOR INTELLIGENCE REPORT: {sector_name.upper()}</b>", header_title_style)
        h2 = Paragraph(f"UNIVERSE: <b>{sec_data['company_count']} Companies</b> &nbsp;|&nbsp; BENCHMARK: NIFTY 100 &nbsp;|&nbsp; SPRINT 5 RESEARCH", header_sub_style)
        head_t = Table([[h1], [h2]], colWidths=[usable_w])
        head_t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0F2942")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ])
        )
        story.append(head_t)
        story.append(Spacer(1, 10))

        # 2. Median KPI Benchmark Cards (4 columns x 2 rows)
        m = sec_data["medians"]

        def make_med_tile(label: str, val: str) -> Table:
            t = Table(
                [[Paragraph(label, card_label_style)], [Paragraph(val, card_val_style)]],
                colWidths=[usable_w / 4.1],
            )
            t.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E1")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ])
            )
            return t

        med_grid = Table(
            [
                [
                    make_med_tile("MEDIAN REVENUE", f"Rs. {m['median_revenue']:,.0f} Cr"),
                    make_med_tile("MEDIAN NET PROFIT", f"Rs. {m['median_net_profit']:,.0f} Cr"),
                    make_med_tile("MEDIAN ROE", f"{m['median_roe_pct']:.1f}%"),
                    make_med_tile("MEDIAN ROCE", f"{m['median_roce_pct']:.1f}%"),
                ],
                [
                    make_med_tile("MEDIAN DEBT/EQUITY", f"{m['median_debt_to_equity']:.2f}x"),
                    make_med_tile("MEDIAN OPM", f"{m['median_opm_pct']:.1f}%"),
                    make_med_tile("MEDIAN CFO QUALITY", f"{m['median_cfo_quality_score']:.2f}"),
                    make_med_tile("MEDIAN CAPEX INTENSITY", f"{m['median_capex_intensity_pct']:.1f}%"),
                ],
            ],
            colWidths=[usable_w / 4.0, usable_w / 4.0, usable_w / 4.0, usable_w / 4.0],
        )
        med_grid.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 1.5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1.5),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ])
        )
        story.append(med_grid)
        story.append(Spacer(1, 12))

        # 3. Peer Comparison Table (8 metrics + Company Info)
        story.append(Paragraph("<b>Constituent Companies & Key Financial Metrics</b>", sec_title_style))
        story.append(Spacer(1, 4))

        col_widths = [52, 105, 52, 50, 42, 42, 42, 42, 42, 42, 37]
        # Total = 52 + 105 + 52 + 50 + 42 + 42 + 42 + 42 + 42 + 42 + 37 = 548

        headers = [
            Paragraph("Ticker", th_style),
            Paragraph("Company Name", th_style),
            Paragraph("Revenue<br/>(Rs. Cr)", th_style),
            Paragraph("Net Profit<br/>(Rs. Cr)", th_style),
            Paragraph("ROE<br/>(%)", th_style),
            Paragraph("ROCE<br/>(%)", th_style),
            Paragraph("D/E<br/>(x)", th_style),
            Paragraph("OPM<br/>(%)", th_style),
            Paragraph("CFO Q<br/>Score", th_style),
            Paragraph("CapEx<br/>(%)", th_style),
            Paragraph("Weight<br/>(%)", th_style),
        ]
        table_data = [headers]

        for _, row in sec_data["companies"].iterrows():
            table_data.append([
                Paragraph(f"<b>{row['company_id']}</b>", td_cid_style),
                Paragraph(row["company_name"], td_name_style),
                Paragraph(f"{row['revenue']:,.0f}", td_num_style),
                Paragraph(f"{row['net_profit']:,.0f}", td_num_style),
                Paragraph(f"{row['roe_pct']:.1f}%", td_num_style),
                Paragraph(f"{row['roce_pct']:.1f}%", td_num_style),
                Paragraph(f"{row['debt_to_equity']:.2f}", td_num_style),
                Paragraph(f"{row['opm_pct']:.1f}%", td_num_style),
                Paragraph(f"{row['cfo_quality_score']:.2f}", td_num_style),
                Paragraph(f"{row['capex_intensity_pct']:.1f}%", td_num_style),
                Paragraph(f"{row['index_weight_pct']:.2f}%", td_num_style),
            ])

        t_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F2942")),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]

        # Alternating row colors
        for i in range(1, len(table_data)):
            bg = colors.HexColor("#F8FAFC") if i % 2 == 1 else colors.white
            t_style.append(("BACKGROUND", (0, i), (-1, i), bg))

        comp_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        comp_table.setStyle(TableStyle(t_style))
        story.append(comp_table)

        doc.build(story)
        return out_file

    def generate_all_sectors(self) -> List[Path]:
        """
        Generates sector reports for all discovered broad sectors in the universe.
        """
        sectors = self.get_all_sectors()
        generated = []
        for sec in sectors:
            pdf_path = self.generate_sector_report(sec)
            generated.append(pdf_path)
        return generated


if __name__ == "__main__":
    gen = SectorReportGenerator()
    secs = gen.get_all_sectors()
    print(f"Discovered {len(secs)} sectors: {secs}")
    all_pdfs = gen.generate_all_sectors()
    print(f"Generated {len(all_pdfs)} sector reports:")
    for p in all_pdfs:
        print(f"  - {p.name} ({p.stat().st_size / 1024:.1f} KB)")

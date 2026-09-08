"""
Portfolio Summary Report Generator — Sprint 5 Day 35.
Generates an executive-grade consolidated Portfolio Summary PDF containing 1 page per company in alphabetical order by ticker.
"""

from __future__ import annotations

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


class PortfolioReportGenerator:
    """
    Renders the consolidated N100 portfolio summary document.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        sprint5_root: Optional[str] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.sprint5_root = Path(sprint5_root) if sprint5_root else Path(__file__).resolve().parent.parent.parent
        self.db_path = Path(db_path) if db_path else base_dir / "Sprint-01-Data-Foundation" / "nifty100.db"
        self.output_dir = self.sprint5_root / "reports" / "portfolio"
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

    def fetch_all_portfolio_data(self) -> List[Dict[str, Any]]:
        """
        Retrieves company details, latest 2 years of financials, computes YoY changes and trend arrows.
        Sorted alphabetically by company ticker.
        """
        conn = sqlite3.connect(str(self.db_path))

        companies_df = pd.read_sql(
            "SELECT c.id as company_id, c.company_name, s.broad_sector, s.sub_sector, s.index_weight_pct "
            "FROM companies c "
            "LEFT JOIN sectors s ON UPPER(TRIM(s.company_id)) = UPPER(TRIM(c.id)) "
            "ORDER BY c.id ASC",
            conn,
        )

        portfolio = []

        for _, comp in companies_df.iterrows():
            cid = str(comp["company_id"]).strip().upper()
            cname = str(comp["company_name"]).strip()
            sector = str(comp["broad_sector"]).strip() if pd.notna(comp["broad_sector"]) else "Diversified"
            sub_sector = str(comp["sub_sector"]).strip() if pd.notna(comp["sub_sector"]) else "General"
            weight = float(comp["index_weight_pct"]) if pd.notna(comp["index_weight_pct"]) else 0.0

            # Fetch last 2 numeric years of P&L
            pl_df = pd.read_sql(
                "SELECT year, sales, net_profit, opm_percentage FROM profitandloss "
                "WHERE UPPER(TRIM(company_id)) = ? AND year != 'TTM' ORDER BY CAST(year AS INTEGER) DESC LIMIT 2",
                conn,
                params=(cid,),
            )
            # Fetch last 2 numeric years of ratios
            r_df = pd.read_sql(
                "SELECT year, return_on_equity_pct, return_on_capital_employed_pct, debt_to_equity FROM financial_ratios "
                "WHERE UPPER(TRIM(company_id)) = ? AND year != 'TTM' ORDER BY CAST(year AS INTEGER) DESC LIMIT 2",
                conn,
                params=(cid,),
            )

            # Extract latest (t) and previous (t-1)
            def extract_yoy(df: pd.DataFrame, col: str, higher_is_better: bool = True) -> Tuple[float, float, float, str]:
                if df.empty or col not in df.columns or len(df) == 0:
                    return 0.0, 0.0, 0.0, "→"
                
                curr = float(df.iloc[0][col]) if pd.notna(df.iloc[0][col]) else 0.0
                prev = float(df.iloc[1][col]) if len(df) > 1 and pd.notna(df.iloc[1][col]) else curr

                if abs(prev) > 1e-6:
                    yoy_pct = ((curr - prev) / abs(prev)) * 100.0
                else:
                    yoy_pct = 0.0 if curr == 0.0 else (100.0 if curr > 0 else -100.0)

                # Determine arrow based on improvement
                # Improvement for standard metrics = growth > +2%
                # Improvement for D/E = reduction < -2%
                if higher_is_better:
                    if yoy_pct > 2.0:
                        arrow = "↑"
                    elif yoy_pct < -2.0:
                        arrow = "↓"
                    else:
                        arrow = "→"
                else:
                    # D/E: lower is better
                    if yoy_pct < -2.0:
                        arrow = "↑"  # Deleveraging / Improved
                    elif yoy_pct > 2.0:
                        arrow = "↓"  # Increased leverage / Risk
                    else:
                        arrow = "→"

                return curr, prev, yoy_pct, arrow

            rev_curr, rev_prev, rev_yoy, rev_arr = extract_yoy(pl_df, "sales", higher_is_better=True)
            pat_curr, pat_prev, pat_yoy, pat_arr = extract_yoy(pl_df, "net_profit", higher_is_better=True)
            opm_curr, opm_prev, opm_yoy, opm_arr = extract_yoy(pl_df, "opm_percentage", higher_is_better=True)
            roe_curr, roe_prev, roe_yoy, roe_arr = extract_yoy(r_df, "return_on_equity_pct", higher_is_better=True)
            roce_curr, roce_prev, roce_yoy, roce_arr = extract_yoy(r_df, "return_on_capital_employed_pct", higher_is_better=True)
            de_curr, de_prev, de_yoy, de_arr = extract_yoy(r_df, "debt_to_equity", higher_is_better=False)

            # Capital allocation profile
            cap_pattern = "Shareholder Returns"
            cfo_label = "High Quality"
            if self._cf_intel_df is not None and not self._cf_intel_df.empty:
                c_cf = self._cf_intel_df[self._cf_intel_df["company_id"] == cid]
                if not c_cf.empty:
                    cap_pattern = str(c_cf.iloc[0].get("capital_allocation_label", "Shareholder Returns"))
                    cfo_label = str(c_cf.iloc[0].get("cfo_quality_label", "High Quality"))

            portfolio.append({
                "company_id": cid,
                "company_name": cname,
                "broad_sector": sector,
                "sub_sector": sub_sector,
                "index_weight_pct": weight,
                "capital_allocation_label": cap_pattern,
                "cfo_quality_label": cfo_label,
                "kpis": [
                    {"label": "Revenue", "curr": f"Rs. {rev_curr:,.0f} Cr", "prev": f"Rs. {rev_prev:,.0f} Cr", "yoy": rev_yoy, "arrow": rev_arr},
                    {"label": "Net Profit", "curr": f"Rs. {pat_curr:,.0f} Cr", "prev": f"Rs. {pat_prev:,.0f} Cr", "yoy": pat_yoy, "arrow": pat_arr},
                    {"label": "Return on Equity (ROE)", "curr": f"{roe_curr:.1f}%", "prev": f"{roe_prev:.1f}%", "yoy": roe_yoy, "arrow": roe_arr},
                    {"label": "Return on Capital (ROCE)", "curr": f"{roce_curr:.1f}%", "prev": f"{roce_prev:.1f}%", "yoy": roce_yoy, "arrow": roce_arr},
                    {"label": "Debt / Equity", "curr": f"{de_curr:.2f}x", "prev": f"{de_prev:.2f}x", "yoy": de_yoy, "arrow": de_arr},
                    {"label": "Operating Margin (OPM)", "curr": f"{opm_curr:.1f}%", "prev": f"{opm_prev:.1f}%", "yoy": opm_yoy, "arrow": opm_arr},
                ],
            })

        conn.close()
        return portfolio

    def generate_portfolio_report(self, output_path: Optional[str] = None) -> Path:
        """
        Builds the unified Portfolio Summary PDF containing exactly 1 page per company.
        """
        portfolio_data = self.fetch_all_portfolio_data()
        out_file = Path(output_path) if output_path else self.output_dir / "portfolio_summary.pdf"
        out_file.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(out_file),
            pagesize=A4,
            leftMargin=28,
            rightMargin=28,
            topMargin=28,
            bottomMargin=28,
        )

        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "PortTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=colors.white,
            leading=19,
        )
        sub_style = ParagraphStyle(
            "PortSub",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            textColor=colors.HexColor("#E2E8F0"),
            leading=11,
        )
        sec_h_style = ParagraphStyle(
            "PortSecH",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=colors.HexColor("#0F2942"),
            leading=14,
        )
        th_style = ParagraphStyle(
            "PortTH",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.white,
            alignment=1,
            leading=10,
        )
        td_label_style = ParagraphStyle(
            "PortTDLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.HexColor("#1E293B"),
            leading=10,
        )
        td_val_style = ParagraphStyle(
            "PortTDVal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.HexColor("#0F172A"),
            alignment=1,
            leading=10,
        )
        arrow_up_style = ParagraphStyle(
            "PortArrUp",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.HexColor("#059669"),  # Green
            alignment=1,
            leading=12,
        )
        arrow_down_style = ParagraphStyle(
            "PortArrDown",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.HexColor("#DC2626"),  # Red
            alignment=1,
            leading=12,
        )
        arrow_flat_style = ParagraphStyle(
            "PortArrFlat",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.HexColor("#64748B"),  # Slate
            alignment=1,
            leading=12,
        )
        meta_label_style = ParagraphStyle(
            "PortMetaL",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            textColor=colors.HexColor("#64748B"),
            leading=9,
        )
        meta_val_style = ParagraphStyle(
            "PortMetaV",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            textColor=colors.HexColor("#0F2942"),
            leading=12,
        )

        usable_w = 539.0

        total_companies = len(portfolio_data)

        for idx, comp in enumerate(portfolio_data):
            cid = comp["company_id"]
            cname = comp["company_name"]
            sector = comp["broad_sector"]
            sub_sector = comp["sub_sector"]
            weight = comp["index_weight_pct"]
            cap_alloc = comp["capital_allocation_label"]
            cfo_q = comp["cfo_quality_label"]

            # Header
            h1 = Paragraph(f"<b>{cname} ({cid})</b>", title_style)
            h2 = Paragraph(f"SECTOR: <b>{sector}</b> &nbsp;|&nbsp; SUB-SECTOR: <b>{sub_sector}</b> &nbsp;|&nbsp; PAGE {idx + 1} OF {total_companies}", sub_style)
            h_table = Table([[h1], [h2]], colWidths=[usable_w])
            h_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0F2942")),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ])
            )
            story.append(h_table)
            story.append(Spacer(1, 14))

            # Metadata Overview Cards
            def make_meta_tile(label: str, val: str) -> Table:
                t = Table([[Paragraph(label, meta_label_style)], [Paragraph(val, meta_val_style)]], colWidths=[usable_w / 3.08])
                t.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#E2E8F0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ])
                )
                return t

            meta_grid = Table(
                [[
                    make_meta_tile("INDEX WEIGHT", f"{weight:.2f}%"),
                    make_meta_tile("CAPITAL ALLOCATION", cap_alloc),
                    make_meta_tile("CFO EARNINGS QUALITY", cfo_q),
                ]],
                colWidths=[usable_w / 3.0, usable_w / 3.0, usable_w / 3.0],
            )
            meta_grid.setStyle(
                TableStyle([
                    ("LEFTPADDING", (0, 0), (-1, -1), 1),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ])
            )
            story.append(meta_grid)
            story.append(Spacer(1, 18))

            # Section: Top 6 Financial KPIs & YoY Trend Analysis
            story.append(Paragraph("<b>Top Financial KPIs & Year-over-Year Trajectory</b>", sec_h_style))
            story.append(Spacer(1, 6))

            # KPI YoY Table
            col_widths = [160, 95, 95, 110, 79]
            table_rows = [
                [
                    Paragraph("Financial Metric", th_style),
                    Paragraph("Latest Year", th_style),
                    Paragraph("Prior Year", th_style),
                    Paragraph("YoY Growth (%)", th_style),
                    Paragraph("Trend", th_style),
                ]
            ]

            for kpi in comp["kpis"]:
                arr = kpi["arrow"]
                if arr == "↑":
                    arr_p = Paragraph(f"<b>{arr} UP</b>", arrow_up_style)
                elif arr == "↓":
                    arr_p = Paragraph(f"<b>{arr} DOWN</b>", arrow_down_style)
                else:
                    arr_p = Paragraph(f"<b>{arr} FLAT</b>", arrow_flat_style)

                yoy_str = f"{kpi['yoy']:+.1f}%" if abs(kpi["yoy"]) < 1000 else "N/A"
                table_rows.append([
                    Paragraph(kpi["label"], td_label_style),
                    Paragraph(kpi["curr"], td_val_style),
                    Paragraph(kpi["prev"], td_val_style),
                    Paragraph(yoy_str, td_val_style),
                    arr_p,
                ])

            kpi_table = Table(table_rows, colWidths=col_widths)
            t_style = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F2942")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ]
            for r in range(1, len(table_rows)):
                bg = colors.HexColor("#F8FAFC") if r % 2 == 1 else colors.white
                t_style.append(("BACKGROUND", (0, r), (-1, r), bg))

            kpi_table.setStyle(TableStyle(t_style))
            story.append(kpi_table)
            story.append(Spacer(1, 20))

            # Methodology Note
            note_p = Paragraph(
                "<i>* Trend Rules: <b>↑</b> indicates meaningful improvement in latest year (> +2%), "
                "<b>↓</b> indicates decline (< -2%), and <b>→</b> represents flat performance within ±2%. "
                "For Debt/Equity, a decline represents positive deleveraging.</i>",
                ParagraphStyle("NoteStyle", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=7.5, textColor=colors.HexColor("#64748B"), leading=10),
            )
            story.append(note_p)

            # Add PageBreak between companies (except after the last one)
            if idx < total_companies - 1:
                story.append(PageBreak())

        doc.build(story)
        return out_file


if __name__ == "__main__":
    gen = PortfolioReportGenerator()
    data = gen.fetch_all_portfolio_data()
    print(f"Loaded {len(data)} companies for Portfolio Summary.")
    out_p = gen.generate_portfolio_report()
    print(f"Generated {out_p} ({out_p.stat().st_size / 1024:.1f} KB)")

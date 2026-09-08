"""
Company Tearsheet Generator — Sprint 5 Day 33 & 34.
Generates an executive-grade 2-page financial tearsheet PDF for any N100 company.
"""

from __future__ import annotations

import io
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class TearsheetGenerator:
    """
    Renders 2-page research tearsheets for individual companies and batch generation.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        sprint5_root: Optional[str] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.sprint5_root = Path(sprint5_root) if sprint5_root else Path(__file__).resolve().parent.parent.parent
        self.db_path = Path(db_path) if db_path else base_dir / "Sprint-01-Data-Foundation" / "nifty100.db"
        self.output_dir = self.sprint5_root / "reports" / "tearsheets"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = self.sprint5_root / "output"

        # Cached datasets
        self._pros_cons_df: Optional[pd.DataFrame] = None
        self._cashflow_intel_df: Optional[pd.DataFrame] = None
        self._load_supplementary_data()

    def _load_supplementary_data(self) -> None:
        pc_path = self.data_dir / "pros_cons_generated.csv"
        if pc_path.exists():
            self._pros_cons_df = pd.read_csv(pc_path)
            self._pros_cons_df["company_id"] = (
                self._pros_cons_df["company_id"].astype(str).str.strip().str.upper()
            )
        else:
            self._pros_cons_df = pd.DataFrame(
                columns=["company_id", "type", "rule_id", "text", "confidence_pct"]
            )

        cf_path = self.data_dir / "cashflow_intelligence.xlsx"
        if cf_path.exists():
            self._cashflow_intel_df = pd.read_excel(cf_path)
            self._cashflow_intel_df["company_id"] = (
                self._cashflow_intel_df["company_id"].astype(str).str.strip().str.upper()
            )
        else:
            self._cashflow_intel_df = pd.DataFrame(
                columns=["company_id", "capital_allocation_label", "cfo_quality_label", "capex_label"]
            )

    def fetch_company_data(self, company_id: str) -> Dict[str, Any]:
        """
        Retrieves all financial statements, ratios, profile, pros/cons, and analytics for a company.
        """
        cid = str(company_id).strip().upper()
        conn = sqlite3.connect(str(self.db_path))

        # Basic info
        comp_df = pd.read_sql(
            "SELECT id, company_name, website FROM companies WHERE UPPER(TRIM(id)) = ?",
            conn,
            params=(cid,),
        )
        if comp_df.empty:
            conn.close()
            raise ValueError(f"Company ID '{cid}' not found in database.")

        company_name = comp_df.iloc[0]["company_name"]
        website = comp_df.iloc[0]["website"] or "N/A"

        # Sector
        sec_df = pd.read_sql(
            "SELECT broad_sector, sub_sector, index_weight_pct FROM sectors WHERE UPPER(TRIM(company_id)) = ?",
            conn,
            params=(cid,),
        )
        broad_sector = sec_df.iloc[0]["broad_sector"] if not sec_df.empty else "Diversified"
        sub_sector = sec_df.iloc[0]["sub_sector"] if not sec_df.empty else "General"

        # Financial statements (filter out TTM, sort numeric years)
        pl_df = pd.read_sql(
            "SELECT year, sales, expenses, operating_profit, opm_percentage, net_profit, eps "
            "FROM profitandloss WHERE UPPER(TRIM(company_id)) = ? AND year != 'TTM'",
            conn,
            params=(cid,),
        )
        pl_df["year_int"] = pd.to_numeric(pl_df["year"], errors="coerce")
        pl_df = pl_df.dropna(subset=["year_int"]).sort_values("year_int").reset_index(drop=True)
        pl_df["year_int"] = pl_df["year_int"].astype(int)

        bs_df = pd.read_sql(
            "SELECT year, equity_capital, reserves, borrowings, other_liabilities, total_liabilities, fixed_assets, total_assets "
            "FROM balancesheet WHERE UPPER(TRIM(company_id)) = ? AND year != 'TTM'",
            conn,
            params=(cid,),
        )
        bs_df["year_int"] = pd.to_numeric(bs_df["year"], errors="coerce")
        bs_df = bs_df.dropna(subset=["year_int"]).sort_values("year_int").reset_index(drop=True)
        bs_df["year_int"] = bs_df["year_int"].astype(int)

        cf_df = pd.read_sql(
            "SELECT year, operating_activity, investing_activity, financing_activity, net_cash_flow "
            "FROM cashflow WHERE UPPER(TRIM(company_id)) = ? AND year != 'TTM'",
            conn,
            params=(cid,),
        )
        cf_df["year_int"] = pd.to_numeric(cf_df["year"], errors="coerce")
        cf_df = cf_df.dropna(subset=["year_int"]).sort_values("year_int").reset_index(drop=True)
        cf_df["year_int"] = cf_df["year_int"].astype(int)

        ratios_df = pd.read_sql(
            "SELECT year, net_profit_margin_pct, operating_profit_margin_pct, return_on_equity_pct, "
            "debt_to_equity, return_on_capital_employed_pct "
            "FROM financial_ratios WHERE UPPER(TRIM(company_id)) = ? AND year != 'TTM'",
            conn,
            params=(cid,),
        )
        ratios_df["year_int"] = pd.to_numeric(ratios_df["year"], errors="coerce")
        ratios_df = ratios_df.dropna(subset=["year_int"]).sort_values("year_int").reset_index(drop=True)
        ratios_df["year_int"] = ratios_df["year_int"].astype(int)

        conn.close()

        # Pros & Cons
        pros = []
        cons = []
        if self._pros_cons_df is not None and not self._pros_cons_df.empty:
            c_pc = self._pros_cons_df[self._pros_cons_df["company_id"] == cid]
            pros = c_pc[c_pc["type"].astype(str).str.lower() == "pro"][["text", "confidence_pct", "rule_id"]].to_dict("records")
            cons = c_pc[c_pc["type"].astype(str).str.lower() == "con"][["text", "confidence_pct", "rule_id"]].to_dict("records")

        # Cashflow Intel
        cap_alloc_label = "Shareholder Returns"
        cfo_quality_label = "High Quality"
        capex_label = "Moderate"
        if self._cashflow_intel_df is not None and not self._cashflow_intel_df.empty:
            c_cf = self._cashflow_intel_df[self._cashflow_intel_df["company_id"] == cid]
            if not c_cf.empty:
                cap_alloc_label = str(c_cf.iloc[0].get("capital_allocation_label", "Shareholder Returns"))
                cfo_quality_label = str(c_cf.iloc[0].get("cfo_quality_label", "High Quality"))
                capex_label = str(c_cf.iloc[0].get("capex_label", "Moderate"))

        return {
            "company_id": cid,
            "company_name": company_name,
            "website": website,
            "broad_sector": broad_sector,
            "sub_sector": sub_sector,
            "pl": pl_df,
            "bs": bs_df,
            "cf": cf_df,
            "ratios": ratios_df,
            "pros": pros,
            "cons": cons,
            "capital_allocation_label": cap_alloc_label,
            "cfo_quality_label": cfo_quality_label,
            "capex_label": capex_label,
        }

    # -----------------------------------------------------------------------
    # Matplotlib Chart Generators
    # -----------------------------------------------------------------------

    def _generate_revenue_profit_chart(self, pl_df: pd.DataFrame) -> io.BytesIO:
        df = pl_df.tail(10).copy()
        years = df["year_int"].astype(str).tolist()
        rev = (df["sales"] / 1.0).tolist()
        pat = (df["net_profit"] / 1.0).tolist()

        fig, ax = plt.subplots(figsize=(7.5, 2.7), dpi=200)
        x = np.arange(len(years))
        width = 0.38

        rects1 = ax.bar(x - width / 2, rev, width, label="Revenue (₹ Cr)", color="#1E3A8A", alpha=0.92)
        rects2 = ax.bar(x + width / 2, pat, width, label="Net Profit (₹ Cr)", color="#10B981", alpha=0.92)

        ax.set_xticks(x)
        ax.set_xticklabels(years, fontsize=8, fontweight="medium", color="#334155")
        ax.tick_params(axis="y", labelsize=8, colors="#334155")
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:,.0f}"))
        ax.grid(axis="y", linestyle="--", alpha=0.35, color="#CBD5E1")
        ax.set_axisbelow(True)

        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#CBD5E1")

        ax.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=8, edgecolor="#E2E8F0")
        plt.title("Historical Revenue & Net Profit Growth (10-Year)", fontsize=9.5, fontweight="bold", pad=8, color="#0F172A")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=200)
        plt.close(fig)
        buf.seek(0)
        return buf

    def _generate_roe_roce_chart(self, ratios_df: pd.DataFrame) -> io.BytesIO:
        df = ratios_df.tail(10).copy()
        years = df["year_int"].astype(str).tolist()
        roe = pd.to_numeric(df["return_on_equity_pct"], errors="coerce").fillna(0.0).tolist()
        roce = pd.to_numeric(df["return_on_capital_employed_pct"], errors="coerce").fillna(0.0).tolist()

        fig, ax = plt.subplots(figsize=(7.5, 2.5), dpi=200)
        x = np.arange(len(years))

        ax.plot(x, roe, marker="o", linewidth=2.0, markersize=4.5, label="ROE (%)", color="#7C3AED")
        ax.plot(x, roce, marker="s", linewidth=2.0, markersize=4.5, label="ROCE (%)", color="#D97706")

        ax.axhline(0, color="#94A3B8", linestyle="-", linewidth=0.8, alpha=0.6)
        ax.axhline(15, color="#10B981", linestyle=":", linewidth=0.8, alpha=0.7, label="15% Benchmark")

        ax.set_xticks(x)
        ax.set_xticklabels(years, fontsize=8, fontweight="medium", color="#334155")
        ax.tick_params(axis="y", labelsize=8, colors="#334155")
        ax.yaxis.set_major_formatter(ticker.PercentFormatter(decimals=0))
        ax.grid(axis="y", linestyle="--", alpha=0.35, color="#CBD5E1")
        ax.set_axisbelow(True)

        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#CBD5E1")

        ax.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=8, edgecolor="#E2E8F0")
        plt.title("Return Metrics: ROE vs ROCE Trend", fontsize=9.5, fontweight="bold", pad=8, color="#0F172A")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=200)
        plt.close(fig)
        buf.seek(0)
        return buf

    def _generate_bs_composition_chart(self, bs_df: pd.DataFrame) -> io.BytesIO:
        df = bs_df.tail(8).copy()
        years = df["year_int"].astype(str).tolist()
        equity = (df["equity_capital"] + df["reserves"]).clip(lower=0).tolist()
        borrowings = df["borrowings"].clip(lower=0).tolist()
        other_liab = df["other_liabilities"].clip(lower=0).tolist()

        fig, ax = plt.subplots(figsize=(7.5, 2.2), dpi=200)
        x = np.arange(len(years))
        width = 0.52

        p1 = ax.bar(x, equity, width, label="Equity & Reserves", color="#2563EB", alpha=0.9)
        p2 = ax.bar(x, borrowings, width, bottom=equity, label="Borrowings (Debt)", color="#EF4444", alpha=0.9)
        bottom_3 = [e + b for e, b in zip(equity, borrowings)]
        p3 = ax.bar(x, other_liab, width, bottom=bottom_3, label="Other Liabilities", color="#94A3B8", alpha=0.9)

        ax.set_xticks(x)
        ax.set_xticklabels(years, fontsize=8, fontweight="medium", color="#334155")
        ax.tick_params(axis="y", labelsize=8, colors="#334155")
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:,.0f}"))
        ax.grid(axis="y", linestyle="--", alpha=0.35, color="#CBD5E1")
        ax.set_axisbelow(True)

        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#CBD5E1")

        ax.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=7.5, edgecolor="#E2E8F0", ncol=3)
        plt.title("Capital Structure & Liabilities (₹ Cr)", fontsize=9, fontweight="bold", pad=6, color="#0F172A")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=200)
        plt.close(fig)
        buf.seek(0)
        return buf

    def _generate_cashflow_waterfall_chart(self, cf_df: pd.DataFrame) -> io.BytesIO:
        latest = cf_df.iloc[-1]
        cfo = float(latest.get("operating_activity", 0.0) or 0.0)
        cfi = float(latest.get("investing_activity", 0.0) or 0.0)
        cff = float(latest.get("financing_activity", 0.0) or 0.0)
        net_cf = float(latest.get("net_cash_flow", 0.0) or 0.0)

        labels = ["CFO (Operating)", "CFI (Investing)", "CFF (Financing)", "Net Cash Flow"]
        vals = [cfo, cfi, cff, net_cf]
        colors_list = [
            "#10B981" if cfo >= 0 else "#EF4444",
            "#10B981" if cfi >= 0 else "#EF4444",
            "#10B981" if cff >= 0 else "#EF4444",
            "#1E3A8A" if net_cf >= 0 else "#DC2626",
        ]

        fig, ax = plt.subplots(figsize=(7.5, 1.8), dpi=200)
        x = np.arange(len(labels))
        width = 0.45

        bars = ax.bar(x, vals, width, color=colors_list, alpha=0.92)
        ax.axhline(0, color="#64748B", linewidth=0.9)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=7.5, fontweight="medium", color="#334155")
        ax.tick_params(axis="y", labelsize=7.5, colors="#334155")
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:,.0f}"))
        ax.grid(axis="y", linestyle="--", alpha=0.35, color="#CBD5E1")
        ax.set_axisbelow(True)

        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#CBD5E1")

        # Annotate values
        for bar, val in zip(bars, vals):
            va = "bottom" if val >= 0 else "top"
            y_offset = (max(vals) - min(vals)) * 0.03 if (max(vals) - min(vals)) > 0 else 1
            y_pos = val + (y_offset if val >= 0 else -y_offset)
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                y_pos,
                f"₹{val:,.0f} Cr",
                ha="center",
                va=va,
                fontsize=7,
                fontweight="bold",
                color="#0F172A",
            )

        plt.title(f"FY{latest['year_int']} Cash Flow Waterfall Bridge (₹ Cr)", fontsize=9, fontweight="bold", pad=6, color="#0F172A")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", dpi=200)
        plt.close(fig)
        buf.seek(0)
        return buf

    # -----------------------------------------------------------------------
    # PDF Document Construction
    # -----------------------------------------------------------------------

    def generate_tearsheet(self, company_id: str, output_path: Optional[str] = None) -> Path:
        """
        Builds the 2-page tearsheet PDF for a specific company.
        """
        data = self.fetch_company_data(company_id)
        cid = data["company_id"]
        cname = data["company_name"]
        sector = data["broad_sector"]

        # Validate minimum usable data (at least 3 years)
        if len(data["pl"]) < 3:
            raise ValueError(f"Company {cid} has fewer than 3 years of financial history ({len(data['pl'])} years).")

        out_file = Path(output_path) if output_path else self.output_dir / f"{cid}_tearsheet.pdf"
        out_file.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(out_file),
            pagesize=A4,
            leftMargin=24,
            rightMargin=24,
            topMargin=20,
            bottomMargin=20,
        )

        story = []
        styles = getSampleStyleSheet()

        # Custom paragraph styles
        header_title_style = ParagraphStyle(
            "HeaderTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            textColor=colors.white,
            leading=18,
        )
        header_sub_style = ParagraphStyle(
            "HeaderSub",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            textColor=colors.HexColor("#E2E8F0"),
            leading=11,
        )
        kpi_label_style = ParagraphStyle(
            "KPILabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            textColor=colors.HexColor("#64748B"),
            alignment=1,  # Center
            leading=9,
        )
        kpi_value_style = ParagraphStyle(
            "KPIVal",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            textColor=colors.HexColor("#0F172A"),
            alignment=1,  # Center
            leading=14,
        )
        section_title_style = ParagraphStyle(
            "SecTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.HexColor("#0F2942"),
            leading=13,
        )
        badge_style = ParagraphStyle(
            "BadgeStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            textColor=colors.HexColor("#1E3A8A"),
            leading=11,
        )
        pro_text_style = ParagraphStyle(
            "ProText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            textColor=colors.HexColor("#065F46"),
            leading=9.5,
        )
        con_text_style = ParagraphStyle(
            "ConText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            textColor=colors.HexColor("#991B1B"),
            leading=9.5,
        )

        usable_width = 547.0

        # ===================================================================
        # PAGE 1
        # ===================================================================

        # 1. Navy Header Bar
        header_p1 = Paragraph(f"<b>{cname}</b>", header_title_style)
        header_p2 = Paragraph(f"TICKER: <b>{cid}</b> &nbsp;|&nbsp; SECTOR: <b>{sector}</b> &nbsp;|&nbsp; NIFTY 100", header_sub_style)
        header_table = Table([[header_p1], [header_p2]], colWidths=[usable_width])
        header_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0F2942")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        story.append(header_table)
        story.append(Spacer(1, 8))

        # 2. Six KPI Tiles (2 rows x 3 columns)
        latest_pl = data["pl"].iloc[-1]
        latest_ratios = data["ratios"].iloc[-1] if not data["ratios"].empty else pd.Series()

        rev_val = f"Rs. {latest_pl.get('sales', 0.0):,.0f} Cr"
        pat_val = f"Rs. {latest_pl.get('net_profit', 0.0):,.0f} Cr"
        roe_val = f"{latest_ratios.get('return_on_equity_pct', 0.0):.1f}%" if pd.notna(latest_ratios.get("return_on_equity_pct")) else "N/A"
        roce_val = f"{latest_ratios.get('return_on_capital_employed_pct', 0.0):.1f}%" if pd.notna(latest_ratios.get("return_on_capital_employed_pct")) else "N/A"
        de_val = f"{latest_ratios.get('debt_to_equity', 0.0):.2f}x" if pd.notna(latest_ratios.get("debt_to_equity")) else "0.00x"
        opm_val = f"{latest_pl.get('opm_percentage', 0.0):.1f}%" if pd.notna(latest_pl.get("opm_percentage")) else "N/A"

        def make_tile(label: str, val: str) -> Table:
            t = Table(
                [[Paragraph(label, kpi_label_style)], [Paragraph(val, kpi_value_style)]],
                colWidths=[usable_width / 3.05],
            )
            t.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#E2E8F0")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ])
            )
            return t

        kpi_grid = Table(
            [
                [make_tile("REVENUE (LATEST FY)", rev_val), make_tile("NET PROFIT (LATEST FY)", pat_val), make_tile("OPERATING MARGIN", opm_val)],
                [make_tile("RETURN ON EQUITY (ROE)", roe_val), make_tile("ROCE", roce_val), make_tile("DEBT / EQUITY", de_val)],
            ],
            colWidths=[usable_width / 3.0, usable_width / 3.0, usable_width / 3.0],
        )
        kpi_grid.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ])
        )
        story.append(kpi_grid)
        story.append(Spacer(1, 10))

        # 3. Chart 1: Revenue & Net Profit Trend
        buf_rev = self._generate_revenue_profit_chart(data["pl"])
        story.append(Image(buf_rev, width=usable_width, height=205))
        story.append(Spacer(1, 10))

        # 4. Chart 2: ROE & ROCE Trend
        buf_roe = self._generate_roe_roce_chart(data["ratios"] if not data["ratios"].empty else pd.DataFrame([{"year_int": 2024, "return_on_equity_pct": 0, "return_on_capital_employed_pct": 0}]))
        story.append(Image(buf_roe, width=usable_width, height=190))

        # End of Page 1
        story.append(PageBreak())

        # ===================================================================
        # PAGE 2
        # ===================================================================

        # Top banner on Page 2
        p2_header = Table(
            [[Paragraph(f"<b>{cname} ({cid})</b> — Balance Sheet & Cash Flow Intelligence", header_sub_style)]],
            colWidths=[usable_width],
        )
        p2_header.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0F2942")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        story.append(p2_header)
        story.append(Spacer(1, 6))

        # Balance Sheet Stacked Bar Chart
        if not data["bs"].empty and len(data["bs"]) >= 2:
            buf_bs = self._generate_bs_composition_chart(data["bs"])
            story.append(Image(buf_bs, width=usable_width, height=160))
            story.append(Spacer(1, 6))

        # Cash Flow Waterfall Bridge Chart
        if not data["cf"].empty:
            buf_cf = self._generate_cashflow_waterfall_chart(data["cf"])
            story.append(Image(buf_cf, width=usable_width, height=135))
            story.append(Spacer(1, 6))

        # Capital Allocation Badge Bar
        cap_pattern = data["capital_allocation_label"]
        cfo_q = data["cfo_quality_label"]
        capex_int = data["capex_label"]

        cap_box = Table(
            [[
                Paragraph(f"<b>Capital Allocation Pattern:</b> {cap_pattern}", badge_style),
                Paragraph(f"<b>CFO Quality:</b> {cfo_q}", badge_style),
                Paragraph(f"<b>CapEx Profile:</b> {capex_int}", badge_style),
            ]],
            colWidths=[usable_width * 0.40, usable_width * 0.30, usable_width * 0.30],
        )
        cap_box.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#93C5FD")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        story.append(cap_box)
        story.append(Spacer(1, 8))

        # Pros & Cons Side-by-Side Cards
        pros_list = data["pros"][:4]  # Top up to 4
        cons_list = data["cons"][:4]  # Top up to 4

        pro_flowables = [Paragraph("<b>PROS / STRENGTHS</b>", ParagraphStyle("ProH", fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.HexColor("#065F46")))]
        if pros_list:
            for p in pros_list:
                pro_flowables.append(Paragraph(f"• <b>[{p['rule_id']}]</b> {p['text']} (<i>{p['confidence_pct']:.0f}% conf</i>)", pro_text_style))
                pro_flowables.append(Spacer(1, 2))
        else:
            pro_flowables.append(Paragraph("• No high-confidence positive signals identified for standard criteria.", pro_text_style))

        con_flowables = [Paragraph("<b>CONS / RISKS</b>", ParagraphStyle("ConH", fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.HexColor("#991B1B")))]
        if cons_list:
            for c in cons_list:
                con_flowables.append(Paragraph(f"• <b>[{c['rule_id']}]</b> {c['text']} (<i>{c['confidence_pct']:.0f}% conf</i>)", con_text_style))
                con_flowables.append(Spacer(1, 2))
        else:
            con_flowables.append(Paragraph("• No high-confidence risk signals identified for standard criteria.", con_text_style))

        col_w = (usable_width - 10) / 2.0
        pro_card = Table([[pro_flowables]], colWidths=[col_w])
        pro_card.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#A7F3D0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )

        con_card = Table([[con_flowables]], colWidths=[col_w])
        con_card.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#FECACA")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )

        pc_table = Table([[pro_card, con_card]], colWidths=[col_w + 5, col_w + 5])
        pc_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ])
        )
        story.append(pc_table)

        doc.build(story)
        return out_file

    def generate_all_batch(self) -> Tuple[List[Path], List[Dict[str, Any]]]:
        """
        Generates tearsheets for all 92 companies, skipping any with < 3 years of history.
        Saves skipped info to output/skipped_tearsheets.csv.
        """
        conn = sqlite3.connect(str(self.db_path))
        companies_df = pd.read_sql("SELECT id, company_name FROM companies ORDER BY id", conn)
        conn.close()

        generated: List[Path] = []
        skipped: List[Dict[str, Any]] = []

        for _, row in companies_df.iterrows():
            cid = str(row["id"]).strip().upper()
            try:
                data = self.fetch_company_data(cid)
                yr_cnt = len(data["pl"])
                if yr_cnt < 3:
                    skipped.append({
                        "company_id": cid,
                        "ticker": cid,
                        "reason": f"Insufficient financial history (< 3 years)",
                        "available_years": yr_cnt,
                    })
                    continue

                pdf_path = self.generate_tearsheet(cid)
                generated.append(pdf_path)
            except Exception as e:
                skipped.append({
                    "company_id": cid,
                    "ticker": cid,
                    "reason": f"Generation error: {str(e)}",
                    "available_years": 0,
                })

        # Save skipped tearsheets log
        skipped_df = pd.DataFrame(skipped)
        if skipped_df.empty:
            skipped_df = pd.DataFrame(columns=["company_id", "ticker", "reason", "available_years"])

        skip_path = self.data_dir / "skipped_tearsheets.csv"
        skipped_df.to_csv(skip_path, index=False)

        return generated, skipped


if __name__ == "__main__":
    gen = TearsheetGenerator()
    print("Testing single generation for TCS...")
    p = gen.generate_tearsheet("TCS")
    print(f"Generated {p} ({p.stat().st_size / 1024:.1f} KB)")

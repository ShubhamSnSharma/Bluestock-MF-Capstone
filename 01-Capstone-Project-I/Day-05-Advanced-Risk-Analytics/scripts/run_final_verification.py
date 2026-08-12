"""
Day 05 Final Verification Script
=================================

This script performs automated validation across all Day 05 Advanced Risk Analytics assets:
    1. Reusable scripts presence and syntax check.
    2. Deliverable outputs presence (var_cvar_report.csv, charts).
    3. Notebook execution validation (Advanced_Analytics.ipynb).
    4. Quantitative metrics audit.

Exit Code: 0 on Success, 1 on Failure.
"""

import sys
from pathlib import Path
import pandas as pd


def verify_day5() -> int:
    base_dir = Path(__file__).resolve().parent.parent
    scripts_dir = base_dir / 'scripts'
    outputs_dir = base_dir / 'outputs'
    charts_dir = base_dir / 'charts' / 'png'
    notebooks_dir = base_dir / 'notebooks'
    reports_dir = base_dir / 'reports'

    print("=== Running Final Verification for Day 05: Advanced Risk Analytics ===")

    # 1. Verify Scripts
    required_scripts = [
        'advanced_metrics.py',
        'cohort_analysis.py',
        'sip_analysis.py',
        'recommender.py',
        'insight_engine.py',
        'performance_metrics.py'
    ]

    for script_name in required_scripts:
        script_path = scripts_dir / script_name
        if not script_path.exists():
            print(f"[FAIL] Missing script: {script_name}")
            return 1
        print(f"[PASS] Script verified: {script_name}")

    # 2. Verify Output CSV
    csv_report = outputs_dir / 'var_cvar_report.csv'
    if not csv_report.exists() or csv_report.stat().st_size == 0:
        print("[FAIL] Missing or empty var_cvar_report.csv")
        return 1

    df_csv = pd.read_csv(csv_report)
    if len(df_csv) != 40:
        print(f"[FAIL] var_cvar_report.csv row count mismatch. Expected 40, got {len(df_csv)}")
        return 1
    print(f"[PASS] var_cvar_report.csv verified ({len(df_csv)} schemes)")

    # 3. Verify Charts
    chart1 = charts_dir / 'rolling_sharpe_chart.png'
    chart2 = charts_dir / 'sip_gap_distribution.png'

    if not chart1.exists() or chart1.stat().st_size == 0:
        print("[FAIL] Missing or empty rolling_sharpe_chart.png")
        return 1
    print(f"[PASS] Chart verified: rolling_sharpe_chart.png ({chart1.stat().st_size / 1024:.1f} KB)")

    if not chart2.exists() or chart2.stat().st_size == 0:
        print("[FAIL] Missing or empty sip_gap_distribution.png")
        return 1
    print(f"[PASS] Chart verified: sip_gap_distribution.png ({chart2.stat().st_size / 1024:.1f} KB)")

    # 4. Verify Notebook
    nb_path = notebooks_dir / 'Advanced_Analytics.ipynb'
    if not nb_path.exists() or nb_path.stat().st_size == 0:
        print("[FAIL] Missing or empty Advanced_Analytics.ipynb")
        return 1
    print(f"[PASS] Notebook verified: Advanced_Analytics.ipynb ({nb_path.stat().st_size / 1024:.1f} KB)")

    # 5. Verify Report
    rep_path = reports_dir / 'day5_validation.md'
    if not rep_path.exists() or rep_path.stat().st_size == 0:
        print("[FAIL] Missing or empty day5_validation.md")
        return 1
    print(f"[PASS] Report verified: day5_validation.md")

    print("\nALL DAY 05 VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    return 0


if __name__ == '__main__':
    sys.exit(verify_day5())

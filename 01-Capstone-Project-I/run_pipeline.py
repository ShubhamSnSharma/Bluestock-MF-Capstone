"""
Bluestock Mutual Fund Analytics — Master Execution Pipeline
===========================================================

This module serves as the primary master orchestration entry point for the
Bluestock Mutual Fund Analytics project. It coordinates and executes the complete
multi-stage data engineering and quantitative analytics workflow in sequential order:

  Stage 1: Raw Data Ingestion & Profiling (Day 01)
  Stage 2: Automated Data Cleaning & Validation (Day 02)
  Stage 3: SQLite Database Star-Schema Build & Population (Day 02)
  Stage 4: Analytical SQL Query Suite Execution (Day 02)
  Stage 5: Fund Performance & Multi-Factor Scorecard Analytics (Day 04)
  Stage 6: Advanced Risk, Tail Loss (VaR/CVaR) & Investor Retention (Day 05)

Usage:
  python run_pipeline.py
"""

import sys
import time
import subprocess
from pathlib import Path


def run_stage(stage_num: int, total_stages: int, name: str, script_path: Path, cwd: Path) -> None:
    """
    Executes an individual pipeline stage script as a subprocess.

    Args:
        stage_num (int): The current stage index.
        total_stages (int): Total number of pipeline stages.
        name (str): Human-readable name of the stage.
        script_path (Path): Absolute path to the python script to execute.
        cwd (Path): Working directory for the subprocess execution.

    Raises:
        FileNotFoundError: If the script does not exist.
        RuntimeError: If the script execution exits with a non-zero return code.
    """
    if not script_path.exists():
        raise FileNotFoundError(f"Pipeline script not found: {script_path}")

    header = f"[{stage_num}/{total_stages}] {name}"
    print("\n" + "=" * 80)
    print(header)
    print("=" * 80)
    print(f"Script: {script_path.relative_to(cwd.parent if cwd.parent.exists() else cwd)}")
    print(f"Working Directory: {cwd}\n")

    start_time = time.time()

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(cwd),
        text=True
    )

    duration = time.time() - start_time

    if result.returncode != 0:
        error_msg = (
            f"\n❌ Stage Failed: {name}\n"
            f"   Script: {script_path}\n"
            f"   Exit Code: {result.returncode}\n"
            f"   Pipeline execution aborted."
        )
        print(error_msg, file=sys.stderr)
        raise RuntimeError(error_msg)

    print(f"\n✅ {header} — COMPLETED ({duration:.2f}s)")


def main() -> None:
    """
    Main entry point orchestrating the full Bluestock Mutual Fund Analytics pipeline.
    """
    repo_root = Path(__file__).resolve().parent

    stages = [
        (
            "Raw Data Ingestion & Profiling",
            repo_root / "Day-01-Project-Setup-ETL" / "data_ingestion.py",
            repo_root / "Day-01-Project-Setup-ETL"
        ),
        (
            "Automated Data Cleaning & Transformation",
            repo_root / "Day-02-Data-Cleaning-SQL" / "scripts" / "run_cleaning_pipeline.py",
            repo_root / "Day-02-Data-Cleaning-SQL"
        ),
        (
            "SQLite Star-Schema Database Build & Table Population",
            repo_root / "Day-02-Data-Cleaning-SQL" / "scripts" / "build_database.py",
            repo_root / "Day-02-Data-Cleaning-SQL"
        ),
        (
            "Analytical SQL Query Suite Execution",
            repo_root / "Day-02-Data-Cleaning-SQL" / "scripts" / "execute_queries.py",
            repo_root / "Day-02-Data-Cleaning-SQL"
        ),
        (
            "Fund Performance & Multi-Factor Scorecard Analytics",
            repo_root / "Day-04-Fund-Performance-Analytics" / "scripts" / "run_final_verification.py",
            repo_root / "Day-04-Fund-Performance-Analytics"
        ),
        (
            "Advanced Risk, Tail Loss (VaR/CVaR) & Investor Analytics",
            repo_root / "Day-05-Advanced-Risk-Analytics" / "scripts" / "run_final_verification.py",
            repo_root / "Day-05-Advanced-Risk-Analytics"
        )
    ]

    total_stages = len(stages)
    overall_start = time.time()

    print("*" * 80)
    print("BLUESTOCK MUTUAL FUND ANALYTICS PLATFORM — MASTER PIPELINE")
    print(f"Repository Root: {repo_root}")
    print(f"Total Stages Scheduled: {total_stages}")
    print("*" * 80)

    for i, (name, script_path, cwd) in enumerate(stages, start=1):
        try:
            run_stage(i, total_stages, name, script_path, cwd)
        except Exception as e:
            print(f"\nFATAL PIPELINE ERROR: {e}", file=sys.stderr)
            sys.exit(1)

    total_duration = time.time() - overall_start

    print("\n" + "*" * 80)
    print("🎉 ALL PIPELINE STAGES EXECUTED AND VALIDATED SUCCESSFULLY!")
    print(f"Total Pipeline Runtime: {total_duration:.2f}s")
    print(f"Relational Database: {repo_root / 'Day-02-Data-Cleaning-SQL' / 'database' / 'bluestock_mf.db'}")
    print(f"Tableau Deliverables: {repo_root / 'Day-06-PowerBI-Dashboard-Design' / 'tableau'}")
    print("*" * 80 + "\n")


if __name__ == "__main__":
    main()

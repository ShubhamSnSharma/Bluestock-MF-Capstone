"""
Unit and integration tests for ETL Loader pipeline.
"""

import sqlite3
import pytest
from pathlib import Path
import pandas as pd

from src.etl.loader import N100DataLoader, resolve_base_dir


@pytest.fixture(scope="module")
def loaded_db():
    """Initializes and executes test database load."""
    base_dir = resolve_base_dir()
    test_db_name = "test_nifty100.db"
    loader = N100DataLoader(
        base_dir=str(base_dir),
        db_filename=test_db_name
    )
    conn = loader.run_pipeline()
    yield conn, loader
    conn.close()
    test_db_path = base_dir / test_db_name
    if test_db_path.exists():
        test_db_path.unlink()


def test_companies_count(loaded_db):
    conn, _ = loaded_db
    count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    assert count == 92


def test_pragma_foreign_key_check(loaded_db):
    conn, _ = loaded_db
    fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert len(fk_errors) == 0


def test_all_twelve_tables_populated(loaded_db):
    conn, _ = loaded_db
    tables = [
        "companies", "profitandloss", "balancesheet", "cashflow",
        "analysis", "documents", "prosandcons", "financial_ratios",
        "market_cap", "peer_groups", "sectors", "stock_prices"
    ]
    for table in tables:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert cnt > 0, f"Table {table} has 0 records"


def test_stock_prices_row_count(loaded_db):
    conn, _ = loaded_db
    cnt = conn.execute("SELECT COUNT(*) FROM stock_prices").fetchone()[0]
    assert cnt == 5520


def test_market_cap_row_count(loaded_db):
    conn, _ = loaded_db
    cnt = conn.execute("SELECT COUNT(*) FROM market_cap").fetchone()[0]
    assert cnt == 552


def test_sectors_row_count(loaded_db):
    conn, _ = loaded_db
    cnt = conn.execute("SELECT COUNT(*) FROM sectors").fetchone()[0]
    assert cnt == 92


def test_load_audit_output_exists():
    base_dir = resolve_base_dir()
    audit_file = base_dir / "output" / "load_audit.csv"
    assert audit_file.exists()
    df = pd.read_csv(audit_file)
    assert len(df) == 12
    assert "accepted_db_records" in df.columns


def test_validation_failures_output_exists():
    base_dir = resolve_base_dir()
    failures_file = base_dir / "output" / "validation_failures.csv"
    assert failures_file.exists()
    df = pd.read_csv(failures_file)
    assert "rule_id" in df.columns
    assert "severity" in df.columns

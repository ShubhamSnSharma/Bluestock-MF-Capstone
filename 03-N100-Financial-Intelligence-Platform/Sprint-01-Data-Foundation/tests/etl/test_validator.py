"""
Unit test suite for DQ Validator module (DQ-01 to DQ-16).
"""

import pytest
import pandas as pd
import numpy as np

from src.etl.validator import DataQualityValidator


def test_dq01_primary_key_uniqueness():
    validator = DataQualityValidator()
    df_valid = pd.DataFrame([{"id": 1}, {"id": 2}, {"id": 3}])
    assert validator.validate_dq01_primary_key_uniqueness(df_valid, "test_table") is True
    assert len(validator.failures) == 0

    df_dup = pd.DataFrame([{"id": 1}, {"id": 1}, {"id": 2}])
    assert validator.validate_dq01_primary_key_uniqueness(df_dup, "test_table") is False
    assert len(validator.failures) > 0
    assert validator.failures[0]["rule_id"] == "DQ-01"


def test_dq02_natural_key_uniqueness():
    validator = DataQualityValidator()
    df_valid = pd.DataFrame([
        {"company_id": "TCS", "year": "2023"},
        {"company_id": "TCS", "year": "2024"},
        {"company_id": "INFY", "year": "2023"}
    ])
    assert validator.validate_dq02_natural_key_uniqueness(df_valid, "pnl", ["company_id", "year"]) is True

    df_dup = pd.DataFrame([
        {"company_id": "TCS", "year": "2023"},
        {"company_id": "TCS", "year": "2023"}
    ])
    assert validator.validate_dq02_natural_key_uniqueness(df_dup, "pnl", ["company_id", "year"]) is False
    assert validator.failures[0]["rule_id"] == "DQ-02"


def test_dq03_foreign_key_integrity():
    validator = DataQualityValidator()
    valid_cids = {"ABB", "TCS", "INFY"}
    df = pd.DataFrame([
        {"id": 1, "company_id": "ABB"},
        {"id": 2, "company_id": "WIPRO"}  # Orphan
    ])
    orphans = validator.validate_dq03_foreign_key_integrity(df, "pnl", valid_cids)
    assert "WIPRO" in orphans
    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-03"


def test_dq04_balancesheet_balance():
    validator = DataQualityValidator()
    df_pass = pd.DataFrame([{"company_id": "ABB", "year": "2024", "total_assets": 1000, "total_liabilities": 1000}])
    validator.validate_dq04_balancesheet_balance(df_pass)
    assert len(validator.failures) == 0

    df_fail = pd.DataFrame([{"company_id": "ABB", "year": "2024", "total_assets": 1000, "total_liabilities": 900}])
    validator.validate_dq04_balancesheet_balance(df_fail)
    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-04"


def test_dq05_opm_cross_check():
    validator = DataQualityValidator()
    # Operating profit 200 on 1000 sales = 20% OPM
    df_pass = pd.DataFrame([{"company_id": "ABB", "year": "2024", "sales": 1000, "operating_profit": 200, "opm_percentage": 20.0}])
    validator.validate_dq05_opm_cross_check(df_pass)
    assert len(validator.failures) == 0

    df_fail = pd.DataFrame([{"company_id": "ABB", "year": "2024", "sales": 1000, "operating_profit": 200, "opm_percentage": 35.0}])
    validator.validate_dq05_opm_cross_check(df_fail)
    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-05"


def test_dq06_positive_sales():
    validator = DataQualityValidator()
    df_pass = pd.DataFrame([{"company_id": "ABB", "year": "2024", "sales": 1500}])
    validator.validate_dq06_positive_sales(df_pass)
    assert len(validator.failures) == 0

    df_fail = pd.DataFrame([{"company_id": "ADANIENSOL", "year": "2014", "sales": 0}])
    validator.validate_dq06_positive_sales(df_fail)
    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-06"


def test_dq07_net_cash_flow_sum():
    validator = DataQualityValidator()
    df_pass = pd.DataFrame([{"company_id": "ABB", "year": "2024", "operating_activity": 100, "investing_activity": -40, "financing_activity": -50, "net_cash_flow": 10}])
    validator.validate_dq07_net_cash_flow_sum(df_pass)
    assert len(validator.failures) == 0

    df_fail = pd.DataFrame([{"company_id": "ABB", "year": "2024", "operating_activity": 100, "investing_activity": -40, "financing_activity": -50, "net_cash_flow": 50}])
    validator.validate_dq07_net_cash_flow_sum(df_fail)
    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-07"


def test_dq08_tax_rate_sanity():
    validator = DataQualityValidator()
    df_pass = pd.DataFrame([{"company_id": "ABB", "year": "2024", "tax_percentage": 25.0}])
    validator.validate_dq08_tax_rate_sanity(df_pass)
    assert len(validator.failures) == 0

    df_fail = pd.DataFrame([{"company_id": "ABB", "year": "2024", "tax_percentage": -64.0}])
    validator.validate_dq08_tax_rate_sanity(df_fail)
    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-08"


def test_dq10_url_syntax():
    validator = DataQualityValidator()
    df_pass = pd.DataFrame([{"id": 1, "website": "https://www.abbott.co.in"}])
    validator.validate_dq10_url_syntax(df_pass, "companies", ["website"])
    assert len(validator.failures) == 0

    df_fail = pd.DataFrame([{"id": 2, "website": "ftp://bad-domain"}])
    validator.validate_dq10_url_syntax(df_fail, "companies", ["website"])
    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-10"


def test_dq11_eps_sign_consistency():
    validator = DataQualityValidator()
    df_pass = pd.DataFrame([{"company_id": "ABB", "year": "2024", "net_profit": 150, "eps": 25.0}])
    validator.validate_dq11_eps_sign_consistency(df_pass)
    assert len(validator.failures) == 0

    df_fail = pd.DataFrame([{"company_id": "ABB", "year": "2024", "net_profit": 150, "eps": -25.0}])
    validator.validate_dq11_eps_sign_consistency(df_fail)
    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-11"


def test_dq15_stock_prices_range():
    validator = DataQualityValidator()
    df_pass = pd.DataFrame([{
        "company_id": "ABB", "date": "2024-01-01",
        "open_price": 100.0, "high_price": 110.0, "low_price": 95.0, "close_price": 105.0, "volume": 1000
    }])
    validator.validate_dq15_stock_prices_range(df_pass)
    assert len(validator.failures) == 0

    df_fail = pd.DataFrame([{
        "company_id": "ABB", "date": "2024-01-01",
        "open_price": 120.0, "high_price": 110.0, "low_price": 95.0, "close_price": 105.0, "volume": 1000
    }])
    validator.validate_dq15_stock_prices_range(df_fail)
    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-15"

import os
import pandas as pd
import pytest
import csv
from scripts.generate_customers import generate_customer_csv

@pytest.fixture
def temp_csv_path(tmp_path):
    return tmp_path / "test_customers.csv"

@pytest.mark.unit
def test_csv_has_correct_columns(temp_csv_path):
    """Asserts columns are Name, Email, Age, Country, Subscription_Type"""
    generate_customer_csv(temp_csv_path, num_rows=10)

    with open(temp_csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)

    expected_columns = ["Name", "Email", "Age", "Country", "Subscription_Type"]
    assert header == expected_columns

@pytest.mark.unit
def test_csv_has_expected_row_count(temp_csv_path):
    """Asserts row count matches requested count"""
    count = 50
    generate_customer_csv(temp_csv_path, num_rows=count)
    df = pd.read_csv(temp_csv_path)
    assert len(df) == count

@pytest.mark.unit
def test_csv_contains_minors(temp_csv_path):
    """Asserts at least one row where Age < 18 (when requested)"""
    # Using a large enough sample to ensure probability hits
    generate_customer_csv(temp_csv_path, num_rows=100, minor_probability=0.5)
    df = pd.read_csv(temp_csv_path)
    assert (df['Age'] < 18).any()

@pytest.mark.unit
def test_csv_contains_restricted_regions(temp_csv_path):
    """Asserts at least one row where Country == 'GDPR_Restricted_Zone'"""
    generate_customer_csv(temp_csv_path, num_rows=100, restricted_region_probability=0.5)
    df = pd.read_csv(temp_csv_path)
    assert (df['Country'] == "GDPR_Restricted_Zone").any()

@pytest.mark.unit
def test_csv_emails_are_unique(temp_csv_path):
    """Asserts no duplicate emails"""
    generate_customer_csv(temp_csv_path, num_rows=100)
    df = pd.read_csv(temp_csv_path)
    assert df['Email'].is_unique

@pytest.mark.unit
def test_csv_is_deterministic(temp_csv_path, tmp_path):
    """Asserts two runs with same seed produce identical output"""
    path1 = tmp_path / "c1.csv"
    path2 = tmp_path / "c2.csv"
    seed = 42

    generate_customer_csv(path1, num_rows=100, seed=seed)
    generate_customer_csv(path2, num_rows=100, seed=seed)

    with open(path1, 'r') as f1, open(path2, 'r') as f2:
        assert f1.read() == f2.read()

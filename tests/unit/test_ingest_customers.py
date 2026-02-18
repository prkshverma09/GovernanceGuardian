import pytest
import os
import csv
from scripts.ingest_customers import transform_row

@pytest.mark.unit
def test_record_transformation():
    """Verify a CSV row is correctly transformed to an ES document."""
    row = {
        "Name": "John Doe",
        "Email": "john@example.com",
        "Age": "25",
        "Country": "USA",
        "Subscription_Type": "Pro"
    }
    doc = transform_row(row)

    assert doc["Name"] == "John Doe"
    assert doc["Email"] == "john@example.com"
    assert doc["Age"] == 25
    assert doc["Country"] == "USA"
    assert doc["Subscription_Type"] == "Pro"

@pytest.mark.unit
def test_record_transformation_handles_integers():
    """Verify Age is converted to integer."""
    row = {"Age": "17"}
    doc = transform_row(row)
    assert doc["Age"] == 17
    assert isinstance(doc["Age"], int)

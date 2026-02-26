#!/usr/bin/env python3
"""
Generate synthetic data access logs for the Time-Series Auditor feature.

Output: CSV with timestamp, user, ip_address, region, records_downloaded, dataset_name.
Some rows simulate anomalies (e.g. non-EU IP downloading large GDPR datasets).
"""
import csv
import os
import random
from datetime import datetime, timedelta, timezone
from faker import Faker

def generate_access_logs_csv(
    output_path,
    num_rows=500,
    seed=42,
    anomaly_probability=0.08,
):
    """
    Generates synthetic database access logs.
    Columns: timestamp, user, ip_address, region, records_downloaded, dataset_name
    """
    fake = Faker()
    Faker.seed(seed)
    random.seed(seed)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    header = ["timestamp", "user", "ip_address", "region", "records_downloaded", "dataset_name"]
    datasets = ["customer_leads_prod", "customer_leads_safe", "legal-knowledge-base", "data_export_v2"]
    regions = ["US", "EU", "UK", "APAC", "LATAM"]
    # Simulate some "restricted" access (e.g. non-EU IP accessing EU data)
    anomaly_regions = ["non_EU_high_volume", "EU", "US"]  # mix for variety

    with open(output_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        base_time = datetime.now(timezone.utc) - timedelta(days=30)
        for i in range(num_rows):
            ts = base_time + timedelta(
                seconds=random.randint(0, 30 * 24 * 3600),
                minutes=random.randint(0, 59),
            )
            timestamp = ts.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            user = fake.user_name() if i % 3 else f"service-{random.randint(1, 20)}"
            ip_address = fake.ipv4()
            if random.random() < anomaly_probability:
                region = random.choice(anomaly_regions)
                records_downloaded = random.randint(2000, 50000)
            else:
                region = random.choice(regions)
                records_downloaded = random.randint(1, 5000)
            dataset_name = random.choice(datasets)
            writer.writerow([timestamp, user, ip_address, region, records_downloaded, dataset_name])

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target = os.path.join(base_dir, "data", "access_logs.csv")
    print(f"Generating synthetic access logs: {target}")
    generate_access_logs_csv(target)
    print("Done.")

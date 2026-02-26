#!/usr/bin/env python3
"""
One-command setup of all test data so every sidebar example query has data to work with.

This script:
  1. Generates data/customers.csv (if missing) and ingests into customer_leads_prod
  2. Generates data/access_logs.csv and ingests into data_access_logs_prod

After running, you still need:
  - legal-knowledge-base: run `python scripts/ingest_contracts.py` (requires ELSER pipeline; see docs/ELASTIC_CLOUD_SETUP.md)
  - For "compliance breaches" / "audit access logs" answers: add the log_auditor ES|QL tool to your agent in Kibana (elastic/agent-config.md §4)

Example queries and which index they use:
  - "What is our policy on minors?" → legal-knowledge-base (run ingest_contracts)
  - "Can I use customer-leads-prod for marketing?" → customer_leads_prod + legal-knowledge-base
  - "Filter out risky records" → agent uses customer_leads_prod
  - "Have there been any compliance breaches in the last 7 days?" → data_access_logs_prod + log_auditor tool
  - "Audit data access logs for high-volume downloads by region" → data_access_logs_prod + log_auditor tool
"""
import os
import sys

# Project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

def main():
    print("Governance Guardian – setting up all test data for example queries.\n")

    # 1. Customers
    csv_customers = os.path.join(PROJECT_ROOT, "data", "customers.csv")
    if not os.path.exists(csv_customers) or os.path.getsize(csv_customers) < 100:
        print("1. Generating customer data...")
        from scripts.generate_customers import generate_customer_csv
        generate_customer_csv(csv_customers)
        print("   Generated:", csv_customers)
    else:
        print("1. Customer CSV already present:", csv_customers)

    print("2. Ingesting customers into customer_leads_prod...")
    from scripts.ingest_customers import ingest_customers
    ingest_customers()

    # 2. Access logs
    print("3. Generating access logs...")
    from scripts.generate_access_logs import generate_access_logs_csv
    access_logs_csv = os.path.join(PROJECT_ROOT, "data", "access_logs.csv")
    generate_access_logs_csv(access_logs_csv)
    print("   Generated:", access_logs_csv)

    print("4. Ingesting access logs into data_access_logs_prod...")
    from scripts.ingest_access_logs import main as ingest_access_logs_main
    ingest_access_logs_main()

    print("\nDone. Data status:")
    print("  - customer_leads_prod: populated (for marketing / filter queries)")
    print("  - data_access_logs_prod: populated (for breach / audit queries)")
    print("\nNext steps so all 5 example queries work:")
    print("  1. Policy query: ensure legal-knowledge-base has data:")
    print("       python scripts/ingest_contracts.py")
    print("  2. Breach/audit queries: add the log_auditor ES|QL tool to your agent in Kibana:")
    print("       See elastic/agent-config.md §4 (log_auditor)")
    print("  3. Restart or refresh the Streamlit app and try the sidebar example queries.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

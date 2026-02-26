#!/usr/bin/env python3
"""
Ingest synthetic access logs into Elasticsearch index data_access_logs_prod.

Run after: python scripts/generate_access_logs.py
"""
import os
import json
import csv
from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv

load_dotenv()
load_dotenv(".env.local")

INDEX_NAME = "data_access_logs_prod"

def get_es_client():
    api_key = os.getenv("ELASTIC_API_KEY")
    es_url = (os.getenv("ELASTICSEARCH_URL") or "").strip().rstrip("/")
    cloud_id = (os.getenv("ELASTIC_CLOUD_ID") or "").strip()
    if es_url:
        return Elasticsearch(es_url, api_key=api_key)
    if cloud_id:
        return Elasticsearch(cloud_id=cloud_id, api_key=api_key)
    raise ValueError("Set ELASTICSEARCH_URL or ELASTIC_CLOUD_ID in .env")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mapping_path = os.path.join(base_dir, "elastic", "access-logs-mapping.json")
    csv_path = os.path.join(base_dir, "data", "access_logs.csv")

    if not os.path.exists(csv_path):
        print(f"Run first: python scripts/generate_access_logs.py")
        return

    es = get_es_client()
    with open(mapping_path) as f:
        mapping = json.load(f)

    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
    es.indices.create(index=INDEX_NAME, body=mapping)
    print(f"Index '{INDEX_NAME}' created.")

    actions = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc = {
                "timestamp": row["timestamp"],
                "user": row["user"],
                "ip_address": row["ip_address"],
                "region": row["region"],
                "records_downloaded": int(row["records_downloaded"]),
                "dataset_name": row["dataset_name"],
            }
            actions.append({"_index": INDEX_NAME, "_source": doc})
            if len(actions) >= 500:
                helpers.bulk(es, actions)
                actions = []
    if actions:
        helpers.bulk(es, actions)
    es.indices.refresh(index=INDEX_NAME)
    print(f"Ingested {es.count(index=INDEX_NAME)['count']} documents into '{INDEX_NAME}'.")

if __name__ == "__main__":
    main()

import os
import json
import csv
from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_es_client():
    cloud_id = os.getenv("ELASTIC_CLOUD_ID")
    api_key = os.getenv("ELASTIC_API_KEY")
    es_url = os.getenv("ELASTICSEARCH_URL")

    if cloud_id:
        return Elasticsearch(cloud_id=cloud_id, api_key=api_key)
    return Elasticsearch(es_url, api_key=api_key)

def transform_row(row):
    """
    Transforms a single CSV row into the Elasticsearch document format.
    """
    return {
        "Name": row.get("Name"),
        "Email": row.get("Email"),
        "Age": int(row.get("Age", 0)) if row.get("Age") else 0,
        "Country": row.get("Country"),
        "Subscription_Type": row.get("Subscription_Type")
    }

def setup_index(es):
    index_name = "customer-leads-prod"
    mapping_path = "elastic/customer-leads-mapping.json"

    with open(mapping_path, "r") as f:
        mapping_body = json.load(f)

    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        print(f"Existing index '{index_name}' deleted.")

    es.indices.create(index=index_name, body=mapping_body)
    print(f"Index '{index_name}' created with correct mapping.")
    return index_name

def ingest_customers():
    es = get_es_client()
    index_name = setup_index(es)

    csv_path = "data/customers.csv"
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return

    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        actions = []
        for row in reader:
            doc = transform_row(row)
            action = {
                "_index": index_name,
                "_source": doc
            }
            actions.append(action)

            # Batch processing if needed for very large files
            if len(actions) >= 500:
                helpers.bulk(es, actions)
                actions = []

        if actions:
            helpers.bulk(es, actions)

    es.indices.refresh(index=index_name)
    print(f"Successfully ingested and refreshed index '{index_name}'.")

if __name__ == "__main__":
    ingest_customers()

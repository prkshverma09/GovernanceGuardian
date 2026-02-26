#!/usr/bin/env python3
"""
Remediation API: executes a safe ES|QL query and reindexes results into a new index.

Used by the "Action-Taker" feature: when the agent suggests filtering risky records,
a Webhook Tool in Elastic Agent Builder can call this API to create a sanitized dataset.

Usage:
  - As HTTP server (for Webhook Tool): python scripts/remediation_api.py
  - As library: from scripts.remediation_api import run_remediation, get_es_client
"""
import os
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
load_dotenv(".env.local")

# Default safe ES|QL: exclude minors and GDPR-restricted regions
DEFAULT_SAFE_QUERY = (
    'FROM customer_leads_prod '
    '| WHERE Age >= 18 AND (Country IS NULL OR Country != "GDPR_Restricted_Zone") '
    '| KEEP Name, Email, Age, Country, Subscription_Type'
)
SOURCE_INDEX = "customer_leads_prod"
TARGET_INDEX = "customer_leads_safe"


def get_es_client():
    from elasticsearch import Elasticsearch
    api_key = os.getenv("ELASTIC_API_KEY")
    es_url = (os.getenv("ELASTICSEARCH_URL") or "").strip().rstrip("/")
    cloud_id = (os.getenv("ELASTIC_CLOUD_ID") or "").strip()
    if es_url:
        return Elasticsearch(es_url, api_key=api_key)
    if cloud_id:
        return Elasticsearch(cloud_id=cloud_id, api_key=api_key)
    raise ValueError("Set ELASTICSEARCH_URL or ELASTIC_CLOUD_ID in .env")


def load_customer_mapping():
    project_root = Path(__file__).resolve().parents[1]
    path = project_root / "elastic" / "customer-leads-mapping.json"
    with open(path) as f:
        return json.load(f)


def run_remediation(es, source_index=None, target_index=None, esql_query=None):
    """
    Execute an ES|QL query that returns safe rows, then bulk index into target_index.

    Args:
        es: Elasticsearch client
        source_index: unused (query defines source); kept for API clarity
        target_index: index name to write sanitized documents into
        esql_query: full ES|QL query string; if None, uses DEFAULT_SAFE_QUERY

    Returns:
        dict: {"index": target_index, "count": N, "error": None or str}
    """
    source_index = source_index or SOURCE_INDEX
    target_index = target_index or TARGET_INDEX
    esql_query = esql_query or DEFAULT_SAFE_QUERY

    try:
        resp = es.esql.query(query=esql_query)
    except Exception as e:
        return {"index": target_index, "count": 0, "error": str(e)}

    columns = resp.get("columns", [])
    values = resp.get("values", [])
    if not columns or not values:
        return {"index": target_index, "count": 0, "error": "No results from ES|QL query"}

    col_names = [c["name"] for c in columns]
    mapping = load_customer_mapping()
    if es.indices.exists(index=target_index):
        es.indices.delete(index=target_index)
    es.indices.create(index=target_index, body=mapping)

    from elasticsearch import helpers
    actions = []
    for row in values:
        doc = dict(zip(col_names, row))
        actions.append({"_index": target_index, "_source": doc})
        if len(actions) >= 500:
            helpers.bulk(es, actions)
            actions = []
    if actions:
        helpers.bulk(es, actions)
    es.indices.refresh(index=target_index)
    count = len(resp["values"])
    return {"index": target_index, "count": count, "error": None}


def main():
    # Run as CLI for one-off remediation
    es = get_es_client()
    out = run_remediation(es)
    print(json.dumps(out, indent=2))


def create_app():
    """Create Flask app for Webhook Tool (POST /remediate)."""
    from flask import Flask, request, jsonify
    app = Flask(__name__)

    @app.route("/remediate", methods=["POST"])
    def remediate():
        body = request.get_json() or {}
        esql_query = body.get("query")
        target_index = body.get("target_index", TARGET_INDEX)
        es = get_es_client()
        result = run_remediation(
            es, target_index=target_index, esql_query=esql_query
        )
        return jsonify(result)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    @app.route("/sample", methods=["GET"])
    def sample():
        """Return up to 20 docs from customer_leads_safe for demo preview."""
        limit = min(20, int(request.args.get("limit", 20)))
        es = get_es_client()
        if not es.indices.exists(index=TARGET_INDEX):
            return jsonify({"rows": [], "index": TARGET_INDEX})
        try:
            r = es.search(index=TARGET_INDEX, size=limit, body={"query": {"match_all": {}}})
            rows = [hit["_source"] for hit in r.get("hits", {}).get("hits", [])]
            return jsonify({"rows": rows, "index": TARGET_INDEX})
        except Exception as e:
            return jsonify({"rows": [], "index": TARGET_INDEX, "error": str(e)}), 500

    return app


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        app = create_app()
        port = int(os.getenv("REMEDIATION_API_PORT", "5050"))
        app.run(host="0.0.0.0", port=port)
    else:
        main()

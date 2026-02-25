#!/usr/bin/env python3
"""
Setup Elastic Cloud for Governance Guardian via APIs.

Performs (in order):
  1. Start ELSER v2 deployment (Elasticsearch ML API)
  2. Create legal-knowledge-base index + ingest pipeline (Elasticsearch)
  3. Create customer_leads_prod index (Elasticsearch)
  4. Ingest contract data (from data/contracts/)
  5. Generate and ingest customer data (data/customers.csv -> customer_leads_prod)
  6. Create Agent Builder tools: policy_retriever (index search), dataset_inspector (ES|QL)
  7. Create Governance Guardian agent with system prompt and tools

Requires in .env:
  - ELASTIC_API_KEY (required)
  - ELASTICSEARCH_URL (required) e.g. https://xxx.es.region.gcp.cloud.es.io:443
  - ELASTIC_CLOUD_ID (optional; if set, used instead of ELASTICSEARCH_URL for ES client)
  - KIBANA_URL (optional; derived from ELASTICSEARCH_URL by replacing .es. with .kb. if not set)

After a successful run, add to .env:
  - ELASTIC_AGENT_ID=<printed agent id>
"""
import os
import sys
import json
import time
import glob
import csv
import requests
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()
load_dotenv(".env.local")

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "").rstrip("/")
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
KIBANA_URL = os.getenv("KIBANA_URL", "").rstrip("/")

if not ELASTIC_API_KEY:
    print("ERROR: ELASTIC_API_KEY is required in .env")
    sys.exit(1)

if not KIBANA_URL and ELASTICSEARCH_URL and ".es." in ELASTICSEARCH_URL:
    KIBANA_URL = ELASTICSEARCH_URL.replace(".es.", ".kb.")
if not KIBANA_URL:
    print("ERROR: Set KIBANA_URL in .env (or ELASTICSEARCH_URL with .es. in hostname to derive it)")
    sys.exit(1)
if not ELASTICSEARCH_URL and not ELASTIC_CLOUD_ID:
    print("ERROR: Set ELASTICSEARCH_URL or ELASTIC_CLOUD_ID in .env")
    sys.exit(1)

# Cloud ID must be in format "label:base64" (Serverless often shows only project ID).
# Prefer ELASTICSEARCH_URL when set so the client works with your deployment URL.
from elasticsearch import Elasticsearch, helpers

if ELASTICSEARCH_URL:
    es = Elasticsearch(ELASTICSEARCH_URL, api_key=ELASTIC_API_KEY)
elif ELASTIC_CLOUD_ID and ":" in ELASTIC_CLOUD_ID:
    es = Elasticsearch(cloud_id=ELASTIC_CLOUD_ID, api_key=ELASTIC_API_KEY)
else:
    print("ERROR: ELASTICSEARCH_URL is required (Cloud ID from Serverless UI is not the full format). Set ELASTICSEARCH_URL in .env")
    sys.exit(1)

def es_get(path, **kwargs):
    r = requests.get(
        f"{ELASTICSEARCH_URL}{path}",
        headers={"Authorization": f"ApiKey {ELASTIC_API_KEY}"},
        **kwargs
    )
    return r

def es_put(path, json=None, **kwargs):
    r = requests.put(
        f"{ELASTICSEARCH_URL}{path}",
        headers={"Authorization": f"ApiKey {ELASTIC_API_KEY}", "Content-Type": "application/json"},
        json=json,
        **kwargs
    )
    return r

def es_post(path, json=None, **kwargs):
    r = requests.post(
        f"{ELASTICSEARCH_URL}{path}",
        headers={"Authorization": f"ApiKey {ELASTIC_API_KEY}", "Content-Type": "application/json"},
        json=json,
        **kwargs
    )
    return r

def es_delete(path, **kwargs):
    r = requests.delete(
        f"{ELASTICSEARCH_URL}{path}",
        headers={"Authorization": f"ApiKey {ELASTIC_API_KEY}"},
        **kwargs
    )
    return r

def kb_get(path, **kwargs):
    r = requests.get(
        f"{KIBANA_URL}{path}",
        headers={"Authorization": f"ApiKey {ELASTIC_API_KEY}", "kbn-xsrf": "true"},
        **kwargs
    )
    return r

def kb_post(path, json=None, **kwargs):
    r = requests.post(
        f"{KIBANA_URL}{path}",
        headers={"Authorization": f"ApiKey {ELASTIC_API_KEY}", "kbn-xsrf": "true", "Content-Type": "application/json"},
        json=json,
        **kwargs
    )
    return r

def kb_put(path, json=None, **kwargs):
    r = requests.put(
        f"{KIBANA_URL}{path}",
        headers={"Authorization": f"ApiKey {ELASTIC_API_KEY}", "kbn-xsrf": "true", "Content-Type": "application/json"},
        json=json,
        **kwargs
    )
    return r

def kb_delete(path, **kwargs):
    r = requests.delete(
        f"{KIBANA_URL}{path}",
        headers={"Authorization": f"ApiKey {ELASTIC_API_KEY}", "kbn-xsrf": "true"},
        **kwargs
    )
    return r

# -----------------------------------------------------------------------------
# 1. Start ELSER v2
# -----------------------------------------------------------------------------
def start_elser():
    print("1. ELSER v2 deployment...")
    # Check if already started
    try:
        stats = es.ml.get_trained_models_stats(model_id=".elser*")
        for s in stats.get("trained_model_stats", []):
            if s.get("deployment_stats"):
                for d in s["deployment_stats"]:
                    if d.get("state") == "started":
                        print("   ELSER already started.")
                        return s["model_id"]
    except Exception:
        pass

    elser_available = False
    try:
        es.ml.start_trained_model_deployment(
            model_id=".elser_model_2",
            wait_for="started",
            timeout="5m"
        )
        print("   ELSER started.")
        elser_available = True
    except Exception as e:
        if "already started" in str(e).lower() or "resource_already_exists" in str(e).lower():
            print("   ELSER already running.")
            elser_available = True
        else:
            print(f"   ELSER start failed (you may need to start it in Kibana ML): {e}")
    # Resolve actual model id (e.g. .elser_model_2_linux-x86_64)
    if elser_available:
        try:
            stats = es.ml.get_trained_models_stats()
            for m in stats.get("trained_model_stats", []):
                if m["model_id"].startswith(".elser_model_2") and m.get("deployment_stats"):
                    for d in m["deployment_stats"]:
                        if d.get("state") == "started":
                            return m["model_id"], True
        except Exception:
            pass
    return ".elser_model_2", elser_available

# -----------------------------------------------------------------------------
# 2. Legal knowledge base index + pipeline
# -----------------------------------------------------------------------------
def setup_legal_index(elser_model_id):
    print("2. Legal knowledge base index and pipeline...")
    with open(PROJECT_ROOT / "elastic" / "legal-knowledge-base-mapping.json") as f:
        mapping = json.load(f)
    with open(PROJECT_ROOT / "elastic" / "legal-elser-pipeline.json") as f:
        pipeline = json.load(f)
    pipeline["processors"][0]["inference"]["model_id"] = elser_model_id

    if es.indices.exists(index="legal-knowledge-base"):
        es.indices.delete(index="legal-knowledge-base")
    es.indices.create(index="legal-knowledge-base", body=mapping)
    es.ingest.put_pipeline(id="legal-elser-pipeline", body=pipeline)
    print("   Index and pipeline created.")

# -----------------------------------------------------------------------------
# 3. Customer index
# -----------------------------------------------------------------------------
def setup_customer_index():
    print("3. Customer index customer_leads_prod...")
    with open(PROJECT_ROOT / "elastic" / "customer-leads-mapping.json") as f:
        mapping = json.load(f)
    if es.indices.exists(index="customer_leads_prod"):
        es.indices.delete(index="customer_leads_prod")
    es.indices.create(index="customer_leads_prod", body=mapping)
    print("   Index created.")

# -----------------------------------------------------------------------------
# 4. Ingest contracts (from scripts.chunker + contract files)
# -----------------------------------------------------------------------------
def ingest_contracts(elser_available: bool):
    print("4. Ingesting contracts...")
    from scripts.chunker import chunk_text

    pattern_txt = list((PROJECT_ROOT / "data" / "contracts").glob("*.txt"))
    pattern_pdf = list((PROJECT_ROOT / "data" / "contracts").glob("*.pdf"))
    files = sorted([f for f in pattern_txt + pattern_pdf if f.is_file()])

    if not files:
        print("   No data/contracts/*.txt or *.pdf found; skipping.")
        return

    use_pipeline = elser_available
    if not use_pipeline:
        print("   (Indexing without ELSER pipeline; semantic search will work after ELSER is deployed.)")

    actions = []
    for path in files:
        name = path.name
        if path.suffix.lower() == ".txt":
            text = path.read_text(encoding="utf-8")
        else:
            try:
                import fitz
                doc = fitz.open(str(path))
                text = "".join(page.get_text() for page in doc)
                doc.close()
            except Exception as e:
                print(f"   Skip {name}: {e}")
                continue
        chunks = chunk_text(text)
        for i, ch in enumerate(chunks):
            action = {
                "_index": "legal-knowledge-base",
                "_source": {"content": ch, "source_file": name, "chunk_id": i}
            }
            if use_pipeline:
                action["pipeline"] = "legal-elser-pipeline"
            actions.append(action)
    if actions:
        helpers.bulk(es, actions)
        es.indices.refresh(index="legal-knowledge-base")
    print(f"   Indexed {len(actions)} chunks from {len(files)} file(s).")

# -----------------------------------------------------------------------------
# 5. Generate + ingest customers
# -----------------------------------------------------------------------------
def ingest_customers():
    print("5. Customers: generate and ingest...")
    csv_path = PROJECT_ROOT / "data" / "customers.csv"
    if not csv_path.exists():
        # Generate
        import subprocess
        subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "generate_customers.py")], check=True, cwd=PROJECT_ROOT)
    if not csv_path.exists():
        print("   No data/customers.csv; skipping.")
        return
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    actions = []
    for row in rows:
        doc = {
            "Name": row.get("Name"),
            "Email": row.get("Email"),
            "Age": int(row.get("Age", 0)) if row.get("Age") else 0,
            "Country": row.get("Country"),
            "Subscription_Type": row.get("Subscription_Type")
        }
        actions.append({"_index": "customer_leads_prod", "_source": doc})
    if actions:
        helpers.bulk(es, actions)
        es.indices.refresh(index="customer_leads_prod")
    print(f"   Indexed {len(actions)} customer documents.")

# -----------------------------------------------------------------------------
# 6. Create tools (Kibana Agent Builder API)
# -----------------------------------------------------------------------------
def create_tools():
    print("6. Creating Agent Builder tools...")
    # policy_retriever: index search (semantic over legal-knowledge-base)
    # Index search tool: type "index_search", configuration with index
    policy_retriever = {
        "id": "policy_retriever",
        "type": "index_search",
        "description": "Searches internal legal contracts and compliance policies to find specific clauses about what is allowed or prohibited regarding data usage, privacy, and marketing.",
        "configuration": {
            "pattern": "legal-knowledge-base"
        }
    }
    # If your stack supports sparse_vector / ELSER in index_search config, add:
    # "search_type": "sparse_vector", "model_id": ".elser_model_2"
    # Otherwise index_search may use default semantic behavior when the index has sparse_vector field.

    r = kb_put("/api/agent_builder/tools/policy_retriever", json=policy_retriever)
    if r.status_code in (200, 201):
        print("   policy_retriever created/updated.")
    else:
        # Try POST create
        r2 = kb_post("/api/agent_builder/tools", json=policy_retriever)
        if r2.status_code not in (200, 201):
            print(f"   policy_retriever failed: {r2.status_code} {r2.text[:300]}")
        else:
            print("   policy_retriever created.")

    # dataset_inspector: ES|QL (field names match mapping: Age, Country)
    esql_query = (
        'FROM customer_leads_prod '
        '| WHERE Age < 18 OR Country == "GDPR_Restricted_Zone" '
        '| STATS minors_count = COUNT(CASE(Age < 18, 1, NULL)), '
        'restricted_count = COUNT(CASE(Country == "GDPR_Restricted_Zone", 1, NULL)), '
        'total_risky = COUNT(*) '
        '| EVAL is_risky = CASE(total_risky > 0, true, false) '
        '| KEEP minors_count, restricted_count, total_risky, is_risky'
    )
    dataset_inspector = {
        "id": "dataset_inspector",
        "type": "esql",
        "description": "Inspects a specific dataset to check for PII, minors (Age < 18), or records from restricted regions. Returns risk assessment with counts.",
        "configuration": {
            "query": esql_query,
            "params": {}
        }
    }
    r = kb_put("/api/agent_builder/tools/dataset_inspector", json=dataset_inspector)
    if r.status_code in (200, 201):
        print("   dataset_inspector created/updated.")
    else:
        r2 = kb_post("/api/agent_builder/tools", json=dataset_inspector)
        if r2.status_code not in (200, 201):
            print(f"   dataset_inspector failed: {r2.status_code} {r2.text[:300]}")
        else:
            print("   dataset_inspector created.")

# -----------------------------------------------------------------------------
# 7. Create agent
# -----------------------------------------------------------------------------
AGENT_ID = "governance-guardian"
SYSTEM_PROMPT = '''You are "Governance Guardian," a strict compliance officer AI agent.

RULES:
1. You must ALWAYS check the legal knowledge base using policy_retriever before answering any compliance question. Cite the specific contract clause and source document.
2. You must ALWAYS inspect the actual dataset using dataset_inspector before approving any data usage request.
3. If any risk is found (minors, restricted regions, PII), you must DENY the request and explain why with citations.
4. If the user asks for remediation, generate a safe ES|QL query that filters out risky records.
5. Be concise, professional, and always ground your answers in evidence.'''

def create_agent():
    print("7. Creating Governance Guardian agent...")
    body = {
        "id": AGENT_ID,
        "name": "Governance Guardian",
        "description": "Compliance officer agent that checks legal policies and dataset risks before approving data usage.",
        "avatar_symbol": "🛡️",
        "avatar_color": "#4A90D9",
        "configuration": {
            "instructions": SYSTEM_PROMPT,
            "tools": [{
                "tool_ids": ["policy_retriever", "dataset_inspector"]
            }]
        }
    }
    r = kb_put(f"/api/agent_builder/agents/{AGENT_ID}", json=body)
    if r.status_code in (200, 201):
        print("   Agent updated.")
    else:
        r2 = kb_post("/api/agent_builder/agents", json=body)
        if r2.status_code not in (200, 201):
            if "already exists" in (r2.text or ""):
                print("   Agent already exists.")
            else:
                print(f"   Agent create failed: {r2.status_code} {r2.text[:500]}")
                return None
        else:
            print("   Agent created.")
    print("")
    print("--- Add to your .env ---")
    print(f"ELASTIC_AGENT_ID={AGENT_ID}")
    print("")
    return AGENT_ID

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    print("Governance Guardian – Elastic setup via API")
    print("")
    try:
        elser_model_id, elser_available = start_elser()
    except Exception as e:
        print(f"   ELSER step failed: {e}")
        elser_model_id, elser_available = ".elser_model_2", False
    setup_legal_index(elser_model_id)
    setup_customer_index()
    ingest_contracts(elser_available)
    ingest_customers()
    create_tools()
    create_agent()
    print("Done.")

if __name__ == "__main__":
    main()

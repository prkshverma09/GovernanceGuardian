import os
import json
import glob
import fitz  # PyMuPDF
from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv
from scripts.chunker import chunk_text

# Load environment variables
load_dotenv()

def get_es_client():
    cloud_id = os.getenv("ELASTIC_CLOUD_ID")
    api_key = os.getenv("ELASTIC_API_KEY")
    es_url = os.getenv("ELASTICSEARCH_URL")

    if cloud_id:
        return Elasticsearch(cloud_id=cloud_id, api_key=api_key)
    return Elasticsearch(es_url, api_key=api_key)

def setup_elasticsearch(es):
    # 1. Discover actual ELSER model ID
    stats = es.ml.get_trained_models_stats()
    model_id = [m["model_id"] for m in stats["trained_model_stats"] if m["model_id"].startswith(".elser_model_2")][0]
    print(f"Using ELSER model: {model_id}")

    # 2. Create Ingest Pipeline
    pipeline_path = "elastic/legal-elser-pipeline.json"
    with open(pipeline_path, "r") as f:
        pipeline_body = json.load(f)

    # Update model_id in pipeline if it differs from default
    pipeline_body["processors"][0]["inference"]["model_id"] = model_id

    es.ingest.put_pipeline(id="legal-elser-pipeline", body=pipeline_body)
    print("Ingest pipeline 'legal-elser-pipeline' created/updated.")

    # 3. Create Index Mapping
    mapping_path = "elastic/legal-knowledge-base-mapping.json"
    with open(mapping_path, "r") as f:
        mapping_body = json.load(f)

    index_name = "legal-knowledge-base"
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        print(f"Existing index '{index_name}' deleted.")

    es.indices.create(index=index_name, body=mapping_body)
    print(f"Index '{index_name}' created with correct mapping.")
    return index_name

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def ingest_contracts():
    es = get_es_client()
    index_name = setup_elasticsearch(es)

    contracts_pattern = "data/contracts/*.pdf"
    contract_files = glob.glob(contracts_pattern)

    actions = []
    for pdf_path in contract_files:
        filename = os.path.basename(pdf_path)
        print(f"Processing {filename}...")

        full_text = extract_text_from_pdf(pdf_path)
        chunks = chunk_text(full_text)

        for i, chunk in enumerate(chunks):
            action = {
                "_index": index_name,
                "pipeline": "legal-elser-pipeline",
                "_source": {
                    "content": chunk,
                    "source_file": filename,
                    "chunk_id": i
                }
            }
            actions.append(action)

    if actions:
        helpers.bulk(es, actions)
        es.indices.refresh(index=index_name)
        print(f"Successfully indexed {len(actions)} chunks from {len(contract_files)} contracts and refreshed index.")
    else:
        print("No contracts found to ingest.")

if __name__ == "__main__":
    ingest_contracts()

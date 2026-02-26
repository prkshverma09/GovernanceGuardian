import os
import pytest
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

# Load environment variables from .env and .env.local if they exist
load_dotenv()
load_dotenv(".env.local")

@pytest.fixture(scope="session")
def es_client():
    """
    Fixture to provide a configured Elasticsearch client.
    Requires ELASTIC_API_KEY and ELASTICSEARCH_URL (or ELASTIC_CLOUD_ID) in .env
    """
    cloud_id = os.getenv("ELASTIC_CLOUD_ID")
    api_key = os.getenv("ELASTIC_API_KEY")
    es_url = os.getenv("ELASTICSEARCH_URL")

    if not api_key:
        pytest.fail("ELASTIC_API_KEY not found in environment variables.")

    # Prefer ELASTICSEARCH_URL (works with deployment URLs); Cloud ID must be full format if used
    if es_url and es_url.strip():
        client = Elasticsearch(es_url.strip().rstrip("/"), api_key=api_key)
    elif cloud_id and cloud_id.strip():
        client = Elasticsearch(cloud_id=cloud_id.strip(), api_key=api_key)
    else:
        pytest.fail("Neither ELASTIC_CLOUD_ID nor ELASTICSEARCH_URL found in environment variables.")

    yield client
    client.close()

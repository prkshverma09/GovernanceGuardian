import os
import pytest
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

# Load environment variables from .env if it exists
load_dotenv()

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

    if cloud_id:
        client = Elasticsearch(cloud_id=cloud_id, api_key=api_key)
    elif es_url:
        client = Elasticsearch(es_url, api_key=api_key)
    else:
        pytest.fail("Neither ELASTIC_CLOUD_ID nor ELASTICSEARCH_URL found in environment variables.")

    yield client
    client.close()

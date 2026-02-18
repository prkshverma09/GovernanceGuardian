import pytest
import time

@pytest.mark.integration
def test_pipeline_exists(es_client):
    """Verify the legal-elser-pipeline is registered in ES."""
    pipeline_id = "legal-elser-pipeline"
    try:
        pipeline = es_client.ingest.get_pipeline(id=pipeline_id)
        assert pipeline_id in pipeline
    except Exception as e:
        pytest.fail(f"Pipeline {pipeline_id} not found: {str(e)}")

@pytest.mark.integration
def test_index_mapping_correct(es_client):
    """Verify the index mapping has the expected fields and types."""
    index_name = "legal-knowledge-base"
    try:
        mapping = es_client.indices.get_mapping(index=index_name)
        properties = mapping[index_name]["mappings"]["properties"]

        assert properties["content"]["type"] == "text"
        assert properties["content_embedding"]["type"] == "sparse_vector"
        assert properties["source_file"]["type"] == "keyword"
        assert properties["chunk_id"]["type"] == "integer"
    except Exception as e:
        pytest.fail(f"Index mapping check failed for {index_name}: {str(e)}")

@pytest.mark.integration
def test_documents_indexed(es_client):
    """Verify that documents are actually present in the index."""
    index_name = "legal-knowledge-base"
    # Wait a bit for indexing if needed
    time.sleep(2)
    count = es_client.count(index=index_name)["count"]
    assert count > 0

@pytest.mark.integration
def test_semantic_search_returns_results(es_client):
    """Verify that ELSER-powered semantic search works."""
    index_name = "legal-knowledge-base"
    query = "data privacy regulations"

    # Using text_expansion for ELSER
    # The model ID used in our infra test was .elser_model_2 (or similar)
    # We should discover the actual model ID from the cluster
    stats = es_client.ml.get_trained_models_stats()
    model_id = [m["model_id"] for m in stats["trained_model_stats"] if m["model_id"].startswith(".elser_model_2")][0]

    search_query = {
        "text_expansion": {
            "content_embedding": {
                "model_id": model_id,
                "model_text": query
            }
        }
    }

    response = es_client.search(index=index_name, query=search_query)
    assert response["hits"]["total"]["value"] > 0
    assert "source_file" in response["hits"]["hits"][0]["_source"]

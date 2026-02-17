import pytest

@pytest.mark.integration
def test_elasticsearch_connection(es_client):
    """
    Verify successful connection to the Elastic cluster.
    """
    info = es_client.info()
    assert "cluster_name" in info
    assert "tagline" in info
    assert info["tagline"] == "You Know, for Search"

@pytest.mark.integration
def test_elser_model_deployed(es_client):
    """
    Verify ELSER v2 model is deployed and started.
    """
    # Base model ID for ELSER v2. Serverless often adds suffixes like _linux-x86_64.
    model_id_prefix = ".elser_model_2"

    try:
        # Get all trained models stats
        stats = es_client.ml.get_trained_models_stats()

        # Find a model that matches the prefix
        matching_models = [
            m for m in stats.get("trained_model_stats", [])
            if m["model_id"].startswith(model_id_prefix)
        ]

        assert len(matching_models) > 0, f"No model starting with '{model_id_prefix}' found."

        model_stats = matching_models[0]
        assert model_stats["deployment_stats"]["state"] == "started", f"Model {model_stats['model_id']} state is {model_stats['deployment_stats']['state']}, expected 'started'."

    except Exception as e:
        pytest.fail(f"ELSER v2 model check failed: {str(e)}")

import pytest

@pytest.mark.integration
def test_customer_index_exists(es_client):
    """Verify that the customer_leads_prod index exists."""
    assert es_client.indices.exists(index="customer_leads_prod")

@pytest.mark.integration
def test_customer_mapping_correct(es_client):
    """Verify the mapping for customer_leads_prod."""
    index_name = "customer_leads_prod"
    mapping = es_client.indices.get_mapping(index=index_name)
    properties = mapping[index_name]["mappings"]["properties"]

    assert properties["Age"]["type"] == "integer"
    assert properties["Country"]["type"] == "keyword"
    assert properties["Email"]["type"] == "keyword"
    assert properties["Subscription_Type"]["type"] == "keyword"

@pytest.mark.integration
def test_customer_count(es_client):
    """Verify that we indexed the target number of records."""
    count = es_client.count(index="customer_leads_prod")["count"]
    # Our faker script generates 1000 by default
    assert count == 1000

@pytest.mark.integration
def test_esql_minors_query(es_client):
    """Verify that ES|QL correctly identifies minors."""
    # Index name with hyphens needs double quotes in some ES|QL versions or backticks
    query = 'FROM customer_leads_prod | WHERE Age < 18 | STATS count = COUNT(*) | KEEP count'
    res = es_client.esql.query(query=query)
    count = res["values"][0][0]
    assert count > 0

@pytest.mark.integration
def test_esql_restricted_zone_query(es_client):
    """Verify that ES|QL correctly identifies restricted zones."""
    query = 'FROM customer_leads_prod | WHERE Country == "GDPR_Restricted_Zone" | STATS count = COUNT(*) | KEEP count'
    res = es_client.esql.query(query=query)
    count = res["values"][0][0]
    assert count > 0

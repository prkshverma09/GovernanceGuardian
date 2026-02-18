import os
import pytest
from scripts.agent_client import AgentClient, parse_agent_response

@pytest.mark.integration
def test_agent_client_initialization():
    """Verify client initializes with env vars."""
    client = AgentClient(agent_id="test-agent")
    assert client.kb_url is not None
    assert client.api_key is not None
    assert client.agent_id == "test-agent"

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("ELASTIC_AGENT_ID"), reason="ELASTIC_AGENT_ID not set in .env")
def test_policy_retriever_integration():
    """Tests the policy_retriever tool via the Agent API."""
    client = AgentClient()
    response = client.chat("What is our privacy policy?")

    content, tool_calls, citations = parse_agent_response(response)

    assert content is not None
    # Use actual platform tool IDs
    assert any(tc['function']['name'] == 'platform.core.search' for tc in tool_calls)

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("ELASTIC_AGENT_ID"), reason="ELASTIC_AGENT_ID not set in .env")
def test_dataset_inspector_integration():
    """Tests the dataset_inspector tool via the Agent API."""
    client = AgentClient()
    response = client.chat("Check customer-leads-prod for risk.")

    content, tool_calls, citations = parse_agent_response(response)

    assert content is not None
    # It might use get_index_mapping or execute_esql
    tool_names = [tc['function']['name'] for tc in tool_calls]
    assert any(name in tool_names for name in ['platform.core.execute_esql', 'platform.core.get_index_mapping', 'platform.core.generate_esql'])

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("ELASTIC_AGENT_ID"), reason="ELASTIC_AGENT_ID not set in .env")
def test_agent_combined_flow():
    """Tests a query that requires both tools."""
    client = AgentClient()
    # Use a query that clearly asks for policy and data check
    response = client.chat("Can I email the customer list based on our NDA policy?")

    content, tool_calls, citations = parse_agent_response(response)

    assert content is not None
    tool_names = [tc['function']['name'] for tc in tool_calls]
    assert 'platform.core.search' in tool_names

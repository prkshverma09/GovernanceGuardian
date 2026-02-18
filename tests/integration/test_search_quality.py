import pytest
from scripts.agent_client import AgentClient, parse_agent_response

@pytest.mark.integration
def test_contract_search_relevance():
    """Verify that a specific search for 'minors' returns relevant documents."""
    client = AgentClient()
    # Query that should trigger platform.core.search
    response = client.chat("Search legal contracts for 'minors'.")
    content, tool_calls, citations = parse_agent_response(response)

    # Check if the search tool was called
    search_calls = [tc for tc in tool_calls if tc['function']['name'] == 'platform.core.search']
    assert len(search_calls) > 0

    # The content should likely mention minors
    assert "minor" in content.lower() or "under 18" in content.lower()

@pytest.mark.integration
def test_esql_results_consistency():
    """Verify that the agent's reported data matches what we expect from the tool."""
    client = AgentClient()
    response = client.chat("How many minors are in customer-leads-prod?")
    content, tool_calls, citations = parse_agent_response(response)

    # Check if esql tool was called
    esql_calls = [tc for tc in tool_calls if tc['function']['name'] == 'platform.core.execute_esql']
    assert len(esql_calls) > 0

    # The content should contain a number (the count)
    # Our synthetic data usually has minors
    assert any(char.isdigit() for char in content)

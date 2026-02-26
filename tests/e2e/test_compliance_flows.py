import pytest
import os
import time
from scripts.agent_client import AgentClient, parse_agent_response

@pytest.mark.e2e
def test_e2e_compliance_flow_denied():
    """Full journey: Ask to use data -> Agent checks policy -> Agent checks data -> Denied."""
    client = AgentClient()
    # We use a query that should trigger the full "strict compliance officer" logic
    # "Can I email the customer list? Check the policy first."
    response = client.chat("I want to email the 'customer_leads_prod' list. Is that safe based on our NDA policy?")

    content, tool_calls, citations = parse_agent_response(response)

    # 1. It should have searched for policy (custom or platform tool name)
    tool_names = [tc['function']['name'] for tc in tool_calls]
    assert any(t in tool_names for t in ['policy_retriever', 'platform.core.search']), f"Expected policy tool, got {tool_names}"

    # 2. It should have inspected the data (custom or platform tool name)
    assert any(t in tool_names for t in ['dataset_inspector', 'platform.core.execute_esql']), f"Expected ES|QL tool, got {tool_names}"

    # 3. Decision: Since synthetic data has minors and NDA prohibits it, it should DENY
    assert any(word in content.upper() for word in ["DENY", "NOT SAFE", "PROHIBIT", "CANNOT", "NO"])
    assert "minor" in content.lower()

@pytest.mark.e2e
def test_e2e_remediation_flow():
    """Follow-up journey: Ask for fix -> Agent generates ES|QL filter."""
    client = AgentClient()
    # Step 1: Establish context (risky data)
    client.chat("Check 'customer_leads_prod' for compliance against NDA.")

    # Step 2: Request remediation
    time.sleep(2) # Brief pause for LLM
    response = client.chat("Can you give me an ES|QL query to filter out those risky records?")

    content, tool_calls, citations = parse_agent_response(response)

    # It should generate an ES|QL query in the content
    assert "FROM" in content.upper()
    assert "WHERE" in content.upper()
    assert "age" in content.lower()

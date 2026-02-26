import pytest
import json
from scripts.agent_client import parse_agent_response

@pytest.mark.unit
def test_response_parsing_text_only():
    """Test parsing a simple text response (Kibana API shape)."""
    mock_response = {
        "response": {"message": "Hello! I am your compliance officer."},
        "steps": []
    }
    content, tool_calls, citations = parse_agent_response(mock_response)
    assert content == "Hello! I am your compliance officer."
    assert tool_calls == []
    assert citations == []

@pytest.mark.unit
def test_response_parsing_with_tool_calls():
    """Test parsing a response that includes tool calls (Kibana API shape)."""
    mock_response = {
        "response": {"message": "I need to check the policy."},
        "steps": [
            {
                "type": "tool_call",
                "tool_call_id": "call_123",
                "tool_id": "policy_retriever",
                "params": {"query": "data privacy"}
            }
        ]
    }
    content, tool_calls, citations = parse_agent_response(mock_response)
    assert content == "I need to check the policy."
    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["name"] == "policy_retriever"

@pytest.mark.unit
def test_citation_extraction_from_content():
    """Test extracting citations from content (Kibana API shape)."""
    mock_response = {
        "response": {"message": "You cannot email minors. [Source: NDA_Partner_A.pdf, Clause 4.2]"},
        "steps": []
    }
    content, tool_calls, citations = parse_agent_response(mock_response)
    assert len(citations) >= 1
    assert "NDA_Partner_A.pdf" in citations[0] or "Clause 4.2" in citations[0]

@pytest.mark.unit
def test_empty_response_handling():
    """Test handling of empty or malformed response."""
    with pytest.raises(ValueError, match="Invalid agent response"):
        parse_agent_response({})

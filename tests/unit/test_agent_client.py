import pytest
import json
from scripts.agent_client import parse_agent_response

@pytest.mark.unit
def test_response_parsing_text_only():
    """Test parsing a simple text response from the agent."""
    mock_response = {
        "content": "Hello! I am your compliance officer.",
        "tool_calls": []
    }
    content, tool_calls, citations = parse_agent_response(mock_response)
    assert content == "Hello! I am your compliance officer."
    assert tool_calls == []
    assert citations == []

@pytest.mark.unit
def test_response_parsing_with_tool_calls():
    """Test parsing a response that includes tool calls."""
    mock_response = {
        "content": "I need to check the policy.",
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "policy_retriever",
                    "arguments": '{"query": "data privacy"}'
                }
            }
        ]
    }
    content, tool_calls, citations = parse_agent_response(mock_response)
    assert content == "I need to check the policy."
    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["name"] == "policy_retriever"

@pytest.mark.unit
def test_citation_extraction_from_content():
    """Test extracting citations from content text.
    Citations are usually formatted like [Source Name](source_id) or similar.
    For this hackathon, we assume a simple [Source: NDA_Partner_A.pdf] format or markdown.
    """
    mock_response = {
        "content": "You cannot email minors. [Source: NDA_Partner_A.pdf, Clause 4.2]",
        "tool_calls": []
    }
    content, tool_calls, citations = parse_agent_response(mock_response)
    assert "NDA_Partner_A.pdf" in citations[0]
    assert "Clause 4.2" in citations[0]

@pytest.mark.unit
def test_empty_response_handling():
    """Test handling of empty or malformed response."""
    with pytest.raises(ValueError, match="Invalid agent response"):
        parse_agent_response({})

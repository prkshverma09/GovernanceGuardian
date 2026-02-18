import pytest
from app_helpers import format_tool_call, format_citation, initialize_session_state
from unittest.mock import MagicMock
import streamlit as st

@pytest.mark.unit
def test_format_tool_call():
    result = format_tool_call("platform.core.search", {"query": "test"})
    assert "platform.core.search" in result
    assert "🛠️" in result

@pytest.mark.unit
def test_format_citation():
    result = format_citation("NDA_Partner_A.pdf")
    assert "NDA_Partner_A.pdf" in result
    assert "📄" in result

@pytest.mark.unit
def test_session_state_initialization():
    # Mock streamlit session state
    st.session_state = {}
    initialize_session_state()
    assert "messages" in st.session_state
    assert st.session_state["messages"] == []
    assert "conversation_id" in st.session_state
    assert st.session_state["conversation_id"] is None

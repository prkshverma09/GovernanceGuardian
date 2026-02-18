import streamlit as st

def format_tool_call(tool_name: str, params: dict):
    """Formats a tool call for display in the UI."""
    return f"🛠️ **Tool Call:** `{tool_name}`"

def format_citation(citation: str):
    """Formats a citation for display."""
    return f"📄 **Source:** {citation}"

def initialize_session_state():
    """Initializes the Streamlit session state."""
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "conversation_id" not in st.session_state:
        st.session_state["conversation_id"] = None

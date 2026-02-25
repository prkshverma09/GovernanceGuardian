import streamlit as st
import os
import requests
from scripts.agent_client import AgentClient, parse_agent_response
from app_helpers import format_tool_call, format_citation, initialize_session_state

# Page configuration
st.set_page_config(
    page_title="Governance Guardian",
    page_icon="🛡️",
    layout="wide",
)

# Initialize state
initialize_session_state()

# Sidebar
with st.sidebar:
    st.title("🛡️ Governance Guardian")
    st.markdown("---")
    st.markdown("""
    **Automated Compliance Officer**

    This agent helps you verify data usage against legal contracts.

    ### Example Queries:
    1. "What is our policy on minors?"
    2. "Can I use 'customer-leads-prod' for marketing?"
    3. "Filter out risky records from the dataset."
    """)
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.rerun()

# Main Chat UI
st.title("Compliance Chat")

# Display message history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "tool_calls" in message and message["tool_calls"]:
            for tc in message["tool_calls"]:
                st.info(tc)
        if "citations" in message and message["citations"]:
            for cit in message["citations"]:
                st.caption(cit)

# User input
if prompt := st.chat_input("Ask a compliance question..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get agent response (Elastic API is synchronous — no streaming; full response after ~30–60s)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown(
            "🔍 **Checking policy and data…**  \n"
            "*The agent runs in the cloud; the first response usually takes 30–60 seconds.*"
        )

        try:
            client = AgentClient()
            response = client.chat(prompt, conversation_id=st.session_state.conversation_id)

            content, tool_calls, citations = parse_agent_response(response)

            # Update conversation ID
            if "conversation_id" in response:
                st.session_state.conversation_id = response["conversation_id"]

            # Display tools and citations
            formatted_tools = [format_tool_call(tc['function']['name'], tc['function'].get('arguments', {})) for tc in tool_calls]
            formatted_citations = [format_citation(cit) for cit in citations]

            for ft in formatted_tools:
                st.info(ft)

            message_placeholder.markdown(content)

            for fc in formatted_citations:
                st.caption(fc)

            # Save message
            st.session_state.messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": formatted_tools,
                "citations": formatted_citations
            })

        except requests.exceptions.Timeout:
            message_placeholder.markdown("")
            st.error("The agent took too long to respond (over 2 minutes). Try again or rephrase your question.")
        except Exception as e:
            message_placeholder.markdown("")
            st.error(f"Error: {str(e)}")

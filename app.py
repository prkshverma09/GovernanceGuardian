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
    4. "Have there been any compliance breaches in the last 7 days?"
    5. "Audit data access logs for high-volume downloads by region."
    """)
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.rerun()
    st.markdown("---")
    st.markdown("**Action-Taker (no Webhook tool?)**")
    st.caption("Uses the ES|QL query from the last assistant message if present; otherwise the default safe query.")

    def _last_esql_from_chat():
        """Extract the most recent ES|QL query from assistant messages (e.g. from a code block)."""
        import re
        for msg in reversed(st.session_state.messages):
            if msg.get("role") != "assistant":
                continue
            content = (msg.get("content") or "")
            # Code blocks: ```esql ... ``` or ``` ... ```
            for block in re.findall(r"```(?:esql)?\s*([\s\S]*?)```", content):
                block = block.strip()
                if "customer_leads_prod" in block and ("WHERE" in block or "|" in block):
                    return block
            # Inline: look for a line starting with FROM customer_leads_prod
            if "FROM customer_leads_prod" in content:
                start = content.find("FROM customer_leads_prod")
                end = content.find("\n\n", start)
                if end == -1:
                    end = len(content)
                return content[start:end].strip()
        return None

    if st.button("Run remediation now", type="secondary"):
        api_base = os.getenv("REMEDIATION_API_URL", "http://localhost:5050").strip().rstrip("/")
        payload = {}
        last_query = _last_esql_from_chat()
        if last_query:
            payload["query"] = last_query
        try:
            r = requests.post(f"{api_base}/remediate", json=payload, timeout=30)
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            if r.status_code == 200 and data.get("error") is None:
                count = data.get("count", 0)
                idx = data.get("index", "customer_leads_safe")
                sample_rows = []
                try:
                    sample_r = requests.get(f"{api_base}/sample", params={"limit": 20}, timeout=10)
                    if sample_r.status_code == 200:
                        sample_data = sample_r.json()
                        sample_rows = sample_data.get("rows", [])
                except Exception:
                    pass
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Remediation executed: created index `{idx}` with **{count}** compliant records.",
                    "tool_calls": [],
                    "citations": [],
                    "remediation_highlight": f"✅ **Safe dataset created:** `{idx}` has {count} records. Use it for compliant marketing.",
                    "remediation_sample": sample_rows,
                })
                st.rerun()
            else:
                st.error(data.get("error", r.text or f"HTTP {r.status_code}"))
        except requests.exceptions.ConnectionError:
            st.error("Remediation API not reachable. Start it: `python scripts/remediation_api.py --serve`")
        except Exception as e:
            st.error(str(e))

# Main Chat UI
st.title("Compliance Chat")

# Display message history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "tool_calls" in message and message["tool_calls"]:
            for tc in message["tool_calls"]:
                st.info(tc)
        if "remediation_highlight" in message and message["remediation_highlight"]:
            st.success(message["remediation_highlight"])
        if "remediation_highlight" in message and message["remediation_highlight"]:
            with st.expander("📋 **Preview: filtered safe dataset**", expanded=True):
                sample_rows = message.get("remediation_sample") or []
                if sample_rows:
                    import pandas as pd
                    df = pd.DataFrame(sample_rows)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    api_base = os.getenv("REMEDIATION_API_URL", "http://localhost:5050").strip().rstrip("/")
                    try:
                        r = requests.get(f"{api_base}/sample", params={"limit": 20}, timeout=5)
                        if r.status_code == 200:
                            data = r.json()
                            rows = data.get("rows", [])
                            if rows:
                                import pandas as pd
                                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                            else:
                                st.caption("No rows in safe index yet.")
                        else:
                            st.caption("Restart the remediation API (with /sample) and run remediation again to see the preview.")
                    except Exception:
                        st.caption("Start the remediation API and click **Run remediation now** again to see the preview.")
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

            formatted_tools = [format_tool_call(tc['function']['name'], tc['function'].get('arguments', {})) for tc in tool_calls]
            formatted_citations = [format_citation(cit) for cit in citations]

            for ft in formatted_tools:
                st.info(ft)

            message_placeholder.markdown(content)

            remediation_highlight = None
            tool_names = [tc["function"]["name"] for tc in tool_calls]
            if "remediate_dataset" in tool_names:
                remediation_highlight = "✅ **Remediation executed:** A sanitized dataset was created (e.g. `customer_leads_safe`). Use it for compliant marketing."
            elif "customer_leads_safe" in content or "sanitized" in content.lower():
                remediation_highlight = "✅ **Safe dataset created.** You can use the new index for compliant campaigns."

            for fc in formatted_citations:
                st.caption(fc)

            if remediation_highlight:
                st.success(remediation_highlight)

            st.session_state.messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": formatted_tools,
                "citations": formatted_citations,
                "remediation_highlight": remediation_highlight,
            })

        except requests.exceptions.Timeout:
            message_placeholder.markdown("")
            st.error("The agent took too long to respond (over 2 minutes). Try again or rephrase your question.")
        except Exception as e:
            message_placeholder.markdown("")
            st.error(f"Error: {str(e)}")

#!/usr/bin/env python3
"""
MCP server exposing Governance Guardian as a compliance-check tool for IDEs.

Run from project root: python mcp_server/server.py
Or: python -m mcp_server.server

Configure Claude Desktop or Cursor to use this server so you can ask
"Is this query compliant with our NDA?" from the editor.
"""
import os
import sys

# Ensure project root is on path when run as script or module
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load env before importing agent_client
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env.local"))

from fastmcp import FastMCP
from scripts.agent_client import AgentClient, parse_agent_response

mcp = FastMCP(
    "Governance Guardian",
    instructions="Compliance officer agent. Use check_compliance to verify data usage or code against legal policies and dataset risks.",
)


@mcp.tool()
def check_compliance(query: str, code_context: str = "") -> str:
    """
    Ask the Governance Guardian compliance agent a question.

    Use this to check if a dataset, query, or workflow is compliant with your
    legal contracts (NDA, DPA, MSA) and data policies. Optionally pass code or
    query text for the agent to evaluate.

    Args:
        query: The compliance question (e.g. "Can I use customer_leads_prod for email marketing?",
               "Is this ES|QL query compliant with our DPA?")
        code_context: Optional code or query snippet to evaluate (e.g. current file or selected ES|QL).
    """
    if not query.strip():
        return "Please provide a compliance question in the 'query' argument."
    message = query
    if (code_context or "").strip():
        message = f"{query}\n\nRelevant code or query to evaluate:\n```\n{code_context.strip()}\n```"
    try:
        client = AgentClient()
        response = client.chat(message)
        content, _tool_calls, _citations = parse_agent_response(response)
        return content
    except Exception as e:
        return f"Compliance check failed: {e}"


if __name__ == "__main__":
    mcp.run()

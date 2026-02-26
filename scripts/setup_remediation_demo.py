#!/usr/bin/env python3
"""
Set up the remediation (Action-Taker) demo via APIs where possible.

1. Resolves the remediation webhook URL (from REMEDIATION_WEBHOOK_URL or ngrok local API).
2. Updates the Governance Guardian agent to include remediate_dataset in tools and system prompt.
3. The Webhook Tool itself cannot be created via the current Kibana API (only esql, index_search,
   workflow, mcp are supported). This script prints the exact URL and steps to add it in Kibana.

Usage:
  - Set REMEDIATION_WEBHOOK_URL in .env to your public URL (e.g. from ngrok) and run:
      python scripts/setup_remediation_demo.py
  - Or run ngrok in another terminal (ngrok http 5050), then run this script;
    it will read the public URL from ngrok's local API and use it.

Requires: .env with ELASTIC_API_KEY, KIBANA_URL (or ELASTICSEARCH_URL to derive it),
          ELASTIC_AGENT_ID (or defaults to governance-guardian).
"""
import os
import sys
import json
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()
load_dotenv(".env.local")

ELASTICSEARCH_URL = (os.getenv("ELASTICSEARCH_URL") or "").strip().rstrip("/")
ELASTIC_API_KEY = (os.getenv("ELASTIC_API_KEY") or "").strip()
KIBANA_URL = (os.getenv("KIBANA_URL") or "").strip().rstrip("/")
AGENT_ID = (os.getenv("ELASTIC_AGENT_ID") or "governance-guardian").strip()

if not ELASTIC_API_KEY:
    print("ERROR: ELASTIC_API_KEY is required in .env")
    sys.exit(1)
if not KIBANA_URL and ELASTICSEARCH_URL and ".es." in ELASTICSEARCH_URL:
    KIBANA_URL = ELASTICSEARCH_URL.replace(".es.", ".kb.")
if not KIBANA_URL:
    print("ERROR: Set KIBANA_URL in .env (or ELASTICSEARCH_URL with .es. in hostname)")
    sys.exit(1)


def kb_get(path, **kwargs):
    return requests.get(
        f"{KIBANA_URL}{path}",
        headers={"Authorization": f"ApiKey {ELASTIC_API_KEY}", "kbn-xsrf": "true"},
        **kwargs,
    )


def kb_put(path, json_body=None, **kwargs):
    return requests.put(
        f"{KIBANA_URL}{path}",
        headers={
            "Authorization": f"ApiKey {ELASTIC_API_KEY}",
            "kbn-xsrf": "true",
            "Content-Type": "application/json",
        },
        json=json_body,
        **kwargs,
    )


def get_webhook_url():
    """Resolve remediation webhook base URL from env or ngrok local API."""
    url = (os.getenv("REMEDIATION_WEBHOOK_URL") or "").strip().rstrip("/")
    if url:
        return url
    try:
        r = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
        if r.status_code != 200:
            return None
        data = r.json()
        for t in data.get("tunnels", []):
            public_url = (t.get("public_url") or "").strip().rstrip("/")
            config = t.get("config", {}) or {}
            addr = config.get("addr", "") or ""
            if "5050" in addr and public_url.startswith("https://"):
                return public_url
        return None
    except Exception:
        return None


def update_agent_with_remediation_tool(agent_id: str):
    """GET agent, add remediate_dataset to tools and system prompt, PUT agent."""
    r = kb_get(f"/api/agent_builder/agents/{agent_id}")
    if r.status_code != 200:
        print(f"   Agent GET failed: {r.status_code} {r.text[:300]}")
        return False
    agent = r.json()
    config = agent.get("configuration") or {}
    instructions = (config.get("instructions") or "").strip()
    tools = config.get("tools") or []
    tool_ids = []
    for t in tools:
        ids = t.get("tool_ids") if isinstance(t, dict) else []
        if ids:
            tool_ids.extend(ids)
    if "remediate_dataset" not in tool_ids:
        tool_ids.append("remediate_dataset")
    prompt_line = (
        'When the user asks you to create a safe list or to remediate the dataset, '
        'you may call remediate_dataset to create a new index with only compliant records.'
    )
    if prompt_line not in instructions:
        instructions = instructions.rstrip() + "\n6. " + prompt_line + "\n"
    body = {
        "name": agent.get("name", "Governance Guardian"),
        "description": agent.get("description", ""),
        "avatar_symbol": agent.get("avatar_symbol", "🛡️"),
        "avatar_color": agent.get("avatar_color", "#4A90D9"),
        "configuration": {
            "instructions": instructions,
            "tools": [{"tool_ids": tool_ids}],
        },
    }
    r = kb_put(f"/api/agent_builder/agents/{agent_id}", json_body=body)
    if r.status_code not in (200, 201):
        print(f"   Agent PUT failed: {r.status_code} {r.text[:400]}")
        return False
    print("   Agent updated: remediate_dataset added to tools and system prompt.")
    return True


def main():
    print("Governance Guardian – Remediation demo setup\n")

    # 1. Webhook URL
    base_url = get_webhook_url()
    if not base_url:
        print("1. Webhook URL")
        print("   Set REMEDIATION_WEBHOOK_URL in .env to your public URL (e.g. from ngrok),")
        print("   or run in another terminal: ngrok http 5050")
        print("   Then re-run this script.\n")
        webhook_remediate_url = "https://<your-ngrok-host>/remediate"
    else:
        webhook_remediate_url = f"{base_url}/remediate"
        print("1. Webhook URL")
        print(f"   Using: {webhook_remediate_url}\n")

    # 2. Webhook tool – Kibana API does not support creating webhook tools; manual step
    print("2. Webhook tool (manual in Kibana)")
    print("   The Agent Builder API only supports esql, index_search, workflow, mcp.")
    print("   Create the Webhook tool in Kibana first:")
    print("   - Agent Builder → Tools → Create tool → Webhook")
    print("   - Tool ID: remediate_dataset")
    print(f"   - URL: {webhook_remediate_url}")
    print("   - Method: POST")
    print("   Then re-run this script to attach the tool to the agent and add the system prompt.\n")

    # 3. Update agent (tool_ids + system prompt) – requires remediate_dataset tool to exist
    print("3. Agent update (via API)")
    if not update_agent_with_remediation_tool(AGENT_ID):
        print("   Tool remediate_dataset does not exist yet. Create it in Kibana (step 2), then re-run this script.\n")
    else:
        print()

    print("Next steps for recording:")
    print("  - Start Remediation API: python scripts/remediation_api.py --serve")
    if not base_url:
        print("  - Run ngrok: ngrok http 5050")
        print("  - In Kibana, set the Webhook tool URL to https://<ngrok-host>/remediate")
    print("  - In Streamlit, ask: 'Create a safe list for me'")
    print()


if __name__ == "__main__":
    main()

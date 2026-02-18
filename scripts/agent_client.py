import os
import re
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def parse_agent_response(response_json: dict):
    """Parses the response from the Elastic Agent Builder (Kibana API).

    Args:
        response_json (dict): The JSON response from the /api/agent_builder/converse endpoint.

    Returns:
        tuple: (content text, tool_calls list, citations list)
    """
    if not response_json or "response" not in response_json:
        # Fallback for error messages or simpler responses
        if "message" in response_json:
             return response_json["message"], [], []
        raise ValueError(f"Invalid agent response: {response_json}")

    content = response_json["response"].get("message", "")
    steps = response_json.get("steps", [])

    tool_calls = []
    for step in steps:
        if step.get("type") == "tool_call":
            # Map Kibana tool call format to a simpler one for our app
            tool_calls.append({
                "id": step.get("tool_call_id"),
                "function": {
                    "name": step.get("tool_id"),
                    "arguments": json.dumps(step.get("params", {}))
                }
            })

    # Extract citations from content
    # Look for [Source: ...] or (Source: ...) or simply [1], [2] styles
    citations = re.findall(r'\[(.*?)\]', content)

    # Filter for citations that look like policies or documents
    citations = [c for c in citations if any(kw in c.lower() for kw in ["source:", ".pdf", "clause", "contract"])]

    return content, tool_calls, citations

class AgentClient:
    def __init__(self, agent_id=None, kb_url=None):
        self.kb_url = kb_url or os.getenv("KIBANA_URL")
        self.api_key = os.getenv("ELASTIC_API_KEY")
        self.agent_id = agent_id or os.getenv("ELASTIC_AGENT_ID")

        # Auto-calculate Kibana URL from Elasticsearch URL if missing
        if not self.kb_url:
            es_url = os.getenv("ELASTICSEARCH_URL")
            if es_url and ".es." in es_url:
                self.kb_url = es_url.replace(".es.", ".kb.")

        if not self.kb_url or not self.api_key:
            raise ValueError("KIBANA_URL (or ELASTICSEARCH_URL) and ELASTIC_API_KEY must be set in .env")

    def chat(self, message: str, conversation_id: str = None):
        """Sends a message to the agent via Kibana API and returns the response.
        """
        if not self.agent_id:
            raise ValueError("ELASTIC_AGENT_ID must be set or passed to AgentClient")

        endpoint = f"{self.kb_url.rstrip('/')}/api/agent_builder/converse"

        headers = {
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json",
            "kbn-xsrf": "true"
        }

        payload = {
            "agent_id": self.agent_id,
            "input": message
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        response = requests.post(endpoint, headers=headers, json=payload)

        if response.status_code >= 400:
            print(f"Error Response Body: {response.text}")

        response.raise_for_status()

        return response.json()

if __name__ == "__main__":
    # Quick manual test
    try:
        client = AgentClient()
        print(f"Agent Client initialized with KbUrl: {client.kb_url}")
    except Exception as e:
        print(f"Initialization error: {e}")

# Governance Guardian MCP Server (IDE Compliance Copilot)

This directory contains an [MCP](https://modelcontextprotocol.io/) server that exposes the Governance Guardian agent as a **check_compliance** tool. Use it from Cursor, Claude Desktop, or any MCP-compatible client to ask compliance questions (e.g. "Is this query compliant with our NDA?") without leaving your editor.

## Prerequisites

- Python 3.10+
- Project `.env` configured (see repo root): `ELASTIC_AGENT_ID`, `ELASTIC_API_KEY`, `KIBANA_URL` or `ELASTICSEARCH_URL`
- Governance Guardian agent and tools already set up in Elastic Cloud

## Install

From the **project root**:

```bash
pip install -r requirements.txt
```

## Run the server (stdio)

From the **project root**:

```bash
python mcp_server/server.py
```

Or:

```bash
python -m mcp_server.server
```

The server uses stdio by default so an MCP client can spawn it and communicate over stdin/stdout.

## Configure Cursor

1. Create or edit **`.cursor/mcp.json`** in this project's root (or in `~/.cursor/mcp.json` for all projects).
2. Add the Governance Guardian server (use the project root as the workspace so the path resolves):

```json
{
  "mcpServers": {
    "governance-guardian": {
      "command": "python",
      "args": ["mcp_server/server.py"],
      "cwd": "/absolute/path/to/GovernanceGuardian"
    }
  }
}
```

Replace `/absolute/path/to/GovernanceGuardian` with your project root. If you open Cursor with the project root as the workspace, you can try:

```json
{
  "mcpServers": {
    "governance-guardian": {
      "command": "python",
      "args": ["mcp_server/server.py"]
    }
  }
}
```

3. Restart Cursor so it picks up the new MCP server.
4. In chat, the **check_compliance** tool will be available. Example: "Run check_compliance with query: Is using customer_leads_prod for email marketing allowed under our DPA? and code_context: (paste your ES|QL or SQL snippet)."

## Configure Claude Desktop

1. Open the Claude Desktop config file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
2. Add the server (ensure `command` runs from the project root so `scripts.agent_client` and `.env` are found):

```json
{
  "mcpServers": {
    "governance-guardian": {
      "command": "python",
      "args": ["/absolute/path/to/GovernanceGuardian/mcp_server/server.py"],
      "cwd": "/absolute/path/to/GovernanceGuardian"
    }
  }
}
```

3. Restart Claude Desktop.

## Tool: check_compliance

- **query** (required): A compliance question, e.g. "Can I use customer_leads_prod for email marketing?" or "Is this ES|QL query compliant with our DPA?"
- **code_context** (optional): Code or query snippet for the agent to evaluate (e.g. current file or selected ES|QL).

The server sends the request to the Elastic Agent Builder agent and returns the agent’s reply (including policy citations and risk assessment when relevant).

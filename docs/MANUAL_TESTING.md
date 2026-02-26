# Manual Testing Guide: Governance Guardian

This document describes how to manually test the Governance Guardian project end-to-end. Use it after completing setup and ingestion to verify the full pipeline (Streamlit → Agent API → Elasticsearch) and to rehearse the demo flow.

---

## Prerequisites

Before manual testing, ensure:

**If you haven’t set up Elastic Cloud yet:** Follow **[ELASTIC_CLOUD_SETUP.md](ELASTIC_CLOUD_SETUP.md)** for deployment, ELSER, API key, data ingestion, and agent configuration.

1. **Python environment** 
   - Python 3.9+
   - Dependencies installed: `pip install -r requirements.txt`

2. **Elastic Cloud**
   - Deployment with ML nodes; ELSER v2 deployed and `started`
   - Agent "Governance Guardian" created and configured per `elastic/agent-config.md`
   - Index Search tool (`policy_retriever`) and ES|QL tool (`dataset_inspector`) attached to the agent
   - Optional: Webhook tool `remediate_dataset` (see `elastic/agent-config.md`) and ES|QL tool `log_auditor` for full feature set

3. **Environment**
   - `.env` created from `.env.example` with:
     - `ELASTIC_CLOUD_ID`
     - `ELASTIC_API_KEY`
     - `ELASTICSEARCH_URL`
     - `ELASTIC_AGENT_ID` (Agent Builder agent ID for the chat API)

4. **Data** (so all 5 sidebar example queries return proper answers)
   - **One-command:** From project root run `python scripts/setup_all_data.py`. This creates/refreshes `customer_leads_prod` and `data_access_logs_prod`.
   - **Contracts (policy query):** Run `python scripts/ingest_contracts.py` so `legal-knowledge-base` is populated (requires ELSER pipeline; see [ELASTIC_CLOUD_SETUP.md](ELASTIC_CLOUD_SETUP.md)).
   - **Breach/audit queries:** The queries *"Have there been any compliance breaches in the last 7 days?"* and *"Audit data access logs for high-volume downloads by region"* need the **log_auditor** ES|QL tool attached to your agent. After `setup_all_data.py`, add the tool in Kibana per `elastic/agent-config.md` §4 (log_auditor). Without it, the agent will report that it has no compliance/audit indices.

---

## 1. Run the Automated Test Suite (Gate)

Run the full test suite to confirm the codebase and integration points are healthy:

```bash
# From project root, with venv activated
pytest tests/ -v --tb=short
```

- **Unit only (no Elastic):**  
  `pytest tests/unit/ -m unit -v`
- **Integration (requires Elastic):**  
  `pytest tests/integration/ -m integration -v`
- **E2E (requires Elastic + configured agent):**  
  `pytest tests/e2e/ -m e2e -v`

**Expected:** All tests that you run (given your environment) pass. Fix any failures before proceeding with manual UI testing.

---

## 2. Start the Streamlit App

```bash
streamlit run app.py
```

- **Where to test:** Open **http://localhost:8501** in your browser.
- Sidebar shows "Governance Guardian", example queries, and a "Clear Chat" button.
- Main area shows "Compliance Chat" and an input: "Ask a compliance question...".

**Other servers (optional):**
- **Remediation API:** see below.
- **MCP server:** `python mcp_server/server.py` → no URL; configure Cursor/Claude per `mcp_server/README.md` and use the **check_compliance** tool in the IDE.

#### Remediation API server (Flask) – what it’s for and how to test it

The **Remediation API** is a small **Flask** HTTP server used by the **Action-Taker** feature. It does not serve the Streamlit UI.

- **What it’s for:** When the user asks the agent to “create a safe list” or “remediate the dataset,” the Elastic Agent Builder can call a **Webhook Tool** (`remediate_dataset`). That webhook calls this API. The API runs a safe ES|QL query against `customer_leads_prod` (excluding minors and GDPR-restricted regions), then **bulk-indexes** the result into a new index (e.g. `customer_leads_safe`). So the agent doesn’t only suggest a fix—it can **execute** it and create the sanitized dataset.

- **When you need it:** Only if you have added the optional Webhook Tool `remediate_dataset` in Kibana and want to test the full Action-Taker flow (agent triggers remediation → new index created → green success box in the Streamlit UI).

**Run the server (from project root):**

```bash
python scripts/remediation_api.py --serve
```

- Default port: **5050** (override with `REMEDIATION_API_PORT` in `.env`).
- Requires the same `.env` as the rest of the project (Elasticsearch URL and API key).

**Test that it’s up:**

1. **Health check:** Open **http://localhost:5050/health** in a browser or run:
   ```bash
   curl http://localhost:5050/health
   ```
   Expected: `{"status":"ok"}`.

2. **Trigger remediation (optional):** Send a POST request to create the safe index:
   ```bash
   curl -X POST http://localhost:5050/remediate -H "Content-Type: application/json" -d '{}'
   ```
   Expected JSON: `{"index": "customer_leads_safe", "count": <number>, "error": null}`. If `error` is not null, check `.env` and that `customer_leads_prod` exists and has data.

**Use with the agent:** In Kibana, create a Webhook Tool with ID `remediate_dataset`, URL `http://localhost:5050/remediate` (or your public URL, e.g. ngrok, if the agent runs in Elastic Cloud), method POST. Attach the tool to the Governance Guardian agent. Then in the Streamlit app, ask e.g. “Create a safe list for me”; you should see the `remediate_dataset` tool call and the green remediation success message.

**CLI (no server):** To run remediation once from the command line without starting the server:
```bash
python scripts/remediation_api.py
```
This prints JSON with `index`, `count`, and `error`.

---

## 3. Manual Test Cases

### 3.1 Policy-only query (knowledge base / RAG)

**Goal:** Confirm the agent uses `policy_retriever` and returns contract citations.

**Steps:**

1. In the chat input, type (or similar):  
   **"What is our policy on emailing minors?"** or **"What does the contract say about data privacy?"**
2. Send the message.

**Expected:**

- A short "Thinking..." state.
- One or more tool-call indicators (e.g. `policy_retriever`).
- A reply that references legal/contract language.
- At least one citation (source document or clause) shown in the UI.

---

### 3.2 Data check – risky dataset (denial path)

**Goal:** Confirm the agent uses `dataset_inspector` and denies usage when the dataset has minors or restricted regions.

**Steps:**

1. In the chat input, type:  
   **"Can I email customer_leads_prod?"** or **"Is it safe to use customer_leads_prod for marketing?"**
2. Send the message.

**Expected:**

- Tool calls visible for both `policy_retriever` and `dataset_inspector` (order may vary).
- Response indicates **denial** (e.g. "DENIED", "not safe", "cannot approve").
- Response includes risk counts (e.g. minors, restricted regions) and/or reference to policy.
- Citations from the knowledge base when relevant.

---

### 3.3 Remediation – safe query

**Goal:** Confirm the agent can suggest a safe ES|QL query that filters out risky records.

**Steps:**

1. After the denial in 3.2 (or in a new chat), ask:  
   **"Filter out risky records"** or **"Give me a safe list"** or **"Can you give me an ES|QL query to exclude minors and restricted regions?"**
2. Send the message.

**Expected:**

- Response includes an ES|QL (or SQL-like) query that filters by age and/or region (e.g. `WHERE Age >= 18`, or equivalent).
- Query is usable in Elastic (e.g. against `customer_leads_prod`).

---

### 3.4 Combined flow (single question)

**Goal:** One question that should trigger both tools and a cited, risk-aware answer.

**Steps:**

1. Clear chat (sidebar: "Clear Chat").
2. Ask:  
   **"Can I use customer_leads_prod for email marketing? Check policy and data."**
3. Send the message.

**Expected:**

- Both `policy_retriever` and `dataset_inspector` appear in tool calls.
- Answer is consistent with actual data (e.g. denial if minors/restricted present) and references policy/citations where appropriate.

---

### 3.5 Action-Taker – remediation execution (optional)

**Goal:** If you have the `remediate_dataset` Webhook Tool configured, confirm the agent can trigger creation of a sanitized index.

**Steps:**

1. Start the remediation API: `python scripts/remediation_api.py --serve` (port 5050). Ensure the Webhook Tool in Kibana points to this URL (or use ngrok for cloud agent).
2. In chat, after a denial (e.g. from 3.2), ask: **"Create a safe list for me"** or **"Remediate the dataset and create a safe index."**
3. Send the message.

**Expected:**

- Tool call for `remediate_dataset` appears.
- Response confirms a new index (e.g. `customer_leads_safe`) was created with compliant records.
- UI shows the green remediation highlight box.

---

### 3.6 Time-Series Auditor – log audit (optional)

**Goal:** If you have the `log_auditor` ES|QL tool and `data_access_logs_prod` populated, confirm the agent can answer breach/audit questions.

**Steps:**

1. Ingest access logs: `python scripts/generate_access_logs.py` then `python scripts/ingest_access_logs.py`.
2. In Kibana, add the `log_auditor` tool per `elastic/agent-config.md` and attach it to the agent.
3. In chat, ask: **"Have there been any compliance breaches in the last 7 days?"** or **"Audit data access logs for high-volume downloads by region."**
4. Send the message.

**Expected:**

- Tool call for `log_auditor` appears.
- Response summarizes access patterns, regions, or high-volume events from the logs.

---

### 3.7 MCP server – IDE Copilot (optional)

**Goal:** Verify the Compliance Copilot works from an MCP client (e.g. Cursor).

**Steps:**

1. From project root: `python mcp_server/server.py` (should start and wait on stdio; Ctrl+C to stop).
2. Configure Cursor (or Claude Desktop) per `mcp_server/README.md` to use this server.
3. In the IDE, invoke the **check_compliance** tool with a query such as: "Is using customer_leads_prod for email marketing allowed under our DPA?"
4. Optionally pass a code snippet in `code_context` (e.g. an ES|QL query) for the agent to evaluate.

**Expected:**

- The agent’s reply is returned in the IDE (citations and risk assessment when relevant).

---

### 3.8 Error handling (optional)

**Goal:** Ensure the app degrades gracefully when the agent or network fails.

**Steps:**

1. Temporarily break config (e.g. wrong `ELASTIC_AGENT_ID` or invalid API key) or disconnect network.
2. Send any compliance question.

**Expected:**

- An error message is shown in the UI (e.g. in the chat area or an error box), and the app does not crash.

Restore correct `.env` after testing.

---

## 4. Demo Script Rehearsal (~3 minutes)

**For the hackathon video:** A narration script optimized for **ElevenLabs TTS** (with SSML tags), plus on-screen timing, is in **[DEMO_SCRIPT_TTS.md](DEMO_SCRIPT_TTS.md)**. Use it together with the flow below.

Use this flow to rehearse the PRD demo (see PRD §6).

| Time       | Action | What to verify |
|-----------|--------|----------------|
| 0:00–0:30 | Intro  | Explain Governance Guardian and the problem it solves. |
| 0:30–1:15 | **Knowledge check** | Ask: *"What is our policy on emailing minors according to the contracts?"* | Agent uses ELSER; reply cites document/clause. |
| 1:15–2:00 | **Data check**      | Ask: *"I want to email the customer_leads_prod list. Is that safe based on the policy?"* | Tool call `dataset_inspector`; reply denies and shows counts (e.g. minors). |
| 2:00–2:45 | **Remediation**     | Ask: *"Can you filter them out and give me a safe list?"* | Reply includes ES|QL (e.g. `WHERE Age >= 18`). |
| 2:45–3:00 | Conclusion         | Summarize value: compliance check in seconds instead of days. |

---

## 5. Demo Tests (Hackathon / Video-Ready)

Use these **exact** flows at **http://localhost:8501** for a polished demo. Copy-paste the queries where indicated.

### Demo A: Core Flow (Policy → Data → Denial → Remediation)

| Step | What you do | Exact query to type | What to show / say |
|------|-------------|---------------------|--------------------|
| 1 | Clear chat (sidebar: **Clear Chat**). | — | "We start with a clean slate." |
| 2 | Ask policy only. | `What is our policy on emailing minors according to the contracts?` | Point out **Tool Call: policy_retriever** and the **Source** citation. Say: "ELSER v2 retrieved the exact clause from our legal index." |
| 3 | Ask if a dataset is safe. | `Can I use customer_leads_prod for email marketing? Check policy and data.` | Point out **policy_retriever** and **dataset_inspector**. Reply should say DENIED with minor/restricted counts. Say: "It checked both the contracts and the live data—and denied with evidence." |
| 4 | Ask for a safe list. | `Give me an ES|QL query to exclude minors and restricted regions so I can run a compliant campaign.` | Reply must include a query with `Age >= 18` and region filter. Say: "It didn’t just block—it gave me a runnable ES|QL query." |

**Success criteria:** All four steps complete; tool badges and citations visible; denial has numbers; remediation has ES|QL.

---

### Demo B: One-Shot “Can I Use This Data?” (Single question)

| Step | What you do | Exact query to type | What to show / say |
|------|-------------|---------------------|--------------------|
| 1 | Clear chat. | — | "One question, full audit." |
| 2 | Ask combined. | `Can I use customer_leads_prod for email marketing? Check policy and data and tell me if it’s approved or denied.` | Both tools should fire; answer should be DENIED with risk counts and a policy citation. Say: "One question—policy plus live data—clear deny with evidence." |

**Success criteria:** Single message triggers both tools; answer is DENIED with counts and citation.

---

### Demo C: Action-Taker (Create Safe Dataset)

**Prereq:** Remediation API running (`python scripts/remediation_api.py --serve`) and Webhook Tool `remediate_dataset` configured in Kibana.

| Step | What you do | Exact query to type | What to show / say |
|------|-------------|---------------------|--------------------|
| 1 | After a denial (e.g. from Demo A step 3), ask for execution. | `Create a safe list for me—remediate the dataset and create a new index with only compliant records.` | **Tool Call: remediate_dataset**; reply confirms index (e.g. `customer_leads_safe`); **green success box** in the UI. Say: "The agent didn’t just suggest—it created the safe index." |

**Success criteria:** `remediate_dataset` tool call; confirmation of new index; green remediation highlight.

---

### Demo D: Time-Series Auditor (Breach / Audit)

**Prereq:** Access logs ingested (`python scripts/generate_access_logs.py` then `python scripts/ingest_access_logs.py`) and `log_auditor` tool attached to the agent.

| Step | What you do | Exact query to type | What to show / say |
|------|-------------|---------------------|--------------------|
| 1 | Clear chat. | — | "Now we audit access logs." |
| 2 | Ask for breaches. | `Have there been any compliance breaches in the last 7 days? Check data access logs.` | **Tool Call: log_auditor**; reply summarizes by time/region or high-volume access. Say: "ES|QL with time bucketing—same agent, now auditing who accessed what." |
| 3 | Optional follow-up. | `Which region had the most records downloaded in the last week?` | Reply uses log data (region, counts). |

**Success criteria:** `log_auditor` runs; answer references access logs, regions, or volumes.

---

### Demo E: “Wow” Single Question (Policy + Data + Remediation in one go)

| Step | What you do | Exact query to type | What to show / say |
|------|-------------|---------------------|--------------------|
| 1 | Clear chat. | — | "Everything in one ask." |
| 2 | Ask full flow. | `I want to run an email campaign on customer_leads_prod. Check our contracts and the data. If it’s not safe, tell me why and give me an ES|QL query to get a compliant subset.` | Multiple tool calls (policy + dataset_inspector); reply: denial reason, risk counts, and a safe ES|QL query. Say: "One question—policy check, data check, and remediation query." |

**Success criteria:** Denial with evidence plus a runnable safe ES|QL query in one reply.

---

### Demo F: MCP Copilot (IDE)

**Prereq:** Cursor (or Claude Desktop) configured with the Governance Guardian MCP server per `mcp_server/README.md`.

| Step | What you do | What to show / say |
|------|-------------|--------------------|
| 1 | In Cursor chat, invoke the **check_compliance** tool. | Query: `Is using customer_leads_prod for email marketing allowed under our DPA?` |
| 2 | Optionally add code context. | Pass an ES|QL snippet in `code_context` (e.g. `FROM customer_leads_prod \| LIMIT 10`) and ask: "Is this query compliant?" |
| 3 | Show the reply in the IDE. | Say: "Compliance check without leaving the editor—same agent via MCP." |

**Success criteria:** Agent reply (with citations/risk when relevant) returned inside the IDE.

---

## 6. Quick Checklist

- [ ] `pytest tests/ -v` (or unit/integration/e2e subsets) pass
- [ ] `streamlit run app.py` starts and loads the chat UI at http://localhost:8501
- [ ] Policy-only question returns citations and uses `policy_retriever`
- [ ] "Can I email customer_leads_prod?" triggers both tools and a denial with risk counts
- [ ] "Filter out risky records" (or similar) returns a safe ES|QL query
- [ ] Combined question uses both tools and gives a consistent, cited answer
- [ ] Demo A (Core Flow) or Demo E (Wow single question) runs smoothly for the video
- [ ] (Optional) Demo C: Remediation API + `remediate_dataset` → green highlight
- [ ] (Optional) Demo D: Access logs + `log_auditor` → breach/audit summary
- [ ] (Optional) Demo F: MCP `check_compliance` works in Cursor/Claude Desktop

---

## 7. Troubleshooting

| Issue | What to check |
|-------|----------------|
| "Error" in chat, no reply | `.env` (especially `ELASTIC_AGENT_ID`, `ELASTIC_API_KEY`); Agent Builder API access; network. |
| No tool calls shown | Agent configuration in Elastic: both tools attached and correctly named. |
| No citations | `legal-knowledge-base` has documents; ELSER pipeline and `policy_retriever` point to that index. |
| Wrong or no risk counts | `customer_leads_prod` ingested; `dataset_inspector` ES|QL uses correct index and field names (`age`, `country`). |
| Tests fail (e.g. `ModuleNotFoundError`) | Activate venv and run `pip install -r requirements.txt`. |
| Integration/e2e tests fail | Elastic deployment reachable; ELSER started; agent and indexes created and populated. |
| Remediation fails or no highlight | Remediation API running (`python scripts/remediation_api.py --serve`); Webhook Tool URL reachable from Elastic Cloud (use ngrok if needed). |
| log_auditor returns nothing | Index `data_access_logs_prod` exists and has data; ES|QL tool uses correct index and time range. |
| "No compliance breach records" / "no audit data" | Run `python scripts/setup_all_data.py` to create `data_access_logs_prod`, then add the **log_auditor** tool to the agent in Kibana (`elastic/agent-config.md` §4). |
| MCP tool not visible in Cursor | Restart Cursor after editing `.cursor/mcp.json`; ensure `cwd` is project root and `python` resolves to the venv. |

---

*Last updated to match the implementation plan and current codebase.*

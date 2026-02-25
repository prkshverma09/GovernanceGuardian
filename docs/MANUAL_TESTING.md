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

3. **Environment**
   - `.env` created from `.env.example` with:
     - `ELASTIC_CLOUD_ID`
     - `ELASTIC_API_KEY`
     - `ELASTICSEARCH_URL`
     - `ELASTIC_AGENT_ID` (Agent Builder agent ID for the chat API)

4. **Data**
   - Contract text: sample `.txt` files are in `data/contracts/` (included in repo). Optionally add PDFs or run `python scripts/generate_contracts.py` to generate PDFs.
   - Customer data: run `python scripts/generate_customers.py`, then `python scripts/ingest_customers.py`
   - Indexes populated: `legal-knowledge-base` and `customer_leads_prod`

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

- App should open in the browser (e.g. http://localhost:8501).
- Sidebar shows "Governance Guardian", example queries, and a "Clear Chat" button.
- Main area shows "Compliance Chat" and an input: "Ask a compliance question...".

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

### 3.5 Error handling (optional)

**Goal:** Ensure the app degrades gracefully when the agent or network fails.

**Steps:**

1. Temporarily break config (e.g. wrong `ELASTIC_AGENT_ID` or invalid API key) or disconnect network.
2. Send any compliance question.

**Expected:**

- An error message is shown in the UI (e.g. in the chat area or an error box), and the app does not crash.

Restore correct `.env` after testing.

---

## 4. Demo Script Rehearsal (~3 minutes)

Use this flow to rehearse the PRD demo (see PRD §6).

| Time       | Action | What to verify |
|-----------|--------|----------------|
| 0:00–0:30 | Intro  | Explain Governance Guardian and the problem it solves. |
| 0:30–1:15 | **Knowledge check** | Ask: *"What is our policy on emailing minors according to the contracts?"* | Agent uses ELSER; reply cites document/clause. |
| 1:15–2:00 | **Data check**      | Ask: *"I want to email the customer_leads_prod list. Is that safe based on the policy?"* | Tool call `dataset_inspector`; reply denies and shows counts (e.g. minors). |
| 2:00–2:45 | **Remediation**     | Ask: *"Can you filter them out and give me a safe list?"* | Reply includes ES|QL (e.g. `WHERE Age >= 18`). |
| 2:45–3:00 | Conclusion         | Summarize value: compliance check in seconds instead of days. |

---

## 5. Quick Checklist

- [ ] `pytest tests/ -v` (or unit/integration/e2e subsets) pass
- [ ] `streamlit run app.py` starts and loads the chat UI
- [ ] Policy-only question returns citations and uses `policy_retriever`
- [ ] "Can I email customer_leads_prod?" triggers both tools and a denial with risk counts
- [ ] "Filter out risky records" (or similar) returns a safe ES|QL query
- [ ] Combined question uses both tools and gives a consistent, cited answer
- [ ] Demo script (PRD §6) runs smoothly in under ~3 minutes

---

## 6. Troubleshooting

| Issue | What to check |
|-------|----------------|
| "Error" in chat, no reply | `.env` (especially `ELASTIC_AGENT_ID`, `ELASTIC_API_KEY`); Agent Builder API access; network. |
| No tool calls shown | Agent configuration in Elastic: both tools attached and correctly named. |
| No citations | `legal-knowledge-base` has documents; ELSER pipeline and `policy_retriever` point to that index. |
| Wrong or no risk counts | `customer_leads_prod` ingested; `dataset_inspector` ES|QL uses correct index and field names (`age`, `country`). |
| Tests fail (e.g. `ModuleNotFoundError`) | Activate venv and run `pip install -r requirements.txt`. |
| Integration/e2e tests fail | Elastic deployment reachable; ELSER started; agent and indexes created and populated. |

---

*Last updated to match the implementation plan and current codebase.*

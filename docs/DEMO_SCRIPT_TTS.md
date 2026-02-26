# Demo Video Narration — Guide

**Script files (TTS-ready, narration only):**
- **SSML (ElevenLabs):** [demo_narration_ssml.ssml](demo_narration_ssml.ssml) — paste entire file into ElevenLabs.
- **Plain text:** [demo_narration_plain.txt](demo_narration_plain.txt) — for rehearsal or TTS without SSML.

**Hackathon:** [Elasticsearch Agent Builder Hackathon](https://elasticsearch.devpost.com/?ref_feature=challenge&ref_medium=discover)  
**Judging:** Technical Execution 30%, Potential Impact & Wow Factor 30%, Demo 30%, Social 10%.

---

## On-screen actions to sync with narration

| Time (approx) | Narration beat | What to show |
|---------------|----------------|--------------|
| 0:00–0:20 | Intro, problem | Streamlit UI; show contracts in knowledge base and data access (customer leads, access logs). Say “Governance Guardian”, “30-second chat”. |
| 0:20–0:55 | Policy / ELSER | Type: *What is our policy on emailing minors according to the contracts?* Show **Tool Call: policy_retriever** and **Source** citation. |
| 0:55–1:35 | Data check / ES\|QL | Type: *Can I use customer_leads_prod for email marketing? Check policy and data.* Show both tools; **DENIED** with counts. |
| 1:35–2:15 | Remediation / Action-Taker | Type: *Give me an ES\|QL query to exclude minors and restricted regions* — show query. Click **Run remediation now** in sidebar → green success box → expand **Preview: filtered safe dataset** to show the compliant rows table. |
| 2:15–2:45 | Auditor + MCP | Optional: *Have there been any compliance breaches in the last 7 days?* Show **log_auditor**. Then show **Claude Desktop**: add the local running MCP server and use **check_compliance** tool. |
| 2:45–3:00 | Conclusion | Recap: ELSER, ES\|QL, Agent Builder; “Thank you.” |

---

## Before recording: Make remediation (Action-Taker) work locally

**Will it work right now?** Only if (1) the Remediation API is running, (2) Elastic Cloud can reach it, and (3) the agent has the Webhook tool configured. The agent runs in **Elastic Cloud**, so it cannot call `http://localhost:5050` — you must expose your local server to the internet.

**If your Kibana has no "Webhook" tool type:** Many deployments only show **MCP**, **ES|QL**, and **Index search** under Create tool. You can still demo the Action-Taker: (1) Ask the agent *Give me an ES|QL query to exclude minors and restricted regions* and show the query. (2) In the Streamlit **sidebar**, click **"Run remediation now"** — it calls the remediation API and shows the green success message. No Webhook tool or ngrok needed; just run `python scripts/remediation_api.py --serve` locally.

**Automated setup (when Webhook exists):** Run `python scripts/setup_remediation_demo.py`. It resolves the webhook URL and updates the agent via API; create the Webhook tool in Kibana if that option is available.

**Do this before recording the demo:**

1. **Data**  
   Ensure `customer_leads_prod` has data (e.g. run `python scripts/setup_all_data.py` then `python scripts/ingest_customers.py`).

2. **Start the Remediation API (local)**  
   From project root with venv activated:
   ```bash
   python scripts/remediation_api.py --serve
   ```
   Server listens on port 5050. Verify: open http://localhost:5050/health → `{"status":"ok"}`.

3. **Expose port 5050 to the internet (ngrok)**  
   So Elastic Cloud can call your API:
   ```bash
   ngrok http 5050
   ```
   Note the **HTTPS** URL ngrok shows (e.g. `https://abc123.ngrok-free.app`).

4. **Point the agent's Webhook at your public URL**  
   In **Kibana**: Agent Builder → your agent → Tools. Edit or create the Webhook tool:
   - **Tool ID:** `remediate_dataset`
   - **URL:** `https://<your-ngrok-host>/remediate` (e.g. `https://abc123.ngrok-free.app/remediate`)
   - **Method:** POST  
   Save and ensure the tool is attached to the Governance Guardian agent.

5. **Optional: system prompt**  
   If the agent doesn't call the tool when you say "Create a safe list for me", add to the agent's system prompt (see `elastic/agent-config.md` §3):  
   *"When the user asks you to create a safe list or to remediate the dataset, you may call `remediate_dataset` to create a new index with only compliant records."*

6. **Record**  
   Keep the Remediation API and ngrok running. In Streamlit, ask *Give me an ES|QL query to exclude minors and restricted regions* (show query), then *Create a safe list for me* — you should see the `remediate_dataset` tool call and the green success box.

**Quick test without the agent:**  
`curl -X POST http://localhost:5050/remediate -H "Content-Type: application/json" -d '{}'`  
→ Expect `{"index":"customer_leads_safe","count":<n>,"error":null}`.

---

## Elastic technologies highlighted (for judges)

- **Elasticsearch** — retrieval platform (structured, unstructured, real-time).
- **ELSER v2** — semantic search over legal documents (`legal-knowledge-base`).
- **ES|QL** — pipelined queries for dataset inspection, remediation, and time-series audit.
- **Elastic Agent Builder** — reasoning model + tool orchestration (Search, ES|QL, Webhook).
- **Tools:** `policy_retriever` (Search/ELSER), `dataset_inspector` (ES|QL), `remediate_dataset` (Webhook), `log_auditor` (ES|QL time-series).
- **MCP** — same agent in the IDE (Cursor / Claude Desktop).

---

*Use with the demo flows in [MANUAL_TESTING.md](MANUAL_TESTING.md) §5 (Demo Tests).*

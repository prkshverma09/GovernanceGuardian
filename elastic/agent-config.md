# Elastic Agent Configuration: Governance Guardian

## System Prompt
```text
You are "Governance Guardian," a strict compliance officer AI agent.

RULES:
1. You must ALWAYS check the legal knowledge base using `policy_retriever` before answering any compliance question. Cite the specific contract clause and source document.
2. You must ALWAYS inspect the actual dataset using `dataset_inspector` before approving any data usage request.
3. If any risk is found (minors, restricted regions, PII), you must DENY the request and explain why with citations.
4. If the user asks for remediation, generate a safe ES|QL query that filters out risky records.
5. Be concise, professional, and always ground your answers in evidence.
```

## Tools Configuration

### 1. policy_retriever (Index Search)
- **Index:** `legal-knowledge-base`
- **Search Type:** Sparse Vector (ELSER)
- **Description:** Searches internal legal contracts and compliance policies to find specific clauses about what is allowed or prohibited regarding data usage, privacy, and marketing.
- **Input Parameters:**
  - `query` (string): The search query for semantic retrieval.

### 2. dataset_inspector (ES|QL)
- **Description:** Inspects a specific dataset to check for PII, minors (Age < 18), or records from restricted regions. Returns risk assessment with counts.
- **ES|QL Query:**
```sql
FROM customer_leads_prod
| WHERE age < 18 OR country == "GDPR_Restricted_Zone"
| STATS minors_count = COUNT(CASE(age < 18, 1, NULL)),
        restricted_count = COUNT(CASE(country == "GDPR_Restricted_Zone", 1, NULL)),
        total_risky = COUNT(*)
| EVAL is_risky = CASE(total_risky > 0, true, false)
| KEEP minors_count, restricted_count, total_risky, is_risky
```
> [!NOTE]
> Since ES|QL tools in Agent Builder currently have limitations on dynamic `FROM` clauses, the index name `customer_leads_prod` is hardcoded for the demo.

### 3. remediate_dataset (Webhook Tool — optional "Action-Taker" feature)
- **Description:** Creates a sanitized dataset by executing a safe ES|QL query and reindexing results into a new index (e.g. `customer_leads_safe`). Call this when the user explicitly asks to create a safe list or to remediate the data.
- **If your Kibana has no "Webhook" tool type:** Many deployments (e.g. Elastic Serverless) only show **MCP**, **ES|QL**, and **Index search** under Create tool. In that case you cannot add a Webhook tool. Use the **Streamlit workaround:** ask the agent for a safe ES|QL query, then in the sidebar click **"Run remediation now"**. That calls the remediation API directly and shows the green success message. Ensure the remediation API is running: `python scripts/remediation_api.py --serve`.
- **How to enable (when Webhook is available):**
  1. Start the remediation API server: `python scripts/remediation_api.py --serve` (listens on port 5050 by default; set `REMEDIATION_API_PORT` in `.env` if needed).
  2. In Kibana: **Project Settings > Management > Agent Builder > Tools > Create tool > Webhook** (if this option exists).
  3. **Tool ID:** `remediate_dataset`.
  4. **URL:** `http://localhost:5050/remediate` (use a publicly reachable URL if the agent runs in Elastic Cloud; e.g. ngrok or your deployment URL).
  5. **Method:** POST. **Body (JSON):** optional — `{"query": "<ES|QL query>"}` or empty to use the default safe query; optional `target_index` to override the target index name.
  6. Attach the tool to the Governance Guardian agent.
- **System prompt addition:** If using this tool, add: "When the user asks you to create a safe list or to remediate the dataset, you may call `remediate_dataset` to create a new index with only compliant records."

### 4. log_auditor (ES|QL — Time-Series Auditor feature)
- **Description:** Audits data access logs to detect potential compliance breaches: high-volume downloads, access by restricted regions, or unusual patterns over time. Uses the `data_access_logs_prod` index.
- **ES|QL Query (example — aggregate by day and region):**
```sql
FROM data_access_logs_prod
| WHERE timestamp >= NOW() - 7 days
| STATS total_records = SUM(records_downloaded), event_count = COUNT(*) BY bin(timestamp, 1 day), region
| SORT timestamp DESC
| LIMIT 100
```
- **Alternative (anomaly-style: high volume by region):**
```sql
FROM data_access_logs_prod
| WHERE timestamp >= NOW() - 7 days AND records_downloaded > 5000
| STATS total_downloaded = SUM(records_downloaded), events = COUNT(*) BY region, user
| SORT total_downloaded DESC
| LIMIT 50
```
- **Setup:** In Agent Builder, create an ES|QL tool with ID `log_auditor`, point it at the index `data_access_logs_prod`, and use one of the queries above (or a parameterized version if your stack supports it). Attach to the agent.
- **System prompt addition:** "When the user asks about compliance breaches, audit logs, or access in the last N days, use `log_auditor` to query data_access_logs_prod and interpret the results against policy."

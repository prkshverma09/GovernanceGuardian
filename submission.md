# Devpost Submission: Governance Guardian

Use this document to copy-paste your content into the [Elasticsearch Agent Builder Hackathon](https://elasticsearch.devpost.com/?ref_feature=challenge&ref_medium=discover) submission form.

---

## 1. Brief Description (~400 words)

**The Problem Solved**

In modern data-driven organizations, there is a massive friction point between data teams and legal/compliance teams. A data scientist or marketing manager wants to use a dataset (e.g., for an email campaign), but they must wait days for a compliance officer to manually review complex regulatory policies (GDPR, CCPA) or specific client contracts (NDAs, MSAs) to ensure the dataset is safe to use. This bottleneck kills speed and agility. Governance Guardian solves this by acting as an automated "Level 1 Compliance Officer," turning a multi-day legal review into a 30-second automated check.

**Features Used**

Governance Guardian is a multi-step AI agent built on **Elastic Agent Builder**. It leverages the power of Elasticsearch for both unstructured and structured data analysis:

1. **Semantic Search with ELSER v2:** We use Elastic's Learned Sparse EncodeR (ELSER v2) to semantically index and search through dense legal PDF contracts and compliance policies (`legal-knowledge-base`).
2. **Structured Data Inspection with ES|QL:** We use Elastic's pipelined query language (ES|QL) to dynamically query and aggregate the actual production datasets (`customer_leads_prod`) in real-time.
3. **Tool Orchestration:** The Agent Builder is configured with custom tools (`policy_retriever`, `dataset_inspector`, and optionally `remediate_dataset`, `log_auditor`). The reasoning model autonomously decides when to read the rules, inspect the data, run remediation, or audit logs.
4. **Action-Taker (Webhook + ES|QL):** A remediation API (triggered from the Streamlit UI via "Run remediation now") executes a safe ES|QL query and reindexes compliant records into a new index (e.g. `customer_leads_safe`), so the agent doesn't just advise—it creates the safe dataset, with a preview of filtered rows in the UI.
5. **Time-Series Auditor (ES|QL):** A `log_auditor` ES|QL tool queries the `data_access_logs_prod` index with time bucketing and aggregations by region to detect compliance breaches and high-volume access patterns.
6. **IDE Compliance Copilot (MCP):** We expose the agent as an MCP server with a `check_compliance` tool, so data engineers can ask compliance questions from Cursor or Claude Desktop without leaving the editor.

**Features We Liked & Challenges Overcome**

* **What we liked:** The seamless integration of **ES|QL** within the Agent Builder framework was a standout feature. Being able to give an LLM the ability to not just write, but *execute* pipelined aggregations against live data is incredibly powerful. It bridges the gap between hallucinated answers and grounded, mathematical reality. We also loved how easy it was to set up **ELSER v2** for out-of-the-box semantic search without managing external vector databases.
* **Challenges:** One of our main challenges was tuning the agent's system prompt to ensure it reliably executed *both* tools for complex queries. Initially, the agent would sometimes rely on general knowledge instead of inspecting the dataset. We overcame this by refining the tool descriptions and strictly instructing the agent in the Agent Builder UI to *always* use `dataset_inspector` before approving data usage, and to *always* cite the `policy_retriever`. We also found that the Kibana API does not support creating Webhook-type tools; we worked around this by adding a "Run remediation now" button in the Streamlit app that calls our remediation API directly and shows the safe-dataset preview.

---

## 2. Demonstration Video (~3 minutes)

**Video URL:** https://youtu.be/vwjl4Ws4UGo

---

## 3. Source Code Repository

**Repository URL:** *(Replace with your public GitHub URL, e.g. `https://github.com/your-username/GovernanceGuardian`)*

The code repository is **public** and uses an **OSI-approved license** (MIT). See the [LICENSE](LICENSE) file in the repo.

---

## 4. Bonus: Level-Up Features (for judges)

- **Action-Taker:** The app triggers a remediation API to create a sanitized index (`customer_leads_safe`) and shows a "Preview: filtered safe dataset" table—so we don't just suggest a fix, we execute it and show the compliant rows.
- **Time-Series Auditor:** With the `log_auditor` ES|QL tool and `data_access_logs_prod`, the agent answers questions like "Have there been any compliance breaches in the last 7 days?" using time bucketing and region aggregations.
- **MCP Compliance Copilot:** An MCP server exposes `check_compliance(query, code_context)` so developers can check compliance from Cursor or Claude Desktop; see `mcp_server/README.md`.

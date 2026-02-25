# Elastic Cloud Setup for Manual Testing

This guide walks you through setting up an Elastic Cloud deployment and configuring it for Governance Guardian so you can run manual testing and the Streamlit chat.

---

## Option A: Automated setup via API (recommended)

If you already have an **Elastic Cloud deployment** (and an API key with Elasticsearch + Kibana permissions), you can run a single script that configures indices, pipeline, ELSER, data ingestion, and the Agent Builder agent via APIs.

1. **Create a deployment** in [Elastic Cloud](https://cloud.elastic.co/) (trial is fine). Ensure it has **ML** capacity so ELSER can run.
2. **Create an API key** in Kibana (Stack Management → API Keys) with privileges: `manage_ml`, manage indices/ingest, and **Kibana** “manage_agent_builder” (or full admin).
3. **Configure `.env`** in the project root:

   ```env
   ELASTIC_API_KEY=your_api_key_here
   ELASTICSEARCH_URL=https://your-deployment.es.region.gcp.cloud.es.io:443
   ```
   If you use **Cloud ID** instead of URL, set `ELASTIC_CLOUD_ID` and **KIBANA_URL** (e.g. `https://your-deployment.kb.region.gcp.cloud.es.io`).

4. **Run the setup script** (from project root, with venv activated):

   ```bash
   python scripts/setup_elastic_api.py
   ```

   The script will:
   - Start the ELSER v2 deployment (if not already started)
   - Create `legal-knowledge-base` index and `legal-elser-pipeline`
   - Create `customer_leads_prod` index
   - Ingest contract data from `data/contracts/` and customer data (generating `data/customers.csv` if missing)
   - Create the Agent Builder tools `policy_retriever` and `dataset_inspector`
   - Create the **Governance Guardian** agent

5. **Add the printed agent ID to `.env`:**

   ```env
   ELASTIC_AGENT_ID=governance-guardian
   ```

6. Start the app: `streamlit run app.py`, and run the manual tests in [MANUAL_TESTING.md](MANUAL_TESTING.md).

If any step fails (e.g. ELSER not available, or Agent Builder API differences), use **Option B** below to complete setup in the Kibana UI.

---

## Option B: Manual setup in Kibana

You will:

1. Create an Elastic Cloud deployment (or use a free trial).
2. Deploy the ELSER v2 model for semantic search.
3. Create an API key and note your Cloud ID / Elasticsearch URL.
4. Ingest contract and customer data (using this project’s scripts).
5. Create the “Governance Guardian” agent with two tools.
6. Fill `.env` and run the app.

**Time:** About 20–30 minutes (plus ELSER deploy time).

---

## 1. Create an Elastic Cloud deployment

1. Go to [elastic.co/cloud](https://www.elastic.co/cloud/) and sign in or create an account.
2. **Option A – Free trial**
   - Create a new deployment (or use “Start free trial”).
   - Choose a **region** and a **deployment type** that supports **Machine Learning** (e.g. “Elasticsearch” with ML nodes, or “Serverless” if available).
   - Ensure the deployment has **ML capacity** so ELSER can run (trial usually includes this).
3. **Option B – Existing deployment**
   - Use a deployment that already has ML nodes (or add ML to the topology).
4. Wait until the deployment is **Healthy**. Note the **Kibana** URL (you’ll open it in the browser).

---

## 2. Get credentials (Cloud ID, API key, URLs)

### 2.1 Where to get ELASTICSEARCH_URL and ELASTIC_CLOUD_ID

1. Go to **[Elastic Cloud Console](https://cloud.elastic.co/)** and sign in.
2. Open your **deployment** (click its name or “Open”).
3. On the deployment overview page you’ll see:
   - **Elasticsearch** – copy the **endpoint URL** (e.g. `https://abc123.es.us-central1.gcp.cloud.es.io:443`).  
     → Use this as **`ELASTICSEARCH_URL`** in `.env`. Include `:443` if it’s shown.
   - **Cloud ID** – a string like `my-deployment:ZXUtY2VudHJhb...` (sometimes under “Manage” or in the same panel).  
     → Use this as **`ELASTIC_CLOUD_ID`** in `.env` if you prefer Cloud ID over the URL.

**You only need one of them** for this project: either **ELASTICSEARCH_URL** or **ELASTIC_CLOUD_ID**.  
If you have both, **ELASTICSEARCH_URL** is usually enough (and is used to derive Kibana URL when **KIBANA_URL** is not set).

**Kibana URL (for the setup script and chat):**  
- Either set **`KIBANA_URL`** in `.env` (e.g. `https://abc123.kb.us-central1.gcp.cloud.es.io`).  
- Or leave it unset and the script will derive it from **ELASTICSEARCH_URL** by replacing `.es.` with `.kb.` (e.g. `https://abc123.kb.us-central1.gcp.cloud.es.io`).

### 2.2 Create an API key

1. In **Stack Management** → **API Keys** (or **Security** → **API Keys**), click **Create API key**.
2. Name it (e.g. `GovernanceGuardian-manual-testing`).
3. Give it a role that has:
   - **Elasticsearch**: `all` or at least read/write/index on the indices you’ll use (`legal-knowledge-base`, `customer_leads_prod`) and permission to manage ML (trained models, ingest pipelines).
   - **Kibana**: “Kibana Admin” or equivalent so the Agent Builder API can be used.
4. Copy the **API key** and store it somewhere safe (it’s shown only once). You’ll put it in `.env` as `ELASTIC_API_KEY`.

---

## 3. Deploy ELSER v2 (semantic search)

1. In Kibana, go to **Machine Learning** → **Trained Models** (or **Stack Management** → **Machine Learning** → **Trained Models**).
2. Find **ELSER** (e.g. `.elser_model_2` or “Elastic Learned Sparse EncodeR”).
3. Click **Deploy** (or **Start**) and wait until status is **Started** / **started**. This can take a few minutes.
4. Optional check via Dev Tools (Kibana → Dev Tools):

   ```json
   GET _ml/trained_models/.elser_model_2/stats
   ```

   Confirm the model is `started`.

---

## 4. Prepare `.env` (so ingest scripts can run)

In the project root, create `.env` from the example and fill what you already have:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Use ELASTICSEARCH_URL if you have the full URL; otherwise use ELASTIC_CLOUD_ID
ELASTIC_CLOUD_ID=your_cloud_id_here
ELASTIC_API_KEY=your_api_key_here
ELASTICSEARCH_URL=https://your-deployment.es.region.gcp.cloud.es.io:443

# Agent ID – fill this after creating the agent (see below)
ELASTIC_AGENT_ID=
```

Save the file. You can leave `ELASTIC_AGENT_ID` empty until the agent is created.

**Where to get ELASTIC_AGENT_ID**

- **If you used the API setup script:** After running `python scripts/setup_elastic_api.py`, it prints `ELASTIC_AGENT_ID=governance-guardian`. Copy that into your `.env` or `.env.local`.
- **If you created the agent in Kibana:** In Kibana go to **Machine Learning** (or **Search**) → **Agent Builder** / **Agents**, open your “Governance Guardian” agent. The **agent ID** is in the page URL (e.g. `.../agents/governance-guardian`) or in the agent’s **Settings** / **API** section. Use that value (e.g. `governance-guardian`) as `ELASTIC_AGENT_ID`.

---

## 5. Ingest data (contracts and customers)

Run these from the project root with your venv activated.

### 5.1 Contract data

1. Verify contract files:
   ```bash
   python scripts/verify_contract_data.py
   ```
   You should see 3 `.txt` files and 11 chunks.

2. Ingest contracts (creates index, pipeline, and ELSER embeddings):
   ```bash
   python scripts/ingest_contracts.py
   ```
   This script will:
   - Create/update the `legal-elser-pipeline` ingest pipeline.
   - Create the `legal-knowledge-base` index.
   - Ingest all `data/contracts/*.txt` (and `*.pdf` if present).

### 5.2 Customer data

1. Generate synthetic customers:
   ```bash
   python scripts/generate_customers.py
   ```
   This creates `data/customers.csv`.

2. Ingest customers:
   ```bash
   python scripts/ingest_customers.py
   ```
   This creates the `customer_leads_prod` index with the expected mapping.

---

## 6. Create the “Governance Guardian” agent in Kibana

1. In Kibana, open **Machine Learning** (or **Search**) → **Agent Builder** / **Agents** (the exact menu name depends on your Elastic version).
2. Create a **new agent**.
3. **Name:** `Governance Guardian` (or any name; you’ll use the agent ID in `.env`).
4. **System prompt:** Paste exactly:

   ```text
   You are "Governance Guardian," a strict compliance officer AI agent.

   RULES:
   1. You must ALWAYS check the legal knowledge base using policy_retriever before answering any compliance question. Cite the specific contract clause and source document.
   2. You must ALWAYS inspect the actual dataset using dataset_inspector before approving any data usage request.
   3. If any risk is found (minors, restricted regions, PII), you must DENY the request and explain why with citations.
   4. If the user asks for remediation, generate a safe ES|QL query that filters out risky records.
   5. Be concise, professional, and always ground your answers in evidence.
   ```

5. **Add two tools:**

   **Tool 1 – Index Search (policy_retriever)**  
   - Type: **Index Search** (or “Semantic / Sparse search”).  
   - Index: `legal-knowledge-base`.  
   - Model: **ELSER** (`.elser_model_2` or the ELSER option shown).  
   - Description (or similar): *Searches internal legal contracts and compliance policies to find specific clauses about what is allowed or prohibited regarding data usage, privacy, and marketing.*  
   - Parameter: `query` (string).

   **Tool 2 – ES|QL (dataset_inspector)**  
   - Type: **ES|QL**.  
   - Description: *Inspects a specific dataset to check for PII, minors (Age < 18), or records from restricted regions. Returns risk assessment with counts.*  
   - Query (paste as one block; line breaks are optional):

   ```sql
   FROM customer_leads_prod
   | WHERE age < 18 OR country == "GDPR_Restricted_Zone"
   | STATS minors_count = COUNT(CASE(age < 18, 1, NULL)),
           restricted_count = COUNT(CASE(country == "GDPR_Restricted_Zone", 1, NULL)),
           total_risky = COUNT(*)
   | EVAL is_risky = CASE(total_risky > 0, true, false)
   | KEEP minors_count, restricted_count, total_risky, is_risky
   ```

6. Save the agent.  
7. **Copy the Agent ID** (from the agent’s URL or a “Copy ID” / “API” section). It’s often a UUID. You’ll put it in `.env` as `ELASTIC_AGENT_ID`.

Reference: `elastic/agent-config.md` and `elastic/tool-definitions.json` in this repo.

---

## 7. Set the Agent ID in `.env` (for Streamlit)

Edit `.env` and set:

```env
ELASTIC_AGENT_ID=your_agent_id_here
```

If the Streamlit app uses a **Kibana** base URL for the Agent API, you can also set (optional):

```env
KIBANA_URL=https://your-deployment.kb.region.gcp.cloud.es.io
```

If `KIBANA_URL` is not set, the app will try to derive it from `ELASTICSEARCH_URL` by replacing `.es.` with `.kb.`.

---

## 8. Quick checks

- **Elasticsearch**
  - Dev Tools: `GET legal-knowledge-base/_count` and `GET customer_leads_prod/_count` — both should be > 0.
- **Agent**
  - In Kibana, open the agent and send a test message, e.g. *“What is our policy on emailing minors?”* You should see the policy_retriever used and a cited answer.
- **Streamlit**
  ```bash
  streamlit run app.py
  ```
  Ask: *“Can I email customer_leads_prod?”* You should see tool calls and a denial with risk counts.

---

## 9. Troubleshooting

| Issue | What to check |
|------|----------------|
| Ingest fails: “model not found” | ELSER must be **Started** under ML → Trained Models. |
| Ingest fails: “index already exists” | The script recreates the index; if it still fails, delete `legal-knowledge-base` in Index Management and run again. |
| Agent doesn’t call tools | Ensure tool names are exactly `policy_retriever` and `dataset_inspector` and the index names match. |
| Streamlit: “Error” or no response | Verify `ELASTIC_AGENT_ID`, `ELASTIC_API_KEY`, and (if used) `KIBANA_URL`. Check Kibana/Agent Builder docs for the correct chat/converse API URL. |
| “Unauthorized” / 401 | API key must have Elasticsearch + Kibana permissions; create a new key with broader scope if needed. |

---

## 10. Summary checklist

- [ ] Elastic Cloud deployment is **Healthy** and has **ML**.
- [ ] ELSER v2 is **Started**.
- [ ] API key created and stored in `.env` as `ELASTIC_API_KEY`.
- [ ] `ELASTICSEARCH_URL` (or `ELASTIC_CLOUD_ID`) set in `.env`.
- [ ] `python scripts/ingest_contracts.py` completed successfully.
- [ ] `python scripts/generate_customers.py` and `python scripts/ingest_customers.py` completed successfully.
- [ ] Agent “Governance Guardian” created with system prompt and both tools.
- [ ] `ELASTIC_AGENT_ID` set in `.env`.
- [ ] `streamlit run app.py` and a test query return a cited, tool-using response.

For end-to-end manual test steps, see [MANUAL_TESTING.md](MANUAL_TESTING.md).

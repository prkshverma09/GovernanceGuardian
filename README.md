# Governance Guardian 🛡️

**Governance Guardian** is an AI-powered compliance officer built using the **Elastic Agent Builder**. It acts as a bridge between legal contracts and actual datasets, ensuring that data usage requests are audited against legal policies before execution.

## Features
- 📜 **Semantic Knowledge Retrieval**: Searches through legal PDFs (NDA, MSA, DPA) using **ELSER v2** to find relevant compliance clauses.
- 📊 **Dataset Inspection**: Uses **ES|QL** to perform real-time risk assessment on customer datasets (e.g., identifies minors, restricted regions, or forbidden fields).
- 🛡️ **Automated Decision Making**: Denies or approves data usage requests based on grounded evidence from both policies and the data itself.
- 💬 **Interactive Chat UI**: A Streamlit-based interface for compliance officers to audit and remediate issues.

## Architecture

```mermaid
flowchart TB
    subgraph Users["Users"]
        UI[Streamlit Chat UI]
        IDE[Cursor / Claude Desktop]
    end

    subgraph App["Application Layer"]
        AC[AgentClient]
        RA[Remediation API<br/>Flask]
        MCP[MCP Server<br/>FastMCP]
    end

    subgraph Elastic["Elastic Cloud"]
        AB[Agent Builder<br/>Kibana API]
        subgraph ES["Elasticsearch"]
            LKB[(legal-knowledge-base)]
            CLP[(customer_leads_prod)]
            DAL[(data_access_logs_prod)]
            CLS[(customer_leads_safe)]
        end
    end

    subgraph Tools["Agent Tools"]
        PR[policy_retriever<br/>ELSER v2 / Index Search]
        DI[dataset_inspector<br/>ES|QL]
        LA[log_auditor<br/>ES|QL]
    end

    UI --> AC
    UI -->|"Run remediation now"| RA
    AC --> AB
    IDE --> MCP
    MCP --> AC

    AB --> PR
    AB --> DI
    AB --> LA
    PR --> LKB
    DI --> CLP
    LA --> DAL
    RA --> CLS

    Ingestion[Ingestion Scripts] --> ES
```

**Flow:** The Streamlit UI and MCP server send messages to the **Agent Builder** via the Kibana API. The agent chooses tools: **policy_retriever** (ELSER v2 over `legal-knowledge-base`), **dataset_inspector** (ES|QL on `customer_leads_prod`), **log_auditor** (ES|QL on `data_access_logs_prod`). Clicking **Run remediation now** calls the **Remediation API**, which runs a safe ES|QL query and writes compliant rows to `customer_leads_safe`. Ingestion scripts populate the Elasticsearch indices.

## Tech Stack
- **Elastic Cloud**: Elasticsearch (Serverless), ELSER v2.
- **Elastic Agent Builder**: For persona, instructions, and tools (Semantic Search & ES|QL).
- **Python**: Ingestion scripts, API Client, and Streamlit Frontend.
- **Testing**: Pytest for unit, integration, and E2E compliance journey tests.

## Prerequisites
- Python 3.9+
- An Elastic Cloud project (with ELSER v2 enabled)
- `.env` file populated with credentials (see `.env.example`)

**New to Elastic Cloud?** Follow **[docs/ELASTIC_CLOUD_SETUP.md](docs/ELASTIC_CLOUD_SETUP.md)** for step-by-step setup. You can either run **`python scripts/setup_elastic_api.py`** (API-based setup with `.env` credentials) or complete setup manually in Kibana.

## Installation
1. Clone the repository.
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Setup & Ingestion
1. **Prepare Data**:
   - Sample contract text is in `data/contracts/*.txt`. Optionally add PDFs to `data/contracts/` or run `python scripts/generate_contracts.py` to generate sample PDFs (requires PyMuPDF).
   - Synthetic customer data: run `python scripts/generate_customers.py` to create `data/customers.csv`.
2. **Ingest to Elastic**:
   - Ingest contracts: `python scripts/ingest_contracts.py`
   - Ingest customers: `python scripts/ingest_customers.py`

**One-command setup so all sidebar example queries have data:**  
Run `python scripts/setup_all_data.py` to generate and ingest customer data (`customer_leads_prod`) and access logs (`data_access_logs_prod`). Then run `python scripts/ingest_contracts.py` for the policy index (`legal-knowledge-base`). For the queries *"Have there been any compliance breaches in the last 7 days?"* and *"Audit data access logs for high-volume downloads by region"* to work, add the **log_auditor** ES|QL tool to your agent in Kibana (see `elastic/agent-config.md` §4).

## Running the App
1. Configure the Agent in Elastic Cloud (see `elastic/agent-config.md`).
2. Update `ELASTIC_AGENT_ID` in `.env`.
3. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```

## Testing
Run the full test suite:
```bash
pytest
```
- Integration tests: `pytest -m integration`
- E2E tests: `pytest -m e2e`

For step-by-step manual testing (Streamlit UI, demo flow, troubleshooting), see **[docs/MANUAL_TESTING.md](docs/MANUAL_TESTING.md)**.

## License
MIT (see LICENSE file)

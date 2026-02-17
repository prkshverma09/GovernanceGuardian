# PRD: Governance Guardian (Elastic Hackathon)

| Project Name | Governance Guardian |
| --- | --- |
| **Track** | Automate Messy Internal Work / Narrow Agents (Legal/Compliance) |
| **Team** | *[Your Team Name]* |
| **Status** | Draft / In-Development |
| **Target Date** | February 27, 2026 |

## 1. Executive Summary

**Governance Guardian** is an AI agent built on **Elastic Agent Builder** that acts as an automated "Level 1 Compliance Officer."

Instead of generic chat, it solves a specific, high-friction problem: **verifying if a specific dataset or document is safe to use based on complex regulatory policies.** It combines **Semantic Search** (to understand laws/contracts) with **Structured ES|QL Analysis** (to inspect the actual data) to render a verdict with citations.

### The "Wow" Factor (Why this wins)

* **Beyond Chat:** It doesn't just read text; it queries the *actual database* to verify facts (e.g., "Does this table contain PII?").
* **Citations:** It grounds every answer in specific clauses from uploaded PDF contracts, solving the "trust/hallucination" problem.
* **Technical Sophistication:** Demonstrates Hybrid Search (Vector + Keyword) AND Structured Aggregation (ES|QL) in a single agent workflow.

---

## 2. User Persona & User Stories

**Primary User:** "Sarah," a Data Scientist or Marketing Ops Manager.

* **Pain Point:** Sarah wants to email a list of customers for a new campaign but is afraid of violating GDPR or a specific client contract. Waiting for the Legal team takes 3 days.

**User Stories:**

1. **As a user**, I want to upload a draft contract or policy PDF so the agent knows the rules.
2. **As a user**, I want to ask, "Can I use the 'Marketing_Leads_v2' dataset for email targeting?" and get a clear Yes/No.
3. **As a user**, I want the agent to scan the actual dataset for "forbidden" columns (like `age < 18` or `SSN`) before approving.
4. **As a user**, I want to see *exactly* which contract clause prohibits my action (Citation).

---

## 3. Technical Architecture

### High-Level Flow

`User Query` -> `Elastic Agent` -> `Tool Selection` -> `[Vector Search Tool]` OR `[ES|QL Data Inspector]` -> `Reasoning` -> `Final Answer`

### Tech Stack

* **Core Engine:** Elastic Agent Builder (Serverless or Cloud).
* **LLM Model:** GPT-4o or Claude 3.5 Sonnet (configured via Elastic Connectors).
* **Vector Database:** Elasticsearch with **ELSER** (Elastic Learned Sparse EncodeR) for semantic retrieval.
* **Query Language:** **ES|QL** for structured data analysis.
* **Frontend:** Kibana Agent Chat Interface (Native) OR Simple Streamlit wrapper using Agent API.

---

## 4. Data Strategy & Ingestion

We will use two distinct datasets to demonstrate the "Hybrid" nature of the agent.

### Dataset A: Unstructured "Knowledge Base" (The Rules)

* **Source:** **CUAD (Contract Understanding Atticus Dataset)**.
* *Specifically:* We will use 5-10 PDF contracts from this dataset that contain "Data Privacy" or "Non-Disclosure" clauses.


* **Ingestion Method:**
* Use Kibana's **"Import File"** feature (Machine Learning > Data Visualizer).
* **Chunking:** Split by paragraph.
* **Embedding:** Use the **ELSER** model pipeline to create sparse vector embeddings for each chunk.
* **Index Name:** `legal-knowledge-base`.



### Dataset B: Structured "Company Data" (The Reality)

* **Source:** **Fake Customer Data (Kaggle)**.
* *Content:* A CSV with columns: `Name`, `Email`, `Age`, `Country`, `Subscription_Type`.


* **Ingestion Method:**
* Upload CSV to Elastic.
* **Index Name:** `customer_leads_prod`.
* **Mapping:** Ensure `Age` is an `integer` and `Country` is a `keyword`.



---

## 5. Agent Tools Implementation

This is the most critical part for the "Technical Execution" score. We will build **two custom tools** in Agent Builder.

### Tool 1: `policy_retriever` (Vector Search)

* **Type:** Index Search Tool.
* **Description:** "Searches internal legal contracts and compliance policies to understand what is allowed or prohibited."
* **Configuration:**
* **Index:** `legal-knowledge-base`.
* **Model:** ELSER (Sparse Vector).
* **Parameters:** `query` (string).



### Tool 2: `dataset_inspector` (ES|QL)

* **Type:** ES|QL Tool.
* **Description:** "Inspects a specific dataset to check for PII (Personally Identifiable Information), minors, or restricted regions."
* **ES|QL Query Logic (Dynamic):**
```sql
FROM customer_leads_prod
| WHERE age < 18 OR country == "GDPR_Restricted_Zone"
| STATS count = COUNT(*)
| EVAL is_risky = CASE(count > 0, true, false)
| KEEP count, is_risky

```


*(Note: In the tool definition, we can make the `WHERE` clause parameters dynamic).*

---

## 6. Demo Script (Video Walkthrough)

**Total Time: 3 Minutes**

**0:00 - 0:30: Introduction**

* "Hi, I'm [Name]. Compliance checks kill speed. Developers wait days to know if they can use a dataset. Meet **Governance Guardian**, an Elastic Agent that automates this reasoning."

**0:30 - 1:15: The "Knowledge" Check (RAG)**

* *Action:* In the Agent Chat, type: **"What is our policy on emailing minors according to the 'NDA_Partner_A' contract?"**
* *Visual:* Agent retrieves the specific clause from the PDF using ELSER.
* *Voiceover:* "First, the agent uses ELSER to perform semantic retrieval on our legal knowledge base. It cites the specific document."

**1:15 - 2:00: The "Data" Check (ES|QL)**

* *Action:* User types: **"I want to email the 'customer_leads_prod' list. Is that safe based on the policy you just found?"**
* *Visual:* Agent pauses, shows "Calling Tool: dataset_inspector".
* *Backend Visual (Optional):* Show the ES|QL query running.
* *Result:* Agent replies: **"No. I inspected 'customer_leads_prod' and found 142 records where 'Age < 18'. The policy strictly prohibits marketing to minors."**

**2:00 - 2:45: The Fix & Workflow**

* *Action:* User types: **"Can you filter them out and give me a safe list?"**
* *Visual:* Agent generates a new ES|QL query: `FROM ... | WHERE Age >= 18`.
* *Voiceover:* "The agent doesn't just block me; it uses Elastic's query language to remediate the data in real-time."

**2:45 - 3:00: Conclusion**

* "Governance Guardian turns a 3-day legal review into a 30-second chat, powered by Elastic Agent Builder."

---

## 7. Submission Checklist (Judging Criteria)

* [ ] **Technical Execution:**
* Did we use **ES|QL**? Yes (Tool 2).
* Did we use **Vector Search**? Yes (Tool 1 / ELSER).
* Did we use **Agent Builder**? Yes.


* [ ] **Impact:**
* Does it solve a real problem? Yes (Compliance bottlenecks).


* [ ] **Demo:**
* Is the video clear? (Follow the script above).
* Is the repo public with an OSI license?


* [ ] **Social:**
* [ ] Tweet/Post link added to Devpost.



---

## 8. Setup Instructions (For Developers)

1. **Create Deployment:** Spin up Elastic Cloud (Serverless Test Drive).
2. **Enable ELSER:** Go to Machine Learning > Trained Models > Deploy ELSER v2.
3. **Ingest Data:**
* Upload `contracts.pdf` using the "Data Visualizer" (it handles the PDF-to-Text).
* Upload `customers.csv`.


4. **Configure Agent:**
* Go to **Project Settings > Management > Agents**.
* Create New Agent "Governance Guardian".
* Paste System Prompt: *"You are a strict compliance officer. You must ALWAYS verify rules against the 'legal-knowledge-base' before answering. You must ALWAYS inspect actual data using 'dataset_inspector' before approving any data usage."*


5. **Test:** Run the "Happy Path" (Safe data) and "Sad Path" (Risky data).

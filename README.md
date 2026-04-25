# Agentic RAG System: Financial Intelligence Engine

An advanced, autonomous LLM Agent that performs multi-step financial reasoning by orchestrating structured SQL data, unstructured vector search (RAG), and live web intelligence.

---

## 1. Quick Start & Execution

### 1.1. Create Virtual Environment (Recommended)

```bash
# Create venv
python -m venv venv

# Activate venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 1.2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 1.3. Configuration

Create a `.env` file in the root directory and add your API keys:

```env
GROQ_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

### 1.4. Run the System

```bash
python main.py     # Launch the interactive agent in the terminal
python evaluate.py # Run the automated 20-case evaluation suite
```

---

## 2. Architectural Overview

Unlike standard RAG pipelines, this system implements a **Native ReAct (Reasoning and Acting) loop**. It bypasses rigid wrappers to provide a transparent, high-performance execution layer directly between the LLM and the Python runtime.

**System Flow:**

```text
[ User Query ] ➔ [ Agent Routing Engine ] ⟷ [ LLM Engine ]
                          |
                          | (Tool Routing based on ReAct Logic)
                          |
                          ├──➔ Tool 1: SQLite [Structured Financials]
                          ├──➔ Tool 2: ChromaDB [Unstructured PDFs]
                          └──➔ Tool 3: Tavily API [Live Web Intelligence]
                          |
                          ↓
        [ Synthesized Narrative Response with Citations ]
```

### Core Engine Parameters

- **Dual-Model Strategy (via Groq)**: The system is designed to easily toggle between models based on execution needs:
  - `llama-3.1-8b-instant`: The default engine. Highly optimized for rapid JSON tool-calling and API rate-limit compliance (used to successfully run the rigorous 20-case evaluation suite).
  - `llama-3.3-70b-versatile`: Can be swapped in for single-query, complex reasoning tasks that require maximum parameter intelligence.
- **Reasoning Pattern**: Native Tool-Calling with a strict 8-step safety circuit breaker.
- **Self-Healing**: Implements an automated correction loop that catches API validation/JSON errors and instructs the LLM to re-align its parameters in real-time without crashing.

---

## 3. Tech Stack

- **Structured Data**: `sqlite3` (Deterministic financial metric retrieval via dynamic SQL generation).
- **Unstructured Data**: `chromadb` (Vector Store) for semantic search over PDF annual reports.
- **Live Intelligence**: `tavily-python` for real-time stock prices and sector news.
- **Numerical Integrity**: Custom **Regex Anchoring** to ensure live stock prices are extracted deterministically without LLM hallucination.

---

## 4. Tool Contracts

1. **`query_data`**:
   - **Action**: Executes dynamically generated SQL against the `financials` table.
   - **Guardrail**: System Prompt enforces schema-awareness and cross-entity selection rules.

2. **`search_docs`**:
   - **Action**: Semantic retrieval of qualitative management commentary from PDF documents.
   - **Output**: Returns relevant chunks with precise source and page citations.

3. **`web_search`**:
   - **Action**: Real-time web fetch with query-enhancement logic.
   - **Optimization**: Differentiates between "Price" queries (strict regex extraction) and "Narrative" queries (1,000-character context window).

---

## 5. Evaluation & Robustness

The system includes a rigorous evaluation suite (`evaluate.py`) consisting of 20 complex test cases.

✅ **Final Result**: Achieved a **perfect 20/20 pass rate**, demonstrating high reliability and robustness across structured, unstructured, and real-time query scenarios.

- **Deterministic Validation**: Ensures exact numbers (e.g., EPS, Revenue) match database records.
- **Constraint Testing**: Proves the agent cleanly rejects out-of-domain queries (e.g., general trivia, sports).
- **Resiliency Testing**: Validates the "Self-Healing" loop by simulating malformed JSON inputs and verifying the agent's ability to recover.

---

## 6. Execution Trace Logging

Every response provides a transparent "Thought Trace" to audit the agent's decision-making process:

```text
Question: What was Infosys' operating margin in FY24?
Step 1: tool=query_data input={'sql_query': 'SELECT operating_margin FROM financials WHERE company = "Infosys" AND year = 2024'} result=[{'operating_margin': 20.7}]
Final Answer: Infosys' operating margin for FY24 was 20.7%.
Citations: financials.db
Steps used: 1 / 8 max
```

## 7. Security & Governance

This system is designed with a "Trust but Verify" security posture, implementing several layers of protection against common LLM vulnerabilities.

### 7.1. Prompt Injection & Jailbreak Guardrails

**Domain Isolation**: The system prompt enforces a strict "Financial Domain" boundary. Any attempt to pivot the agent toward non-business topics (e.g., social engineering, unrelated code execution) results in a hard refusal.

**SQL Injection Prevention**: While the agent generates dynamic SQL, the execution layer is constrained to a Read-Only SQLite connection. Destructive commands (DROP, DELETE, UPDATE) are implicitly neutralized by the database's restricted permission set.

### 7.2. Sensitive Data Handling

**Source Anonymity**: The agent is instructed to provide answers based on context without exposing the raw internal file paths or server-side directory structures.

**API Secret Management**: Implementation follows best practices using `python-dotenv`, ensuring that Groq and Tavily credentials never touch the application logs or version control.

---

## 8. Scalability & Performance

The architecture is built to scale horizontally, moving away from the "monolithic script" approach to a modular, tool-based design.

### 8.1. The Semantic Bleed Firewall (Optimization)

**Token Efficiency**: Instead of sending 20+ irrelevant document chunks to the LLM, the Semantic Bleed Firewall intercepts wrong-company data at the Python layer.

**Latency Reduction**: By failing fast and pivoting to `web_search` immediately when a vector mismatch is detected, the system avoids "Hallucination Loops" that would otherwise burn through API credits and time.

### 8.2. Horizontal Tool Expansion

**Pluggable Architecture**: The system uses a Function Registry pattern. New intelligence sources (e.g., a Bloomberg Terminal API, a CRM database, or an SEC EDGAR scraper) can be added by simply defining a new JSON schema and a Python function, without modifying the core ReAct loop.

**Model Agnostic**: The engine is optimized for the Model Context Protocol (MCP) logic, allowing the backend to swap from Llama-3.1-8b to GPT-4o or Claude 3.5 with zero changes to the underlying tool logic.

### 8.3. Vector Store Optimization

**Chunking Strategy**: Documents are processed using a `RecursiveCharacterTextSplitter` with specific overlap, ensuring that financial tables in PDFs aren't cut in half, which maintains semantic density during retrieval.

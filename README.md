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

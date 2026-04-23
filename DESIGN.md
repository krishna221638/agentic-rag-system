# System Design Document: Agentic RAG System

## 1. Architectural Overview

This structured Agentic RAG (Retrieval-Augmented Generation) system is designed for high-accuracy financial data analysis and document retrieval. Built as a custom ReAct (Reasoning and Acting) framework, it leverages native LLM tool-calling capabilities to dynamically route queries. To ensure absolute accuracy in a financial context, the system surrounds the LLM with strict deterministic guardrails, self-healing error correction loops, and circuit breakers, eliminating hallucinations while maintaining the flexibility of an autonomous agent.

## 2. Core Components

### 2.1 Agent Logic Layer

- **Routing Mechanism:** Native JSON Tool Calling (`auto` choice mode)
- **Role:** The LLM dynamically determines which tool to use, the sequence of tools, and the exact parameters (e.g., generating raw SQL or semantic search queries) based on the user's prompt.
- **Execution Loop:** An iterative `while` loop (capped at 8 steps) that executes a standard Agentic flow: *Observe Query -> Select Tool -> Execute Python Function -> Return Observation to LLM -> Synthesize or Call Next Tool.*

### 2.2 Tooling Ecosystem

1. **Structured Data Store (`query_data.py`)**
   - **Backend:** SQLite3 (populated via Pandas from `.csv` files during setup).
   - **Use Case:** Deterministic retrieval of quantitative financial metrics. The LLM is granted schema awareness via the System Prompt and dynamically writes SQL (e.g., `SELECT company, year, operating_margin FROM financials...`) to fetch comparative data.
2. **Unstructured Data Store (`search_docs.py`)**
   - **Backend:** ChromaDB with vector embeddings.
   - **Use Case:** Vector-based semantic search for retrieving qualitative insights (e.g., corporate strategies, reasons for margin improvements).
3. **Live Web Fetch (`web_search.py`)**
   - **Backend:** Tavily API / Live Web Search.
   - **Use Case:** Fetching real-time data beyond the LLM's knowledge cutoff (e.g., live stock prices). Wrapped in intelligent query-enhancement logic to ensure optimal search results.

## 3. Key Design Decisions & Optimizations

- **Self-Healing Error Recovery (`system_correction`):** LLMs occasionally fail at strict JSON generation (e.g., unescaped apostrophes or hallucinated parameter names). Instead of throwing a fatal API error, the Python runtime catches `tool_use_failed` exceptions and injects a `system_correction` prompt. This explicitly instructs the LLM on how to fix its formatting (e.g., "Remove punctuation") and allows the loop to continue gracefully.
- **Infinite Loop Circuit Breakers:** To prevent token-burning "panic loops" where the LLM repeats a failed action, the system tracks the execution trace. If two consecutive `system_correction` errors or redundant `web_search` calls occur, the Python code forcefully halts the loop and instructs the LLM to synthesize what it currently knows.
- **Deterministic Number Anchoring:** When fetching stock prices, a pure-Python RegEx layer intercepts the raw web text *before* the LLM sees it. If a price is found, the system overwrites the tool observation with a strict directive: `"Exact extracted price: ₹X. You MUST use this exact value..."` This prevents the LLM from rounding or guessing numbers.
- **Intelligent Query Detection (`is_price_query`):** The system distinguishes between "Stock Price" queries and "General/Why" queries. It routes price queries through strict regex extractors, but allows qualitative queries to read longer context chunks (up to 1,000 characters), preventing aggressive regex from blocking narrative answers.
- **Strict Context Injection:** The system prompt explicitly defines the database schema (`financials`) and the exact available entities (`Infosys, TCS, Wipro`). This acts as an anti-hallucination shield, preventing the LLM from attempting to query fake tables or invent arbitrary metrics.

## 4. Data Flow (Example: Complex ReAct Loop)

1. **Input:** "What reason did TCS give for its margin improvement in FY24?"
2. **Tool Selection:** The LLM realizes it needs qualitative data and attempts to call `search_docs`.
3. **Self-Healing (Optional):** If the LLM generates invalid JSON (e.g., unescaped apostrophe in "TCS'"), the Python engine intercepts the crash, logs `tool=system_correction`, and asks the LLM to retry without punctuation.
4. **Execution:** The LLM corrects itself, outputs valid JSON (`{"query_string": "TCS margin improvement FY24 reason"}`), and ChromaDB retrieves the most relevant text chunks.
5. **Synthesis:** The LLM analyzes the returned text chunk. If the answer is present, it generates the final narrative. If missing, it uses its built-in conversational awareness to state the data is unavailable rather than fabricating a response.
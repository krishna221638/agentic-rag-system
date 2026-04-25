# System Design Document: Agentic RAG System

## 1. Architectural Overview

This structured Agentic RAG (Retrieval-Augmented Generation) system is designed for high-accuracy financial data analysis. Built as a custom **Native ReAct (Reasoning and Acting) framework**, it leverages native LLM tool-calling capabilities to dynamically route queries.

**Zero Black-Box Philosophy:** To ensure absolute transparency and execution speed, the architecture strictly avoids heavy abstraction frameworks (e.g., LangChain). The core orchestration is handled by a pure Python `while` loop (under 80 lines). To guarantee accuracy in a financial context, the system surrounds the LLM with deterministic guardrails, self-healing error correction loops, and strict circuit breakers, eliminating hallucinations while maintaining the flexibility of an autonomous agent.

---

## 2. Core Components

### 2.1 Agent Logic Layer

- **LLM Engine:** `llama-3.1-8b-instant` (via Groq). Chosen specifically for its low-latency, highly reliable native JSON tool-calling capabilities, ensuring rapid multi-step reasoning without hitting API rate limits.
- **Routing Mechanism:** Native JSON Tool Calling (`auto` choice mode).
- **Role:** The LLM dynamically determines which tool to use, the sequence of tools, and the exact parameters (e.g., generating raw SQL or semantic search queries) based on the user's prompt.
- **Execution Loop:** An iterative `while` loop (capped at a strict 8 steps) that executes a standard Agentic flow: _Observe Query -> Select Tool -> Execute Python Function -> Return Observation to LLM -> Synthesize or Call Next Tool._

### 2.2 Tooling Ecosystem

1. **Structured Data Store (`query_data.py`)**
   - **Backend:** SQLite3 (populated via Pandas from `.csv` files).
   - **Use Case:** Deterministic retrieval of quantitative financial metrics. The LLM is granted schema awareness via the System Prompt and dynamically writes SQL (e.g., `SELECT company, year, operating_margin FROM financials`) to fetch comparative data.
2. **Unstructured Data Store (`search_docs.py`)**
   - **Backend:** ChromaDB with vector embeddings.
   - **Use Case:** Vector-based semantic search for retrieving qualitative insights (e.g., corporate strategies, reasons for margin improvements).
3. **Live Web Fetch (`web_search.py`)**
   - **Backend:** Tavily API / Live Web Search.
   - **Use Case:** Fetching real-time data beyond the LLM's knowledge cutoff (e.g., live stock prices, current executives). Wrapped in intelligent query-enhancement logic to ensure optimal search results.

---

## 3. Key Design Decisions & Optimizations

- **Dual-Model Infrastructure Strategy:** The system is architected to separate routing logic from heavy synthesis. While `llama-3.1-8b` acts as the primary, high-speed routing engine to navigate API rate limits during automated testing, the architecture allows for seamless swapping to `llama-3.3-70b-versatile` for single-query tasks requiring maximum reasoning depth.
- **Self-Healing Error Recovery (`system_correction`):** LLMs occasionally fail at strict JSON generation (e.g., unescaped apostrophes or hallucinated XML tags). Instead of throwing a fatal `400 Bad Request` API error, the Python runtime catches the parse exceptions and injects a `system_correction` prompt. This explicitly instructs the LLM on how to fix its formatting and allows the loop to recover gracefully.
- **Deterministic Number Anchoring:** When fetching stock prices, a pure-Python RegEx layer intercepts the raw web text _before_ the LLM sees it. If a price is found, the system overwrites the tool observation with a strict directive: `"Exact extracted price: ₹X. You MUST use this exact value."` This prevents the LLM from rounding or guessing financial numbers.
- **Infinite Loop Circuit Breakers:** To prevent token-burning "panic loops," the system tracks the execution trace. If multiple consecutive `system_correction` errors or redundant `web_search` calls occur, the Python code forcefully halts the loop and instructs the LLM to synthesize what it currently knows, ensuring a graceful degradation of service.
- **Strict Context Injection:** The system prompt explicitly defines the database schema and valid entities (`Infosys, TCS, Wipro`). This acts as an anti-hallucination shield, preventing the LLM from attempting to query fake tables or invent arbitrary metrics.

---

## 4. Observability & Tracing

A critical requirement for enterprise financial systems is auditability. The engine implements a deterministic tracing system:

- **State Tracking:** Every iteration appends the exact tool name, the generated input parameters, and the truncated system observation to a trace array.
- **Citation Mapping:** Instead of generic sourcing, the system captures exact origins (e.g., specific SQLite tables, exact PDF page numbers, or precise Web URLs) and surfaces them alongside the final answer to guarantee data lineage.

---

## 5. Data Flow (Example: Complex ReAct Loop)

1. **Input:** _"What reason did TCS give for its margin improvement in FY24?"_
2. **Tool Selection:** The LLM realizes it needs qualitative data and attempts to call `search_docs`.
3. **Self-Healing (Edge Case):** If the LLM generates invalid JSON (e.g., unescaped apostrophe in "TCS'"), the Python engine intercepts the crash, logs `tool=system_correction`, and asks the LLM to retry without punctuation.
4. **Execution:** The LLM corrects itself, outputs valid JSON (`{"query_string": "TCS margin improvement FY24 reason"}`), and ChromaDB retrieves the most relevant text chunks.
5. **Synthesis:** The LLM analyzes the returned text chunk and generates the final narrative, successfully citing the specific Annual Report page number.

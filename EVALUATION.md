# System Evaluation & Honest Failure Analysis Report

## 1. Executive Summary

An automated evaluation suite (`evaluate.py`) was executed to rigorously validate the Agentic RAG System across a 20-case matrix. While the final architecture achieved a **100% (20/20) pass rate**, the initial development iterations revealed several critical failure modes related to API infrastructure, LLM formatting limitations, and guardrail tuning.

In accordance with the assignment guidelines, this report details those failures, the specific diagnoses, the engineering fixes implemented, and unexpected observations made during testing.

---

## 2. Honest Failure Analysis & Specific Fixes

### Failure Mode 1: Infrastructure Bottlenecks (API Rate Limits)

- **The Failure:** During the initial run of the 20-question evaluation loop, the system successfully answered the first case but immediately failed the next 17 cases with a `429 Rate Limit Reached` error.
- **Specific Diagnosis:** The agent was initially powered by `llama-3.3-70b-versatile`. While highly capable, the 70B model has restrictive token-per-minute limits on the API tier, which were instantly overwhelmed by the rapid `while` loop execution of the automated test suite.
- **The Fix:** 1. Migrated the core reasoning engine to `llama-3.1-8b-instant`, which is explicitly optimized for rapid tool-calling and has significantly higher API throughput. 2. Implemented a `time.sleep(5)` throttle in the evaluation script to allow the API token bucket to reset between complex multi-tool queries.

### Failure Mode 2: JSON Parsing Crashes (Error 400)

- **The Failure:** The agent frequently failed on queries involving possessive nouns (e.g., _"What was Infosys' operating margin?"_). The system crashed with a `400 Bad Request` API error.
- **Specific Diagnosis:** The LLM was passing unescaped apostrophes directly into the JSON tool arguments (e.g., `{"query_string": "Infosys' margin"}`). This broke the native JSON parser before the Python backend could even execute the tool.
- **The Fix:** Broadened the `try/except` block to specifically catch `400` and `parse` errors. Instead of terminating, the system now intercepts the crash and triggers a **Self-Healing Loop**, feeding a system prompt back to the LLM: _"System Error: Tool call failed due to JSON validation. Remove ALL punctuation... Try again."_ This allowed the agent to self-correct and recover within the 8-step limit.

### Failure Mode 3: Overly Aggressive Domain Guardrails

- **The Failure:** The system correctly rejected questions about swallows and cricket. However, it also rejected valid business queries like _"Who is the CEO of Wipro?"_ (TC-19), refusing to call the web search tool.
- **Specific Diagnosis:** The system prompt's instruction to "reject anything not related to finance or the IT sector" was interpreted too strictly by the LLM, classifying "people/executives" as out-of-domain.
- **The Fix:** Injected a micro-whitelist into the system prompt specifically authorizing the agent to use `web_search` for queries regarding executives (CEOs/CFOs) of the three target companies.

---

## 3. Curiosity: Unexpected Agent Behavior

During the transition to the 8B model, I observed a highly unexpected behavior regarding how smaller LLMs interpret tool-calling instructions:

**The XML Hallucination:** Instead of utilizing the API's native JSON tool-calling array, the LLM would occasionally hallucinate raw XML tags in its standard text output. For example, instead of firing a background tool request, it would output: `<web_search>{"query_string": "IT sector stocks"}</web_search>` directly to the user.

**Why this matters:** It highlighted that smaller models sometimes revert to generalized web-training data (where XML/HTML tags are common) when prompt instructions aren't absolutely rigid.

**The Implementation Result:** To counter this, I added a specific string-detection mechanism in the main reasoning loop. If the agent's content string contains `<function`, `<web_search>`, or `<query_data>`, the system intercepts the message before it reaches the user, flags it as a formatting error, and forces the LLM to rewrite its request using the native JSON schema.

---

## 4. Final Evaluation Matrix Summary

After implementing the self-healing loops and model optimizations, the system successfully cleared all 20 test cases without manual intervention.

| Category                    | Count  | Expected Behavior                                                  | Final Result     |
| :-------------------------- | :----- | :----------------------------------------------------------------- | :--------------- |
| **Single-Tool (SQL)**       | 6      | Accurate routing to SQLite, returning exact values.                | 6/6 Passed       |
| **Single-Tool (RAG)**       | 4      | Accurate routing to ChromaDB, providing cited summaries.           | 4/4 Passed       |
| **Live Web Intelligence**   | 4      | Accurate routing to Tavily, extracting live prices/data.           | 4/4 Passed       |
| **Multi-Tool (Hybrid)**     | 3      | Orchestrating multiple tools sequentially to synthesize an answer. | 3/3 Passed       |
| **Refusals (Domain Check)** | 3      | Rejecting non-financial trivia cleanly with 0 tool calls.          | 3/3 Passed       |
| **TOTAL**                   | **20** | System handles all cases within the 8-step hard cap.               | **20/20 Passed** |

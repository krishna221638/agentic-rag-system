import os
import json
import re
from dotenv import load_dotenv
from groq import Groq

from tools.query_data import query_data
from tools.search_docs import search_docs
from tools.web_search import web_search

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------------- TOOL SCHEMAS ---------------- #
# Enhanced descriptions to strictly guide the LLM's routing behavior.
agent_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "Semantic search over unstructured company documents (Annual Reports, MD&A). Use this to find explanations, reasons, strategic priorities, or risks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_string": {
                        "type": "string",
                        "description": "The search query without special characters. Example: TCS margin improvement reasons FY24"
                    }
                },
                "required": ["query_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_data",
            "description": "Query structured financial database for exact metrics (revenue, margin, profit, headcount, eps).",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {"type": "string"}
                },
                "required": ["sql_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the live web for real-time stock prices, recent news, or current executives.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_string": {"type": "string"}
                },
                "required": ["query_string"],
            },
        },
    }
]

# ---------------- HELPERS ---------------- #

def summarize_text(text):
    text = str(text).replace("\n", " ")
    if len(text) > 1000:
        return text[:1000] + "..."
    return text if text else "No useful information found."


def pick_best_url(urls):
    priority = [
        "moneycontrol.com",
        "screener.in",
        "investing.com",
        "nseindia.com",
        "bseindia.com"
    ]
    for u in urls:
        if any(p in u for p in priority):
            return u
    return urls[0] if urls else "Live Web"


def extract_price(text):
    text = str(text)

    patterns = [
        ("current price", r"(current price|ltp|last)[^\d₹]*₹?\s*([\d,]+\.?\d*)"),
        ("previous close", r"(prev\.?\s*close)[^\d₹]*₹?\s*([\d,]+\.?\d*)"),
        ("open price", r"(open price)[^\d₹]*₹?\s*([\d,]+\.?\d*)"),
        ("price", r"₹\s*([\d,]+\.?\d+)") 
    ]

    for label, pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"₹{match.group(2) if len(match.groups()) > 1 else match.group(1)}", label

    return None, None


# ---------------- MAIN AGENT ---------------- #

def run_agent(question: str):
    trace = []
    citations = set()
    step_count = 0
    max_steps = 8
    
    web_search_used = False 

    messages = [
        {
            "role": "system",
            "content": (
                "You are an elite Financial AI Intelligence Engine.\n"
                "DATABASE CONTEXT:\n"
                "- The SQL table is strictly named 'financials'.\n"
                "- Available columns: company, year, revenue, operating_margin, net_profit, eps, headcount.\n"
                "- Valid companies: 'Infosys', 'TCS', and 'Wipro'.\n\n"
                "STRICT RULES:\n"
                "1. OUT-OF-DOMAIN GUARDRAIL: Refuse questions completely unrelated to finance, business, or the 3 allowed companies. HOWEVER, questions about executives (e.g., CEO, CFO) of Infosys, TCS, or Wipro ARE valid and you MUST use web_search to find them.\n"
                "2. When a tool returns a deterministically extracted numeric value, you MUST output that exact value in your final answer.\n"
                "3. Use only ONE web_search call per question. Do NOT search the web multiple times.\n"
                "4. When writing SQL queries, ALWAYS select the 'company' and 'year' columns alongside your metric.\n"
                "5. STRICT SCHEMA: ONLY use the exact parameter names ('query_string' or 'sql_query'). NEVER invent extra parameters.\n"
                "6. NEVER output raw XML/HTML tags like <web_search> or <query_data> in your response. Use the native tool calling API.\n"
                "7. Remove apostrophes and special characters from your tool arguments to prevent JSON parsing errors."
            )
        },
        {"role": "user", "content": question}
    ]

    while step_count < max_steps:
        step_count += 1

        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",  
                messages=messages,
                tools=agent_tools,
                tool_choice="auto",
                temperature=0.0
            )

            msg = response.choices[0].message
            tool_calls = msg.tool_calls

            # ---------------- FINAL ANSWER ---------------- #
            if not tool_calls:
                content_text = msg.content or ""
                
                # Catch ANY hallucinated XML tags from the LLM
                if any(tag in content_text for tag in ["<function", "<web_search", "<query_data", "<search_docs", "<tool"]):
                    messages.append({"role": "user", "content": "System Error: You outputted raw text tags. You MUST use the native JSON tool calling API."})
                    
                    trace.append({
                        "tool": "system_correction",
                        "input": "LLM outputted raw text tags instead of JSON.",
                        "result": "Triggered self-healing retry to fix formatting."
                    })
                    continue

                return {
                    "answer": content_text,
                    "trace": trace,
                    "citations": list(citations),
                    "steps": len(trace) if len(trace) > 0 else 1
                }

            messages.append(msg)

            for tool_call in tool_calls:
                fname = tool_call.function.name

                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except:
                    args = {}

                result = ""

                # ---------------- SQL ---------------- #
                if fname == "query_data":
                    result = query_data(args.get("sql_query", ""))
                    citations.add("financials.db")

                # ---------------- DOC SEARCH ---------------- #
                elif fname == "search_docs":
                    result = search_docs(args.get("query_string", ""))
                    sources = re.findall(r"from (.*? p\. \d+)", str(result))
                    for s in sources:
                        citations.add(s)
                    if not sources:
                        citations.add("PDF documents")

                # ---------------- WEB SEARCH ---------------- #
                elif fname == "web_search":
                    if web_search_used:
                        result = "System Error: You have already used web_search for this query. You are forbidden from searching again. Synthesize your final answer using the information you already have."
                    else:
                        web_search_used = True
                        query = args.get("query_string", "")

                        is_price_query = any(word in query.lower() for word in ["price", "stock", "ltp", "share"])

                        if is_price_query:
                            if "moneycontrol" not in query.lower() and "nse" not in query.lower():
                                query += " current share price NSE moneycontrol"
                        elif not any(k in query.lower() for k in ["nse", "bse", "inr"]):
                            query += " NSE INR"

                        raw = web_search(query)
                        text = str(raw)

                        urls = re.findall(r"\((https?://[^\)]+)\)", text)
                        best_url = pick_best_url(urls)
                        citations.add(best_url)

                        if is_price_query:
                            price, label = extract_price(text)
                            if price:
                                if label == "current price":
                                    result = f"Exact extracted price: {price}. You MUST use this exact value in your final answer."
                                else:
                                    result = f"Exact extracted price: {price} ({label}). You MUST use this exact value in your final answer."
                            else:
                                result = summarize_text(text)
                        else:
                            result = summarize_text(text)

                else:
                    result = "Unknown tool"

                trace.append({
                    "tool": fname,
                    "input": str(args),
                    "result": str(result)[:200]
                })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fname,
                    "content": str(result)
                })

        except Exception as e:
            error_str = str(e).lower()
            
            # 🚀 CIRCUIT BREAKER: Prevents infinite API crash loops
            if len(trace) >= 2 and trace[-1]["tool"] == "system_correction" and trace[-2]["tool"] == "system_correction":
                return {
                    "answer": "System encountered a repeated API validation error while calling tools. Please rephrase your question.",
                    "trace": trace,
                    "citations": list(citations),
                    "steps": len(trace)
                }

            # Broadened exception catching to catch Groq 400 Bad Request JSON errors and 429 Rate Limits
            if "400" in error_str or "tool" in error_str or "validation" in error_str or "json" in error_str or "parse" in error_str:
                # 🚀 ULTIMATE RECOVERY PROMPT
                messages.append({
                    "role": "user",
                    "content": "System Error: Tool call failed due to JSON validation. Remove ALL punctuation (like apostrophes) from your arguments and ensure you ONLY use the exact parameter names defined in the schema. Try again."
                })
                
                trace.append({
                    "tool": "system_correction",
                    "input": "API Schema Validation or JSON Parsing Error.",
                    "result": "Triggered self-healing retry to fix parameters and remove punctuation."
                })
                continue 
            elif "429" in error_str or "rate limit" in error_str:
                return {
                    "answer": "System Error: API Rate Limit Reached. Please wait a moment and try again.",
                    "trace": trace,
                    "citations": list(citations),
                    "steps": len(trace)
                }
            else:
                return {
                    "answer": f"Agent encountered an execution error: {error_str}",
                    "trace": trace,
                    "citations": list(citations),
                    "steps": len(trace)
                }

    return {
        "answer": "I am unable to answer this question as it requires too many steps or I am stuck in a loop. I must stop here.",
        "trace": trace,
        "citations": list(citations),
        "steps": len(trace)
    } 
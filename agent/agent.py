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

agent_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "Search company documents for explanations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_string": {"type": "string"}
                },
                "required": ["query_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_data",
            "description": "Query structured financial data.",
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
            "description": "Search the web for real-time data.",
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
    # Expanded to 1000 characters so the LLM can read the actual reasons/explanations
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
                "You are an AI agent.\n"
                "DATABASE CONTEXT:\n"
                "- The SQL database table is strictly named 'financials'. Do NOT query any other table name.\n"
                "- Available columns in 'financials': company, year, revenue, operating_margin, net_profit, eps, headcount.\n"
                "- The only companies available in the database are 'Infosys', 'TCS', and 'Wipro'. If a user asks about 'all 3 companies', they mean these exact three.\n\n"
                "Rules:\n"
                "1. Use tools sequentially if multiple are needed.\n"
                "2. When a tool returns a deterministically extracted numeric value, you MUST output that exact value in your final answer. Do not modify or guess numbers.\n"
                "3. Use only ONE web_search call per question. Do NOT search the web multiple times.\n"
                "4. Return clean, direct answers and explicitly cite the provided URLs or sources.\n"
                "5. ALWAYS use the native tool JSON format. NEVER output raw tags like <function>.\n"
                "6. When writing SQL queries for multiple companies or years, ALWAYS select the 'company' and 'year' columns alongside your metric so you can correctly identify the data.\n"
                "7. STRICT SCHEMA RULE: When calling tools, ONLY use the exact parameter names defined in the schema ('query_string' or 'sql_query'). Never invent parameters."
            )
        },
        {"role": "user", "content": question}
    ]

    while step_count < max_steps:
        step_count += 1

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
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
                if "<function" in content_text:
                    messages.append({"role": "user", "content": "Error: Use native tool calling API, not text tags."})
                    
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
            error_str = str(e)
            
            # 🚀 CIRCUIT BREAKER: Prevents infinite API crash loops
            if len(trace) >= 2 and trace[-1]["tool"] == "system_correction" and trace[-2]["tool"] == "system_correction":
                return {
                    "answer": "System encountered a repeated API validation error while calling tools. Please rephrase your question.",
                    "trace": trace,
                    "citations": list(citations),
                    "steps": len(trace)
                }

            if "tool_use_failed" in error_str or "failed_generation" in error_str or "validation" in error_str.lower():
                # 🚀 ULTIMATE RECOVERY PROMPT: Fixes both parameter names AND punctuation crashes
                messages.append({
                    "role": "user",
                    "content": "System Error: Tool call failed. 1) Use EXACT parameter names like 'query_string'. 2) Remove ALL punctuation (like apostrophes in TCS's) from your arguments to prevent JSON escaping errors. Try again with simple keywords."
                })
                
                trace.append({
                    "tool": "system_correction",
                    "input": "API Schema Validation or JSON Error.",
                    "result": "Triggered self-healing retry to fix parameters and remove punctuation."
                })
                continue 
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
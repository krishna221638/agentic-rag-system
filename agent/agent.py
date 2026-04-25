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
            "description": "Semantic search over unstructured documents. Use this ONLY when the user asks for 'reasons', 'explanations', 'how', or 'why' something happened (e.g., 'why did margins improve?').",
            "parameters": {
                "type": "object",
                "properties": {
                    "reasoning": {
                        "type": "string",
                        "description": "Explain briefly WHY you chose this tool and what you hope to find."
                    },
                    "query_string": {
                        "type": "string",
                        "description": "The search query without special characters. Example: TCS margin improvement reasons FY24"
                    }
                },
                "required": ["reasoning", "query_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_data",
            "description": "Query structured database ONLY for exact numerical metrics (revenue, margin, profit). DO NOT use this if the user is asking for 'reasons' or 'explanations'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reasoning": {
                        "type": "string",
                        "description": "Explain briefly WHY you are querying the database for these specific metrics."
                    },
                    "sql_query": {"type": "string"}
                },
                "required": ["reasoning", "sql_query"],
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
                    "reasoning": {
                        "type": "string",
                        "description": "Explain briefly WHY you are searching the live web."
                    },
                    "query_string": {"type": "string"}
                },
                "required": ["reasoning", "query_string"],
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
    priority = ["moneycontrol.com", "screener.in", "investing.com", "nseindia.com", "bseindia.com"]
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
                "5. NEVER output raw XML/HTML tags like <web_search> or <query_data> in your response. Use the native tool calling API.\n"
                "6. Remove apostrophes and special characters from your tool arguments to prevent JSON parsing errors.\n"
                "7. BE CONCISE: NEVER repeat the same sentence multiple times in your final answer. If you lack information, simply state it once cleanly.\n"
                "8. PIVOT STRATEGY: If you receive a 'System Guardrail' error telling you to stop using a tool, you MUST immediately pivot to a DIFFERENT tool (e.g., switch from search_docs to web_search).\n"
                "9. BULK DATA & MATH: If the user asks for trends, growth, or data over multiple years (e.g., 'last 4 years'), fetch ALL data in a SINGLE SQL query. DO NOT query the database year-by-year. Once the tool returns the bulk data, calculate the differences yourself and synthesize the final answer immediately."
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
                temperature=0.1,
                max_tokens=400
            )

            msg = response.choices[0].message
            tool_calls = msg.tool_calls

            # ---------------- FINAL ANSWER ---------------- #
            if not tool_calls:
                content_text = msg.content or ""
                
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

            # 🚀 STRICT RE-ACT ENFORCEMENT: Process exactly ONE tool call per step
            if len(tool_calls) > 1:
                tool_calls = tool_calls[:1]

            for tool_call in tool_calls:
                fname = tool_call.function.name

                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except:
                    args = {}

                agent_thought = args.get("reasoning", "No explicit reasoning provided.")
                
                # 🚀 TWO-STRIKE BAILOUT: If the agent triggers Anti-Loop twice, gracefully exit early.
                anti_loop_count = sum(1 for t in trace if "Anti-Loop" in t.get("tool", ""))
                if anti_loop_count >= 2:
                    return {
                        "answer": "I have thoroughly searched the available documents but cannot find the specific information required to answer this question.",
                        "trace": trace,
                        "citations": list(citations),
                        "steps": len(trace)
                    }

                # 🚀 ANTI-REPETITION GUARDRAIL 🚀
                current_action_signature = f"{fname}-{args.get('query_string', args.get('sql_query', ''))}"
                
                if len(trace) > 0:
                    last_trace = trace[-1]
                    last_action_signature = last_trace.get('raw_input', '') 
                    
                    if current_action_signature == last_action_signature and fname != "system_correction":
                        error_msg = f"System Guardrail: You just tried searching '{args.get('query_string', args.get('sql_query', ''))}' and it failed or looped. Do NOT repeat the exact same query. Change your keywords or synthesize an answer."
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": fname,
                            "content": error_msg
                        })
                        
                        trace.append({
                            "tool": "system_correction (Anti-Loop)",
                            "thought": "System intercepted duplicate action.",
                            "input": "Duplicate tool call detected.",
                            "result": "Intercepted infinite loop. Forced LLM to change strategy.",
                            "raw_input": current_action_signature
                        })
                        continue

                result = ""

                # ---------------- EXECUTE TOOLS ---------------- #
                if fname == "query_data":
                    result = query_data(args.get("sql_query", ""))
                    citations.add("financials.db")

                elif fname == "search_docs":
                    query_string = args.get("query_string", "")
                    raw_result = search_docs(query_string)
                    result = str(raw_result)
                    
                    # 🚀 THE SEMANTIC BLEED FIREWALL (Tool Pivot Logic) 🚀
                    q_lower = query_string.lower()
                    r_lower = result.lower()
                    
                    if ("tcs" in q_lower or "tata" in q_lower) and "wipro.pdf" in r_lower:
                        result = "System Guardrail: The local vector database is suffering from Semantic Bleed and returning Wipro documents instead of TCS. Do NOT use search_docs again. Pivot your strategy and use web_search to find the answer."
                    
                    # 🚀 UPDATED INFOSYS & WIPRO GUARDRAILS 🚀
                    elif ("infosys" in q_lower) and ("wipro.pdf" in r_lower or "tcs.pdf" in r_lower):
                        result = "System Guardrail: Semantic Bleed detected. The database got confused by generic terms. Retry search_docs ONE MORE TIME using ONLY the company name and core topic (e.g., 'Infosys strategic priorities'). Remove words like 'MD&A' or 'FY24'. If it fails again, then pivot to web_search."
                    elif ("wipro" in q_lower) and ("infosys.pdf" in r_lower or "tcs.pdf" in r_lower):
                        result = "System Guardrail: Semantic Bleed detected. The database got confused by generic terms. Retry search_docs ONE MORE TIME using ONLY the company name and core topic (e.g., 'Wipro strategic priorities'). Remove words like 'MD&A' or 'FY24'. If it fails again, then pivot to web_search."
                    
                    else:
                        sources = re.findall(r"from (.*? p\. \d+)", result)
                        for s in sources:
                            citations.add(s)
                        if not sources:
                            citations.add("PDF documents")

                elif fname == "web_search":
                    if web_search_used:
                        # 🚀 UPDATED WEB SEARCH GUARDRAIL 🚀
                        result = "System Guardrail: You have already used web_search. Look at your previous tool results—you already have the data. Synthesize your final answer immediately."
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
                                # 🚀 THE STOP COMMAND 🚀
                                result = f"ACTION SUCCESSFUL. The exact extracted price is {price}. DO NOT call any more tools. Synthesize your final answer immediately using this exact number."
                            else:
                                result = summarize_text(text)
                        else:
                            result = summarize_text(text)
                else:
                    result = "Unknown tool"

                trace.append({
                    "tool": fname,
                    "thought": agent_thought,
                    "input": str(args),
                    "result": str(result)[:200],
                    "raw_input": current_action_signature
                })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fname,
                    "content": str(result)
                })

        except Exception as e:
            error_str = str(e).lower()
            
            if "400" in error_str or "tool" in error_str or "validation" in error_str or "json" in error_str or "parse" in error_str:
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
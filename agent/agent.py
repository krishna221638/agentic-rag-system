import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

from tools.query_data import query_data
from tools.search_docs import search_docs
from tools.web_search import web_search

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MAX_TOOL_CALLS = 8

tools_def = [
    {
        "name": "search_docs",
        "description": "Semantic search over unstructured documents. Use this to find explanations, management commentary, or qualitative information from PDFs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_string": {
                    "type": "string",
                    "description": "Natural language query string to search documents."
                }
            },
            "required": ["query_string"]
        }
    },
    {
        "name": "query_data",
        "description": "Query the structured financial / stats table. Use this for exact numbers, historical data, or metrics. Table is 'financials' with columns: company, year, revenue, operating_margin, net_profit, eps, headcount.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "A valid SQL query string (e.g., SELECT revenue FROM financials WHERE company='TCS' AND year=2024)"
                }
            },
            "required": ["sql_query"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the live web for recent information. Use this if the knowledge limit is reached or real-time news is requested.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_string": {
                    "type": "string",
                    "description": "A short search query string (under 10 words)."
                }
            },
            "required": ["query_string"]
        }
    }
]

def run_agent(question: str) -> dict:
    """
    Main agent loop using Anthropic function calling limit to exactly 8 steps.
    Returns structured log as trace.
    """
    system_prompt = "You are an intelligent data agent. Answer questions using the provided tools. You must cite the tool name and exact source (e.g., filename, table row, webpage) in your final answer when combining facts. If you truly cannot answer the question after trying, admit you cannot help instead of guessing."
    
    messages = [
        {"role": "user", "content": question}
    ]
    
    trace_steps = []
    citations = set()
    step_count = 0
    
    while step_count < MAX_TOOL_CALLS:
        try:
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
                tools=tools_def
            )
        except Exception as e:
            return {
                "answer": f"API Error: {str(e)}",
                "trace": trace_steps,
                "citations": list(citations),
                "steps": step_count
            }
            
        messages.append({"role": "assistant", "content": response.content})
        
        if response.stop_reason != "tool_use":
            final_text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
            return {
                "answer": final_text or "No answer provided.",
                "trace": trace_steps,
                "citations": list(citations),
                "steps": step_count
            }
            
        tool_results = []
        for block in response.content:
            if getattr(block, "type", "") == "tool_use":
                name = block.name
                args = block.input
                tool_use_id = block.id
                
                step_record = {"tool": name, "input": str(args)}
                citations.add(name)
                
                try:
                    if name == "search_docs":
                        result = search_docs(args.get("query_string", ""))
                    elif name == "query_data":
                        result = query_data(args.get("sql_query", ""))
                    elif name == "web_search":
                        result = web_search(args.get("query_string", ""))
                    else:
                        result = f"Error: Tool {name} not found."
                except Exception as e:
                    result = f"Execution error: {str(e)}"
                    
                step_record["result"] = str(result)[:300] + "..." if len(str(result)) > 300 else str(result)
                trace_steps.append(step_record)
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": str(result)
                })
        
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
            
        step_count += 1
        
    return {
        "answer": "Refusal: Reached maximum 8 tool call steps without finding a complete answer. I cannot complete this request.",
        "trace": trace_steps,
        "citations": list(citations),
        "steps": step_count
    }
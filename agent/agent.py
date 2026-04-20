import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools.query_data import query_data
from tools.search_docs import search_docs
from tools.web_search import web_search

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MAX_TOOL_CALLS = 8

# Using standard Python functions as the tool schemas for Gemini:
def search_docs_tool(query_string: str) -> str:
    """Semantic search over unstructured documents. Use this to find explanations, management commentary, or qualitative information from PDFs."""
    return str(search_docs(query_string))

def query_data_tool(sql_query: str) -> str:
    """Query the structured financial / stats table. Use this for exact numbers, historical data, or metrics. Table is 'financials' with columns: company, year, revenue, operating_margin, net_profit, eps, headcount."""
    return str(query_data(sql_query))

def web_search_tool(query_string: str) -> str:
    """Search the live web for recent information. Use this if the knowledge limit is reached or real-time news is requested."""
    return str(web_search(query_string))

tools_def = [search_docs_tool, query_data_tool, web_search_tool]

def run_agent(question: str) -> dict:
    """
    Main agent loop using Gemini function calling limit to exactly 8 steps.
    Returns structured log as trace.
    """
    try:
        chat = client.chats.create(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                tools=tools_def,
                temperature=0.0,
                system_instruction="You are an intelligent data agent. You MUST ALWAYS use the provided tools to retrieve facts before answering (never use your internal knowledge). You must cite the tool name and exact source (e.g., filename, table row, webpage) in your final answer when combining facts. If you truly cannot answer the question after trying, admit you cannot help instead of guessing."
            )
        )
    except Exception as e:
        return {"answer": f"Initialization Error: {str(e)}\n\nDid you forget to set GEMINI_API_KEY?", "trace": [], "citations": [], "steps": 0}
        
    trace_steps = []
    citations = set()
    step_count = 0
    
    try:
        response = chat.send_message(question)
    except Exception as e:
        return {"answer": f"API Error: {str(e)}", "trace": trace_steps, "citations": list(citations), "steps": step_count}

    while step_count < MAX_TOOL_CALLS:
        if not response.function_calls:
             break
        
        tool_responses = []

        for fn_call in response.function_calls:
            name = fn_call.name
            args = fn_call.args
            
            # Standardize name for tracing
            clean_name = name.replace("_tool", "")
            step_record = {"tool": clean_name, "input": str(args)}
            
            if clean_name == "query_data":
                citations.add("financials.csv (query_data)")
            elif clean_name == "search_docs":
                citations.add("PDF Docs (search_docs)")
            elif clean_name == "web_search":
                citations.add("Live Web (web_search)")
            else:
                citations.add(f"{clean_name} (unknown source)")
            
            try:
                if name == "search_docs_tool":
                    result = search_docs_tool(args.get("query_string", ""))
                elif name == "query_data_tool":
                    result = query_data_tool(args.get("sql_query", ""))
                elif name == "web_search_tool":
                    result = web_search_tool(args.get("query_string", ""))
                else:
                    result = f"Error: Tool {name} not found."
            except Exception as e:
                result = f"Execution error: {str(e)}"
                
            step_record["result"] = str(result)[:300] + "..." if len(str(result)) > 300 else str(result)
            trace_steps.append(step_record)

            # Properly construct the response in the new SDK
            tool_responses.append(
                types.Part.from_function_response(
                    name=name,
                    response={"result": result}
                )
            )

        if not tool_responses:
            return {
                "answer": response.text or "No answer provided.",
                "trace": trace_steps,
                "citations": list(citations),
                "steps": max(1, step_count)
            }

        step_count += 1
        try:
            response = chat.send_message(tool_responses)
        except Exception as e:
            return {
                "answer": f"API Error during tool execution reporting: {str(e)}",
                "trace": trace_steps,
                "citations": list(citations),
                "steps": step_count
            }
        
        # If response returned text alongside function calls, capture it
        if response.text and not response.function_calls:
             return {
                "answer": response.text,
                "trace": trace_steps,
                "citations": list(citations),
                "steps": step_count
             }
    
    return {
        "answer": response.text if response.text else "Refusal: Reached maximum 8 tool call steps without finding a complete answer.",
        "trace": trace_steps,
        "citations": list(citations),
        "steps": step_count
    }
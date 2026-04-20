import os
import json
from dotenv import load_dotenv
from groq import Groq

from tools.query_data import query_data
from tools.search_docs import search_docs
from tools.web_search import web_search

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ---------------- EXTRACT VALUE FROM SQL RESULT ---------------- #

def extract_value(result):
    try:
        if isinstance(result, str):
            result = json.loads(result)

        if "data" in result and len(result["data"]) > 0:
            row = result["data"][0]
            return list(row.values())[0]

        return result
    except:
        return result


# ---------------- NL → SQL ---------------- #

def nl_to_sql(question: str) -> str:
    q = question.lower()

    company = None
    if "tcs" in q:
        company = "TCS"
    elif "infosys" in q:
        company = "Infosys"
    elif "wipro" in q:
        company = "Wipro"

    year = None
    for y in ["2021", "2022", "2023", "2024"]:
        if y in q:
            year = y

    if "revenue" in q:
        column = "revenue"
    elif "profit" in q:
        column = "net_profit"
    elif "margin" in q:
        column = "operating_margin"
    elif "eps" in q:
        column = "eps"
    elif "headcount" in q:
        column = "headcount"
    else:
        column = "*"

    return f"SELECT {column} FROM financials WHERE company='{company}' AND year={year};"


# ---------------- TOOL DECISION ---------------- #

def decide_tool(question: str):
    q = question.lower()

    if any(k in q for k in ["revenue", "profit", "eps", "margin", "headcount"]):
        return "query_data"

    if any(k in q for k in ["why", "explain", "strategy", "initiative"]):
        return "search_docs"

    if any(k in q for k in ["stock", "latest", "news", "today"]):
        return "web_search"

    return "query_data"


# ---------------- MAIN AGENT ---------------- #

def run_agent(question: str) -> dict:
    trace_steps = []
    citations = set()
    step_count = 0

    tool = decide_tool(question)

    try:
        if tool == "query_data":
            sql_query = nl_to_sql(question)
            raw_result = query_data(sql_query)
            value = extract_value(raw_result)

            citations.add("financials.csv (query_data)")

            # ✅ Clean natural answer
            answer = f"The revenue of TCS in 2024 is {value}."

        elif tool == "search_docs":
            value = search_docs(question)
            citations.add("PDF documents (search_docs)")
            answer = value

        elif tool == "web_search":
            value = web_search(question)
            citations.add("web results (web_search)")
            answer = value

        else:
            answer = "Unable to process query."

        step_count = 1

        trace_steps.append({
            "tool": tool,
            "input": question,
            "result": str(value)
        })

    except Exception as e:
        return {
            "answer": f"Execution Error: {str(e)}",
            "trace": trace_steps,
            "citations": list(citations),
            "steps": step_count
        }

    return {
        "answer": answer,
        "trace": trace_steps,
        "citations": list(citations),
        "steps": step_count
    }
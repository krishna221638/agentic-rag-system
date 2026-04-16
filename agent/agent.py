from tools.query_data import query_data
from tools.search_docs import search_docs
from tools.web_search import web_search

MAX_TOOL_CALLS = 5

def decide_tool(question):
    """
    Decide which tool to use based on the user's question.
    """
    question = question.lower()
    if any(keyword in question for keyword in ["revenue", "profit", "margin", "eps", "headcount"]):
        return "query_data"
    elif any(keyword in question for keyword in ["why", "explain", "strategy", "mission", "vision"]):
        return "search_docs"
    elif any(keyword in question for keyword in ["stock", "latest", "news", "current price"]):
        return "web_search"
    else:
        return None

def run_agent(question):
    """
    Main agent loop to process a user question.
    """
    tool_calls = 0
    while tool_calls < MAX_TOOL_CALLS:
        tool = decide_tool(question)
        
        if tool == "query_data":
            # This is a simplified logic. A real agent would need to construct a SQL query.
            # For now, we'll use a placeholder query based on keywords.
            company = None
            if "tcs" in question.lower():
                company = "TCS"
            elif "infosys" in question.lower():
                company = "Infosys"
            elif "wipro" in question.lower():
                company = "Wipro"
            
            if company:
                sql_query = f"SELECT * FROM financials WHERE company = '{company}'"
                result = query_data(sql_query)
                return {"answer": result, "source": "financials.csv"}
            else:
                return {"answer": "Could not determine the company from the question.", "source": "agent"}

        elif tool == "search_docs":
            # Simplified: using the whole question as a keyword
            result = search_docs(question)
            return {"answer": result, "source": "PDF documents"}

        elif tool == "web_search":
            result = web_search(question)
            return {"answer": result, "source": "Web Search"}
            
        else:
            return {"answer": "I am not sure how to answer that. Please try rephrasing your question.", "source": "agent"}
        
        tool_calls += 1
    
    return {"answer": "Reached maximum tool calls. Unable to provide a definitive answer.", "source": "agent"}

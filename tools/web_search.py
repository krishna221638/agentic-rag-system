import os
from dotenv import load_dotenv
# from tavily import TavilyClient

load_dotenv()

# tavily_api_key = os.getenv("TAVILY_API_KEY")
# tavily = TavilyClient(api_key=tavily_api_key)

def web_search(query):
    """
    Perform a web search using Tavily API.
    For now, it returns a dummy response.
    """
    # response = tavily.search(query=query, search_depth="basic")
    # return response['results']
    return {
        "query": query,
        "response": "This is a dummy response for web search. Replace with actual Tavily API call."
    }

if __name__ == '__main__':
    # Example usage
    print(web_search("latest news on TCS stock"))

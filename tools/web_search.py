import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

def web_search(query_string: str) -> str:
    """
    Search the live web for recent information using a short query string.
    Args:
        query_string: A short search query string (under 10 words).
    Returns:
        Top-3 result snippets with URL and publication date.
    """
    try:
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            return "Error: TAVILY_API_KEY not found in environment."
            
        tavily = TavilyClient(api_key=tavily_api_key)
        response = tavily.search(query=query_string, max_results=3, search_depth="basic")
        
        output = ""
        for i, res in enumerate(response.get('results', [])):
            snippet = res.get('content', '')
            url = res.get('url', '')
            date = res.get('published_date', 'Unknown date')
            output += f"Result {i+1} [Date: {date}] ({url}): {snippet}\n"
            
        return output if output else "No results found."
    except Exception as e:
        return f"Error executing web search: {str(e)}"

if __name__ == '__main__':
    # Example usage
    print(web_search("latest news on TCS stock"))
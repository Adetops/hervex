# web_search.py - HERVEX's first real tool
# It wraps Tavily search API - which returns actual search content summaries

from tavily import TavilyClient
from app.core.config import settings


# Initialize Tavily api key from settings using TavilyClient
# to handle authentication and request formatting
_client = TavilyClient(api_key=settings.TAVILY_API_KEY)


async def web_search(query: str, max_results: int = 5) -> str:
    """
    Performs a real web search using the Tavily API and returns
    a clean, formatted string of results ready for LLM consumption
    
    Tavily is purpose built for AI agents. It returns summarized content
    rather than raw HTML, making results immediately usable without additional parsing.
    
    Args:
        query: The search query string extracted from task description
        max_results: Maximum number of results to return (default: 5)
        
    Returns:
        A formatted string containing titles, URLs, content summary for each task result.
    
    Raises:
        Exception: If the Tavily API call fails
    """
    
    # search_depth "basic" is fast and sufficient for most agent tasks
    # "advanced" gives deeper results but uses more API credits
    response = _client.search(
        query=query,
        searc_depth="basic",
        max_results=max_results
    )
    
    # Tavily returns a dict with a 'results' list
    # Each result has: title, url, content (summary), and score
    results = response.get("results", [])
    
    if not results:
        return (f"No results found for query: {query}")
    
    # Format result into a clean readable string
    # This format is optimized for LLM consumption in the aggregator
    formatted = []
    for i, result in enumerate(results, 1):
        formatted.append(
            f"Result: {i}\n"
            f"Title: {result.get('title', 'No title')}\n"
            f"URL: {result.get('url', 'No URL')}\n"
            f"Summary: {result.get('content', 'No content')}\n"
        )
    
    return "\n".join(formatted)

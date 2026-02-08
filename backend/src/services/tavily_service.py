"""Tavily search service wrapper."""

from typing import Dict, Any, List, Optional
import os

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

from src.config import settings


class TavilyService:
    """Service wrapper for Tavily search API."""
    
    def __init__(self):
        if TavilyClient is None:
            raise ImportError("tavily-python is required. Install with: pip install tavily-python")
        
        api_key = settings.tavily_api_key or os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY is required")
        
        self.client = TavilyClient(api_key=api_key)
        self.max_results = settings.max_search_results
    
    def search(
        self,
        query: str,
        search_depth: str = "advanced",
        max_results: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a search query.
        
        Args:
            query: Search query string
            search_depth: "basic" or "advanced"
            max_results: Maximum number of results to return
            
        Returns:
            Tavily search results dictionary
        """
        return self.client.search(
            query=query,
            search_depth=search_depth,
            max_results=max_results or self.max_results
        )
    
    def search_multiple(
        self,
        queries: List[str],
        search_depth: str = "advanced",
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Execute multiple search queries.
        
        Args:
            queries: List of search query strings
            search_depth: "basic" or "advanced"
            max_results: Maximum results per query
            
        Returns:
            List of search results
        """
        results = []
        for query in queries:
            try:
                result = self.search(query, search_depth, max_results)
                results.append({"query": query, "results": result})
            except Exception as e:
                results.append({"query": query, "error": str(e), "results": None})
        return results
    
    def get_context(self, query: str) -> str:
        """Get search context optimized for LLMs.
        
        Args:
            query: Search query string
            
        Returns:
            Compiled context string from search results
        """
        results = self.search(query)
        
        context_parts = []
        for result in results.get("results", [])[:5]:
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")
            
            if title and content:
                context_parts.append(f"## {title}\n{content}\nSource: {url}\n")
        
        return "\n".join(context_parts)

from typing import List, Optional
from pydantic import BaseModel, Field

from serpapi.google_search import GoogleSearch

class SearchTool(BaseModel):
    """
        A tool for performing web searches using SerpAPI.
        Requires a SerpAPI API key.

        Attributes:
            name (str): The name of the tool.
            description (str): A brief description of the tool's functionality.
            apikey (str): The SerpAPI API key for authentication.
        
        Methods:
            _search(query: str, num_results: int) -> List[str]: Perform a web search and return the top results.
            run(query: str, num_results: int) -> str: Run the search tool and return formatted results.
    """

    name: str = "web_search"
    description: str = '''
            A tool for performing web searches to find relevant information.

            Input : Input should be a search query string.
            Output: Output will be a list of relevant search result snippets.
    '''    
    apikey: str = Field(..., description="Your SerpAPI API key.")

    def _search(self, query: str, num_results: int = 5) -> List[str]:
        """Perform a web search and return the top results."""
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.apikey,
            "num": num_results
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "error" in results:
            raise ValueError(f"SerpAPI Error: {results['error']}")

        urls = []
        for result in results.get("organic_results", []):
            if result:
                urls.append(
                    {
                        "title": result.get('title', ''),
                        "link": result.get('link', ''),
                        "snippet": result.get('snippet', ''),
                        "sitelinks": result.get('sitelinks', {}),
                        "source": result.get('source', 'google')
                    }
                )        
        return urls

    async def run(self, query: str, num_results: int = 5) -> str:
        """Run the search tool and return formatted results."""
        try:
            urls = self._search(query, num_results)
            if not urls:
                return "No results found."
            return {i: url for i, url in enumerate(urls)}
        except Exception as e:
            return f"An error occurred during the search: {str(e)}"
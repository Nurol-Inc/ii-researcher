import os
import re
import urllib.parse

import requests
from tavily import TavilyClient, MissingAPIKeyError, InvalidAPIKeyError

try:
    from ddgs import DDGS
    HAS_DUCKDUCKGO = True
except ImportError:
    HAS_DUCKDUCKGO = False

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


class SearchClient:
    """A class that provides web search capabilities using different search providers."""

    def __init__(self, query=None, max_results=10, search_provider="tavily"):
        """
        Initialize the WebSearchTool with search parameters and API keys.

        Args:
            query: The search query to execute
            max_results: Maximum number of results to return
            search_provider: The search provider to use ("serpapi" or "tavily")
        """
        self.query = query
        self.max_results = max_results
        self.search_provider = search_provider.lower()

    def _search_query_by_tavily(self, query, max_results=10):
        """Searches the query using Tavily API."""
        tavily_api_key = os.environ.get("TAVILY_API_KEY")
        try:
            client = TavilyClient(tavily_api_key)
            response = client.search(
                query=query,
                max_results=max_results,
                include_raw_content=True,
                # search_depth="advanced",
            )
            return response.get("results", [])
        except (MissingAPIKeyError, InvalidAPIKeyError) as e:
            print(f"API Key Error: {e}. Failed fetching sources from Tavily.")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}. Failed fetching sources from Tavily.")
            return []

    def _search_query_by_jina(self, query, max_results=10):
        """Searches the query using Jina AI search API."""
        jina_api_key = os.environ.get("JINA_API_KEY")
        if not jina_api_key:
            print("Error: JINA_API_KEY environment variable not set")
            return []

        url = "https://s.jina.ai/"
        params = {"q": query, "num": max_results}
        encoded_url = url + "?" + urllib.parse.urlencode(params)

        headers = {
            "Authorization": f"Bearer {jina_api_key}",
            "X-Respond-With": "no-content",
            "Accept": "application/json",
        }

        search_response = []
        try:
            response = requests.get(encoded_url, headers=headers)
            if response.status_code == 200:
                search_results = response.json()["data"]
                if search_results:
                    for result in search_results:
                        search_response.append(
                            {
                                "title": result.get("title", ""),
                                "url": result.get("url", ""),
                                "content": result.get("description", ""),
                            }
                        )
                return search_response
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []

        return search_response

    def _search_query_by_serp_api(self, query, max_results=10):
        """Searches the query using SerpAPI."""

        serpapi_api_key = os.environ.get("SERPAPI_API_KEY")

        url = "https://serpapi.com/search.json"
        params = {"q": query, "api_key": serpapi_api_key}
        encoded_url = url + "?" + urllib.parse.urlencode(params)
        search_response = []
        try:
            response = requests.get(encoded_url)
            if response.status_code == 200:
                search_results = response.json()
                if search_results:
                    results = search_results["organic_results"]
                    results_processed = 0
                    for result in results:
                        if results_processed >= max_results:
                            break
                        search_response.append(
                            {
                                "title": result["title"],
                                "url": result["link"],
                                "content": result["snippet"],
                            }
                        )
                        results_processed += 1
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []

        return search_response

    def _search_query_by_duckduckgo(self, query, max_results=10):
        """Searches the query using DuckDuckGo with multiple fallback methods."""
        search_response = []
        
        # Method 1: Try the ddgs package with retry
        if HAS_DUCKDUCKGO:
            for attempt in range(3):
                try:
                    ddgs = DDGS()
                    results = list(ddgs.text(query, max_results=max_results))
                    for result in results:
                        search_response.append(
                            {
                                "title": result.get("title", ""),
                                "url": result.get("href", ""),
                                "content": result.get("body", ""),
                            }
                        )
                    if search_response:
                        return search_response
                except Exception as e:
                    print(f"DuckDuckGo attempt {attempt + 1} failed: {e}")
                    import time
                    time.sleep(1)
        
        # Method 2: Fallback to DuckDuckGo HTML search
        if HAS_BS4 and not search_response:
            try:
                search_response = self._search_duckduckgo_html(query, max_results)
            except Exception as e:
                print(f"DuckDuckGo HTML fallback failed: {e}")
        
        return search_response
    
    def _search_duckduckgo_html(self, query, max_results=10):
        """Fallback: Search DuckDuckGo using HTML parsing."""
        search_response = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            # Use DuckDuckGo HTML version
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('div', class_='result')
                
                for i, result in enumerate(results[:max_results]):
                    title_elem = result.find('a', class_='result__a')
                    snippet_elem = result.find('a', class_='result__snippet')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        href = title_elem.get('href', '')
                        
                        # Extract actual URL from DuckDuckGo redirect
                        if 'uddg=' in href:
                            import re
                            url_match = re.search(r'uddg=([^&]+)', href)
                            if url_match:
                                href = urllib.parse.unquote(url_match.group(1))
                        
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                        
                        search_response.append({
                            "title": title,
                            "url": href,
                            "content": snippet,
                        })
        except Exception as e:
            print(f"DuckDuckGo HTML search error: {e}")
        
        return search_response

    def search(self, query=None, max_results=None):
        """
        Execute search using configured provider or provided parameters.

        Args:
            query: The search query (overrides initialization parameter)
            max_results: Maximum number of results (overrides initialization parameter)
        """
        query = query or self.query
        max_results = max_results or self.max_results

        if not query:
            return []

        if self.search_provider == "tavily":
            return self._search_query_by_tavily(query, max_results)
        elif self.search_provider == "serpapi":
            return self._search_query_by_serp_api(query, max_results)
        elif self.search_provider == "jina":
            return self._search_query_by_jina(query, max_results)
        elif self.search_provider == "duckduckgo":
            return self._search_query_by_duckduckgo(query, max_results)
        print(f"Error: Invalid search provider specified {self.search_provider}")
        return {}


def remove_all_line_breaks(text: str) -> str:
    """
    Remove all line breaks from text and replace them with spaces.

    Args:
        text: Input string

    Returns:
        String with line breaks replaced with spaces
    """
    return re.sub(r"(\r\n|\n|\r)", " ", text)

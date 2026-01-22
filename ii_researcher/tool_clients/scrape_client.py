import asyncio
from typing import Optional

from colorama import Fore, Style

from ii_researcher.config import (
    COMPRESS_EMBEDDING_MODEL,
    COMPRESS_MAX_INPUT_WORDS,
    COMPRESS_MAX_OUTPUT_WORDS,
    COMPRESS_SIMILARITY_THRESHOLD,
    MAX_CONCURRENT_BROWSER_SCRAPES,
    SCRAPER_PROVIDER,
    USE_LLM_COMPRESSOR,
)
from ii_researcher.tool_clients.compressor import (
    ContextCompressor,
    EmbeddingCompressor,
    LLMCompressor,
)

from .scraper import Scraper

# Global semaphore to limit concurrent browser scrapes
# This prevents resource exhaustion when multiple sessions scrape simultaneously
_browser_semaphore: Optional[asyncio.Semaphore] = None
_semaphore_lock = asyncio.Lock()


async def get_browser_semaphore() -> asyncio.Semaphore:
    """Get or create the browser scrape semaphore (thread-safe lazy initialization)."""
    global _browser_semaphore
    if _browser_semaphore is None:
        async with _semaphore_lock:
            if _browser_semaphore is None:
                _browser_semaphore = asyncio.Semaphore(MAX_CONCURRENT_BROWSER_SCRAPES)
    return _browser_semaphore


class ScrapeClient:
    def __init__(self, query, cfg=None, context_compressor=None):
        """
        Initialize the ScrapeClient
        Args:
            query: str
            cfg: Config (optional)
        """
        self.query = query
        self.cfg = cfg
        if context_compressor:
            self.context_compressor = context_compressor
        else:
            if (
                COMPRESS_EMBEDDING_MODEL is not None
                and len(COMPRESS_EMBEDDING_MODEL.strip()) > 0
            ):
                # Initialize the embedding compressor with the specified similarity threshold
                # and embedding model
                embedding_compressor = EmbeddingCompressor(
                    similarity_threshold=COMPRESS_SIMILARITY_THRESHOLD,
                    embedding_model=COMPRESS_EMBEDDING_MODEL,
                )
                compressors = [embedding_compressor]
            else:
                compressors = []

            if USE_LLM_COMPRESSOR:
                llm_compressor = LLMCompressor()
                compressors.append(llm_compressor)

            if len(compressors) == 0:
                # No compressor configured - use passthrough mode
                self.context_compressor = None
            else:
                self.context_compressor = ContextCompressor(
                    compressors=compressors,
                    max_input_words=COMPRESS_MAX_INPUT_WORDS,
                    max_output_words=COMPRESS_MAX_OUTPUT_WORDS,
                )

    def _scrape_urls(self, urls):
        """
        Scrapes the urls using browser

        Returns:
            Dict[str, Any]: Scraped content contains the raw content, title, url, image_urls
        """
        scraped_data = []
        user_agent = (
            self.cfg.user_agent
            if self.cfg
            else "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )

        try:
            scraper = Scraper(urls, user_agent, SCRAPER_PROVIDER)
            scraped_data = scraper.run()

        except Exception as e:
            print(f"{Fore.RED}Error in scrape_urls_by_browser: {e}{Style.RESET_ALL}")

        return scraped_data

    def _handle_github_link(self, url):
        """
        Handle github links by converting them to raw links
        """
        if "github.com" in url and "/blob/" in url:
            url = url.replace("github.com", "raw.githubusercontent.com").replace(
                "/blob/", "/"
            )
            return url
        return url

    async def scrape(self, url):
        """Scrape a URL with browser semaphore limiting for concurrent safety.
        
        Uses a semaphore to limit concurrent browser scrapes (configurable via
        MAX_CONCURRENT_BROWSER_SCRAPES env var, default: 5). This prevents
        resource exhaustion when multiple research sessions run in parallel.
        """
        url = self._handle_github_link(url)
        
        # Get the browser semaphore for limiting concurrent scrapes
        semaphore = await get_browser_semaphore()
        
        try:
            # Acquire semaphore before scraping (limits concurrent browser instances)
            async with semaphore:
                # Run the blocking scrape operation in a thread pool
                scraped_data = await asyncio.to_thread(self._scrape_urls_single, url)
            
            if scraped_data is None:
                return {
                    "raw_content": "",
                    "url": url,
                    "content": f"Unable to access the content at {url}. Please consider exploring alternative sources to find the information you need.",
                }
            
            # Use compressor if available, otherwise use raw content
            if self.context_compressor is not None:
                compressed_content = await self.context_compressor.acompress(
                    scraped_data["raw_content"],
                    title=scraped_data.get("title", self.query),
                    query=self.query,
                )
                scraped_data["content"] = compressed_content
            else:
                # No compressor - truncate raw content to reasonable size
                raw_content = scraped_data.get("raw_content", "")
                # Truncate to ~10000 words (approx 50000 chars)
                if len(raw_content) > 50000:
                    scraped_data["content"] = raw_content[:50000] + "... [truncated]"
                else:
                    scraped_data["content"] = raw_content

            return scraped_data
        except Exception as e:
            print(f"{Fore.RED}Error in scrape: {e}{Style.RESET_ALL}")
            return {
                "raw_content": "",
                "url": url,
                "content": f"Unable to access the content at {url}. Please consider exploring alternative sources to find the information you need.",
            }
    
    def _scrape_urls_single(self, url):
        """Scrape a single URL synchronously (for use with asyncio.to_thread)."""
        try:
            result = self._scrape_urls([url])
            return result[0] if result else None
        except Exception as e:
            print(f"{Fore.RED}Error in _scrape_urls_single: {e}{Style.RESET_ALL}")
            return None

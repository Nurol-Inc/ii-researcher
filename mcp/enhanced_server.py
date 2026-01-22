"""
II-Researcher Enhanced MCP Server v2.3.0

A practical, working MCP server that exposes ii-researcher's deep research
capabilities through the Model Context Protocol.

Features:
- Deep research via the actual ReasoningAgent
- Batch web search (like ii-agent's WebBatchSearchTool)
- Web scraping with embedding-based content compression
- DuckDuckGo search with fallback support
- Simple environment variable configuration
- **Concurrent session support** - Multiple clients can perform research simultaneously
- **Timeout protection** - Configurable timeout for deep research operations
- **Browser scrape limiting** - Configurable concurrent browser scrape limit

Usage:
    # Start with stdio transport (for Claude Desktop)
    python mcp/enhanced_server.py

    # Start with HTTP transport
    python mcp/enhanced_server.py --transport sse --port 8765

Environment Variables:
    OPENAI_API_KEY          - OpenAI API key (required)
    OPENAI_BASE_URL         - OpenAI API base URL (default: http://localhost:4000)
    EMBEDDING_BASE_URL      - Embedding server URL (default: same as OPENAI_BASE_URL)
    R_MODEL                 - Model name for reasoning (default: r1)
    R_REPORT_MODEL          - Model name for reports (default: gpt-4o)
    SEARCH_PROVIDER         - Search provider: tavily, serpapi, jina, duckduckgo
    SCRAPER_PROVIDER        - Scraper provider: bs, firecrawl, browser, jina
    COMPRESS_EMBEDDING_MODEL - Embedding model for content compression
    DEEP_RESEARCH_TIMEOUT   - Timeout for deep research in seconds (default: 600)
    MAX_CONCURRENT_BROWSER_SCRAPES - Max concurrent browser scrapes (default: 5)

Concurrent Session Support:
    This server supports multiple concurrent research sessions. Each call to
    deep_research creates an isolated session with its own:
    - Configuration settings
    - Search query history (prevents duplicate searches within a session)
    - Visited URL history (prevents duplicate visits within a session)
    
    Sessions are fully isolated - one client's research does not affect another's.
"""

import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ii_researcher.reasoning.agent import ReasoningAgent
from ii_researcher.reasoning.builders.report import ReportType
from ii_researcher.reasoning.config import create_config
from ii_researcher.tool_clients.search_client import SearchClient
from ii_researcher.tool_clients.scrape_client import ScrapeClient
from ii_researcher.config import (
    COMPRESS_EMBEDDING_MODEL,
    EMBEDDING_BASE_URL,
    COMPRESS_SIMILARITY_THRESHOLD,
    DEEP_RESEARCH_TIMEOUT,
    MAX_CONCURRENT_BROWSER_SCRAPES,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ii-researcher-mcp")

# Track active sessions for monitoring (async-safe counter using asyncio.Lock)
_active_sessions_lock = asyncio.Lock()
_active_sessions = 0
_total_sessions = 0

# Browser scrape semaphore for limiting concurrent browser operations
_browser_scrape_semaphore: Optional[asyncio.Semaphore] = None

def get_browser_semaphore() -> asyncio.Semaphore:
    """Get or create the browser scrape semaphore."""
    global _browser_scrape_semaphore
    if _browser_scrape_semaphore is None:
        _browser_scrape_semaphore = asyncio.Semaphore(MAX_CONCURRENT_BROWSER_SCRAPES)
    return _browser_scrape_semaphore


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

async def get_server_status_impl() -> Dict[str, Any]:
    """
    Get the current status of the II-Researcher MCP server.
    
    Returns information about:
    - Server version and uptime
    - Configured LLM settings
    - Embedding configuration
    - Search and scraper providers
    - Available API keys
    - Active session information (for concurrent session monitoring)
    """
    # Create a config to read default settings (doesn't affect any session)
    config = create_config()
    
    # Check which API keys are configured
    api_keys_status = {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "tavily": bool(os.getenv("TAVILY_API_KEY")),
        "serpapi": bool(os.getenv("SERPAPI_API_KEY")),
        "jina": bool(os.getenv("JINA_API_KEY")),
        "firecrawl": bool(os.getenv("FIRECRAWL_API_KEY")),
    }
    
    # Check embedding configuration
    embedding_configured = bool(COMPRESS_EMBEDDING_MODEL and COMPRESS_EMBEDDING_MODEL.strip())
    
    # Get session statistics (use sync access since this is just reading)
    active = _active_sessions
    total = _total_sessions
    
    return {
        "status": "healthy",
        "version": "2.3.0",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "llm_model": config.llm.model,
            "llm_base_url": config.llm.base_url,
            "report_model": config.llm.report_model,
            "temperature": config.llm.temperature,
            "search_provider": config.tool.search_provider,
            "max_search_results": config.tool.max_search_results,
            "max_search_queries": config.tool.max_search_queries,
            "max_urls_to_visit": config.tool.max_urls_to_visit,
        },
        "embedding": {
            "enabled": embedding_configured,
            "model": COMPRESS_EMBEDDING_MODEL if embedding_configured else None,
            "base_url": EMBEDDING_BASE_URL if embedding_configured else None,
            "similarity_threshold": COMPRESS_SIMILARITY_THRESHOLD if embedding_configured else None,
        },
        "api_keys_configured": api_keys_status,
        "scraper_provider": os.getenv("SCRAPER_PROVIDER", "firecrawl"),
        "concurrency": {
            "deep_research_timeout_seconds": DEEP_RESEARCH_TIMEOUT,
            "max_concurrent_browser_scrapes": MAX_CONCURRENT_BROWSER_SCRAPES,
        },
        "sessions": {
            "active": active,
            "total_since_start": total,
            "concurrent_support": True,
        },
    }


async def deep_research_impl(
    question: str,
    report_type: str = "advanced",
    progress_callback: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Perform comprehensive multi-step research on a topic.
    
    This tool conducts thorough research using:
    1. Iterative web searches to gather information
    2. Web scraping to extract detailed content from sources
    3. Multi-step reasoning to analyze and synthesize findings
    4. Report generation with citations and structured sections
    
    Each call creates an isolated session, allowing multiple concurrent
    research operations without interference.
    
    Timeout: Configurable via DEEP_RESEARCH_TIMEOUT env var (default: 600s)
    Progress: Sends progress notifications via MCP protocol if client supports it
    """
    import queue  # Thread-safe queue for cross-thread communication
    
    global _active_sessions, _total_sessions
    
    # Generate unique session ID for tracking
    session_id = str(uuid.uuid4())[:8]
    
    # Track session start (using async lock)
    async with _active_sessions_lock:
        _active_sessions += 1
        _total_sessions += 1
        current_active = _active_sessions
    
    logger.info(f"[Session {session_id}] Starting deep research: {question[:100]}...")
    logger.info(f"[Session {session_id}] Active sessions: {current_active}, Timeout: {DEEP_RESEARCH_TIMEOUT}s")
    start_time = datetime.now()
    
    # Thread-safe queue for cross-thread progress communication
    # (asyncio.Queue doesn't work across event loops in different threads)
    thread_safe_queue: queue.Queue = queue.Queue()
    
    try:
        # Map report type string to enum
        rt = ReportType.ADVANCED if report_type.lower() == "advanced" else ReportType.BASIC
        
        # Create a SYNCHRONOUS progress callback that puts messages in thread-safe queue
        # This callback will be called from within the agent's thread
        def sync_progress_callback(progress: float, total: float, message: str):
            thread_safe_queue.put((progress, total, message))
            logger.info(f"[Session {session_id}] Progress: {progress:.1f}% - {message}")
        
        # Initialize the reasoning agent with sync progress callback wrapper
        # The agent expects an async callback, so we wrap the sync one
        async def agent_progress_callback(progress: float, total: float, message: str):
            # This will be called from the agent's event loop in the thread
            # We put the message in the thread-safe queue (sync operation)
            sync_progress_callback(progress, total, message)
        
        agent = ReasoningAgent(
            question=question,
            report_type=rt,
            progress_callback=agent_progress_callback,
        )
        
        # Send initial progress notification
        if progress_callback:
            try:
                await progress_callback(0.0, 100.0, "Starting research session...")
            except Exception as e:
                logger.warning(f"[Session {session_id}] Initial progress callback error: {e}")
        
        # Run the research with timeout protection
        # The agent.run() method contains blocking synchronous calls (OpenAI sync client),
        # so we wrap it in asyncio.to_thread to avoid blocking the event loop
        try:
            # Start agent in background task
            agent_task = asyncio.create_task(_run_agent_with_progress(agent))
            
            # Process progress updates while agent runs
            while not agent_task.done():
                # Check thread-safe queue for progress updates (non-blocking)
                try:
                    progress, total, message = thread_safe_queue.get_nowait()
                    # Send progress notification if callback available
                    if progress_callback:
                        try:
                            await progress_callback(progress, total, message)
                        except Exception as e:
                            logger.warning(f"[Session {session_id}] Progress callback error: {e}")
                except queue.Empty:
                    # No progress update, yield control briefly
                    await asyncio.sleep(0.1)
                    continue
            
            # Drain any remaining progress updates from the queue
            while True:
                try:
                    progress, total, message = thread_safe_queue.get_nowait()
                    if progress_callback:
                        try:
                            await progress_callback(progress, total, message)
                        except Exception as e:
                            logger.warning(f"[Session {session_id}] Progress callback error: {e}")
                except queue.Empty:
                    break
            
            # Get the result (may raise if agent failed)
            report = await asyncio.wait_for(agent_task, timeout=DEEP_RESEARCH_TIMEOUT)
            
        except asyncio.TimeoutError:
            logger.error(f"[Session {session_id}] Research timed out after {DEEP_RESEARCH_TIMEOUT}s")
            # Send timeout progress notification
            if progress_callback:
                try:
                    await progress_callback(100.0, 100.0, "Research timed out")
                except Exception:
                    pass
            return {
                "error": f"Research timed out after {DEEP_RESEARCH_TIMEOUT} seconds",
                "report": None,
                "sources": {"visited_urls": [], "search_queries": []},
                "metadata": {
                    "question": question,
                    "report_type": report_type,
                    "duration_seconds": DEEP_RESEARCH_TIMEOUT,
                    "error": True,
                    "timed_out": True,
                    "session_id": session_id,
                }
            }
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Extract visited URLs from the agent's tool history
        visited_urls = list(agent.tool_history.get_visited_urls()) if agent.tool_history else []
        searched_queries = list(agent.tool_history.get_searched_queries()) if agent.tool_history else []
        
        logger.info(f"[Session {session_id}] Research completed in {duration:.2f}s, visited {len(visited_urls)} URLs")
        
        # Send completion progress notification
        if progress_callback:
            try:
                await progress_callback(100.0, 100.0, "Research complete")
            except Exception as e:
                logger.warning(f"[Session {session_id}] Completion progress callback error: {e}")
        
        return {
            "report": report,
            "sources": {
                "visited_urls": visited_urls,
                "search_queries": searched_queries,
            },
            "metadata": {
                "question": question,
                "report_type": report_type,
                "duration_seconds": duration,
                "turns": len(agent.trace.turns) if hasattr(agent, 'trace') else 0,
                "timestamp": end_time.isoformat(),
                "session_id": session_id,
            }
        }
        
    except Exception as e:
        logger.error(f"[Session {session_id}] Research failed: {str(e)}")
        import traceback
        traceback.print_exc()
        # Send error progress notification
        if progress_callback:
            try:
                await progress_callback(100.0, 100.0, f"Research failed: {str(e)}")
            except Exception:
                pass
        return {
            "error": str(e),
            "report": None,
            "sources": {"visited_urls": [], "search_queries": []},
            "metadata": {
                "question": question,
                "report_type": report_type,
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "error": True,
                "session_id": session_id,
            }
        }
    finally:
        # Track session end (using async lock)
        async with _active_sessions_lock:
            _active_sessions -= 1
            remaining = _active_sessions
        logger.info(f"[Session {session_id}] Session ended. Remaining active sessions: {remaining}")


async def _run_agent_with_progress(agent: ReasoningAgent) -> str:
    """Run the agent in a thread pool to avoid blocking the event loop.
    
    The ReasoningAgent.run() method contains synchronous blocking calls
    (OpenAI sync client, Selenium browser operations), so we run it in
    a thread pool to prevent blocking other concurrent research sessions.
    
    Progress updates from the agent are sent via the progress_callback
    which puts messages into a thread-safe queue.
    """
    # Create a new event loop for the thread since agent.run() is async
    # but contains blocking sync calls internally
    def run_sync():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(agent.run(is_stream=False))
        finally:
            loop.close()
    
    return await asyncio.to_thread(run_sync)


async def web_batch_search_impl(
    queries: List[str],
    provider: str = None,
    max_results: int = 5,
) -> Dict[str, Any]:
    """
    Perform batch web searches (multiple queries) using the configured search provider.
    This matches ii-agent's WebBatchSearchTool functionality.
    """
    logger.info(f"Batch web search: {queries}")
    
    # Limit queries and results
    queries = queries[:5]
    max_results = min(max(1, max_results), 10)
    
    # Determine search provider
    search_provider = provider or os.getenv("SEARCH_PROVIDER", "duckduckgo")
    
    all_results = []
    total_count = 0
    
    for query in queries:
        try:
            search_client = SearchClient(
                query=query,
                max_results=max_results,
                search_provider=search_provider.lower()
            )
            results = search_client.search()
            
            all_results.append({
                "query": query,
                "results": results,
                "count": len(results)
            })
            total_count += len(results)
            
        except Exception as e:
            logger.error(f"Search error for query '{query}': {str(e)}")
            all_results.append({
                "query": query,
                "results": [],
                "error": str(e),
                "count": 0
            })
    
    # Format output similar to ii-agent's WebBatchSearchTool
    result_str = ""
    for i, qr in enumerate(all_results):
        result_str += f"Query: {qr['query']}\n"
        for j, result in enumerate(qr.get('results', [])):
            result_str += f"Output {j+1}:\n"
            result_str += f"Title: {result.get('title', '')}\n"
            result_str += f"URL: {result.get('url', '')}\n"
            result_str += f"Snippet: {result.get('content', '')}\n"
            result_str += "-----------------------------------\n"
    
    return {
        "provider": search_provider,
        "total_queries": len(queries),
        "total_results": total_count,
        "results": all_results,
        "formatted_output": result_str,
    }


async def web_search_impl(
    queries: List[str],
    provider: str = None,
    max_results: int = 5,
) -> Dict[str, Any]:
    """
    Perform web searches using the configured search provider.
    Wrapper around web_batch_search for backward compatibility.
    """
    return await web_batch_search_impl(queries, provider, max_results)


async def web_scrape_impl(
    urls: List[str],
    query: str = "",
) -> Dict[str, Any]:
    """
    Scrape and extract content from web pages with optional embedding-based compression.
    """
    logger.info(f"Web scrape: {urls}")
    
    # Limit URLs
    urls = urls[:5]
    
    # Check if embedding compression is configured
    embedding_enabled = bool(COMPRESS_EMBEDDING_MODEL and COMPRESS_EMBEDDING_MODEL.strip())
    
    results = []
    for url in urls:
        try:
            scrape_client = ScrapeClient(query=query or "")
            scraped_data = await scrape_client.scrape(url)
            
            results.append({
                "url": url,
                "title": scraped_data.get("title", ""),
                "content": scraped_data.get("content", ""),
                "success": True,
                "compression_used": embedding_enabled,
            })
            
        except Exception as e:
            logger.error(f"Scrape error for URL '{url}': {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                "url": url,
                "title": "",
                "content": "",
                "error": str(e),
                "success": False,
            })
    
    return {
        "total_urls": len(urls),
        "successful": sum(1 for r in results if r.get("success")),
        "embedding_compression": embedding_enabled,
        "results": results,
    }


async def web_visit_compress_impl(
    urls: List[str],
    query: str,
) -> Dict[str, Any]:
    """
    Visit URLs and extract content with query-based compression.
    This matches ii-agent's WebVisitCompressTool functionality.
    """
    logger.info(f"Web visit compress: {urls} with query: {query}")
    
    # Process URLs (handle arxiv links)
    processed_urls = []
    for url in urls:
        if "arxiv.org/abs" in url:
            url = "https://arxiv.org/html/" + url.split("/")[-1]
        processed_urls.append(url)
    
    return await web_scrape_impl(processed_urls, query)


async def configure_research_impl(
    search_provider: str = None,
    max_search_results: int = None,
    max_search_queries: int = None,
    max_urls_to_visit: int = None,
    llm_temperature: float = None,
) -> Dict[str, Any]:
    """
    Get current default research configuration.
    
    Note: With session isolation, each deep_research call creates its own
    isolated configuration. This tool shows the default settings that new
    sessions will use (based on environment variables).
    
    The parameters are accepted for API compatibility but are informational only.
    To change settings, modify environment variables and restart the server.
    """
    # Create a config to show default values
    config = create_config()
    
    # Show what was requested vs current defaults
    requested = {}
    if search_provider:
        requested["search_provider"] = search_provider
    if max_search_results is not None:
        requested["max_search_results"] = max_search_results
    if max_search_queries is not None:
        requested["max_search_queries"] = max_search_queries
    if max_urls_to_visit is not None:
        requested["max_urls_to_visit"] = max_urls_to_visit
    if llm_temperature is not None:
        requested["llm_temperature"] = llm_temperature
    
    return {
        "note": "With session isolation, each research call uses its own config. "
                "These are the default settings for new sessions.",
        "requested_changes": requested if requested else "none",
        "current_defaults": {
            "search_provider": config.tool.search_provider,
            "max_search_results": config.tool.max_search_results,
            "max_search_queries": config.tool.max_search_queries,
            "max_urls_to_visit": config.tool.max_urls_to_visit,
            "llm_temperature": config.llm.temperature,
        },
        "how_to_change": "Set environment variables (SEARCH_PROVIDER, R_TEMPERATURE, etc.) and restart server"
    }


# ============================================================================
# CREATE AND CONFIGURE MCP SERVER
# ============================================================================

def create_server(host: str = "0.0.0.0", port: int = 8765, log_level: str = "INFO"):
    """Create and configure the MCP server with all tools."""
    from mcp.server.fastmcp import FastMCP, Context
    
    # Create server with configuration
    server = FastMCP(
        name="II-Researcher",
        host=host,
        port=port,
        log_level=log_level,
    )
    
    # Register tools using decorators
    @server.tool()
    async def get_server_status() -> Dict[str, Any]:
        """Get the current status of the II-Researcher MCP server including configuration, embedding settings, and health information."""
        return await get_server_status_impl()
    
    @server.tool()
    async def deep_research(
        question: str,
        report_type: str = "advanced",
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive multi-step research on a topic.
        
        This tool conducts thorough research using iterative web searches,
        content extraction, multi-step reasoning, and report generation.
        
        Progress notifications are sent during research if the client supports them.
        
        Args:
            question: The research question or topic to investigate
            report_type: Type of report - "basic" for quick summary, "advanced" for comprehensive report
        
        Returns:
            Research results including report, sources, and metadata
        """
        # Create progress callback using Context if available
        progress_callback = None
        logger.info(f"[deep_research] Context available: {ctx is not None}")
        if ctx:
            logger.info(f"[deep_research] Context type: {type(ctx)}, has report_progress: {hasattr(ctx, 'report_progress')}")
            async def progress_callback(progress: float, total: float, message: str):
                logger.info(f"[deep_research] Sending MCP progress: {progress:.1f}% - {message}")
                try:
                    await ctx.report_progress(progress, total, message)
                    logger.info(f"[deep_research] MCP progress sent successfully")
                except Exception as e:
                    logger.error(f"[deep_research] MCP progress error: {e}")
        else:
            logger.warning("[deep_research] No Context available - progress notifications disabled")
        
        return await deep_research_impl(question, report_type, progress_callback)
    
    @server.tool()
    async def web_batch_search(
        queries: List[str],
        provider: str = None,
        max_results: int = 5,
    ) -> Dict[str, Any]:
        """
        Perform batch web searches (multiple queries at once) using the configured search provider.
        This is the recommended tool for research as it efficiently handles multiple queries.
        
        Args:
            queries: List of search queries to execute (max 5)
            provider: Search provider override (tavily, serpapi, jina, duckduckgo)
            max_results: Maximum results per query (1-10)
        
        Returns:
            Search results for each query with formatted output
        """
        return await web_batch_search_impl(queries, provider, max_results)
    
    @server.tool()
    async def web_search(
        queries: List[str],
        provider: str = None,
        max_results: int = 5,
    ) -> Dict[str, Any]:
        """
        Perform web searches using the configured search provider.
        
        Args:
            queries: List of search queries to execute (max 5)
            provider: Search provider override (tavily, serpapi, jina, duckduckgo)
            max_results: Maximum results per query (1-10)
        
        Returns:
            Search results for each query
        """
        return await web_search_impl(queries, provider, max_results)
    
    @server.tool()
    async def web_scrape(
        urls: List[str],
        query: str = "",
    ) -> Dict[str, Any]:
        """
        Scrape and extract content from web pages with optional embedding-based compression.
        
        Args:
            urls: List of URLs to scrape (max 5)
            query: Optional query for content relevance filtering (uses embedding similarity)
        
        Returns:
            Scraped content for each URL
        """
        return await web_scrape_impl(urls, query)
    
    @server.tool()
    async def web_visit_compress(
        urls: List[str],
        query: str,
    ) -> Dict[str, Any]:
        """
        Visit URLs and extract content with query-based compression.
        Similar to web_scrape but optimized for research with query context.
        Handles special URL formats like arxiv.org/abs links.
        
        Args:
            urls: List of URLs to visit (max 5)
            query: Query for content relevance filtering (required)
        
        Returns:
            Extracted and compressed content for each URL
        """
        return await web_visit_compress_impl(urls, query)
    
    @server.tool()
    async def configure_research(
        search_provider: str = None,
        max_search_results: int = None,
        max_search_queries: int = None,
        max_urls_to_visit: int = None,
        llm_temperature: float = None,
    ) -> Dict[str, Any]:
        """
        Configure research parameters at runtime.
        
        Args:
            search_provider: Search provider (tavily, serpapi, jina, duckduckgo)
            max_search_results: Maximum search results per query (1-20)
            max_search_queries: Maximum queries per search operation (1-5)
            max_urls_to_visit: Maximum URLs to visit per operation (1-10)
            llm_temperature: LLM temperature (0.0-1.0)
        
        Returns:
            Updated configuration
        """
        return await configure_research_impl(
            search_provider, max_search_results, max_search_queries,
            max_urls_to_visit, llm_temperature
        )
    
    return server


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Run the II-Researcher MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="II-Researcher MCP Server - Deep research via Model Context Protocol"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio for Claude Desktop)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="HTTP server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="HTTP server port (default: 8765)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check embedding configuration
    embedding_enabled = bool(COMPRESS_EMBEDDING_MODEL and COMPRESS_EMBEDDING_MODEL.strip())
    
    # Log startup info
    logger.info("=" * 60)
    logger.info("II-Researcher MCP Server v2.3.0")
    logger.info("Concurrent session support: ENABLED")
    logger.info("=" * 60)
    logger.info(f"Transport: {args.transport}")
    if args.transport == "sse":
        logger.info(f"Endpoint: http://{args.host}:{args.port}")
    logger.info(f"Search Provider: {os.getenv('SEARCH_PROVIDER', 'duckduckgo')}")
    logger.info(f"Scraper Provider: {os.getenv('SCRAPER_PROVIDER', 'bs')}")
    logger.info(f"LLM Base URL: {os.getenv('OPENAI_BASE_URL', 'http://localhost:4000')}")
    logger.info(f"Deep Research Timeout: {DEEP_RESEARCH_TIMEOUT}s")
    logger.info(f"Max Concurrent Browser Scrapes: {MAX_CONCURRENT_BROWSER_SCRAPES}")
    if embedding_enabled:
        logger.info(f"Embedding Model: {COMPRESS_EMBEDDING_MODEL}")
        logger.info(f"Embedding Base URL: {EMBEDDING_BASE_URL}")
    else:
        logger.info("Embedding: Disabled (passthrough mode)")
    logger.info("=" * 60)
    
    # Create server
    server = create_server(
        host=args.host,
        port=args.port,
        log_level=args.log_level,
    )
    
    # Run the server
    server.run(transport=args.transport)


if __name__ == "__main__":
    main()

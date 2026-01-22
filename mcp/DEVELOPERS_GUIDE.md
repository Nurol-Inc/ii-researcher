# II-Researcher MCP Server Developer's Guide

A comprehensive guide for application developers to integrate II-Researcher's deep research capabilities into agentic applications using the Model Context Protocol (MCP).

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Server Configuration](#server-configuration)
5. [Available Tools](#available-tools)
6. [Integration Patterns](#integration-patterns)
7. [Client Examples](#client-examples)
8. [Advanced Usage](#advanced-usage)
9. [Error Handling](#error-handling)
10. [Best Practices](#best-practices)

---

## Overview

The II-Researcher MCP Server exposes powerful deep research capabilities through the standardized Model Context Protocol. It enables AI agents and applications to:

- **Conduct autonomous multi-step research** using iterative web searches and content extraction
- **Perform batch web searches** across multiple queries simultaneously
- **Scrape and extract content** from web pages with intelligent compression
- **Generate comprehensive research reports** with citations and structured sections

### Key Features

| Feature | Description |
|---------|-------------|
| Deep Research | Multi-step reasoning with automatic web search and content synthesis |
| Batch Search | Execute multiple search queries in parallel |
| Web Scraping | Extract and compress content with embedding-based relevance filtering |
| Configurable Providers | Support for Tavily, SerpAPI, Jina, and DuckDuckGo search providers |
| Multiple Transports | stdio (for Claude Desktop) and SSE/HTTP for programmatic access |

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MCP Client Application                        │
│                 (Claude Desktop, Custom Agents, etc.)                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ MCP Protocol (stdio/SSE)
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      II-Researcher MCP Server                        │
│                        (enhanced_server.py)                          │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │deep_research│  │web_batch_   │  │ web_scrape  │  │ configure_ │ │
│  │             │  │search       │  │             │  │ research   │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────────────┘ │
│         │                │                │                         │
│         ▼                ▼                ▼                         │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                     ReasoningAgent                               ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          ││
│  │  │  ToolHistory │  │    Trace     │  │ ReportBuilder│          ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘          ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │SearchClient │ │ScrapeClient │ │  OpenAI/    │
            │             │ │             │ │  LiteLLM    │
            └─────────────┘ └─────────────┘ └─────────────┘
                    │               │               │
                    ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │ DuckDuckGo  │ │BeautifulSoup│ │  LLM APIs   │
            │ Tavily      │ │ Firecrawl   │ │ (reasoning) │
            │ SerpAPI     │ │ Jina        │ │             │
            │ Jina        │ │ Browser     │ │             │
            └─────────────┘ └─────────────┘ └─────────────┘
```

### Core Components

1. **MCP Server Layer** (`enhanced_server.py`)
   - Handles MCP protocol communication
   - Exposes tools via FastMCP framework
   - Manages transport (stdio/SSE)

2. **ReasoningAgent** (`ii_researcher/reasoning/agent.py`)
   - Orchestrates multi-step research process
   - Manages tool execution and result synthesis
   - Tracks research trace and tool history

3. **Tool Clients** (`ii_researcher/tool_clients/`)
   - `SearchClient`: Web search abstraction across providers
   - `ScrapeClient`: Web scraping with content compression
   - `ContextCompressor`: Embedding-based content filtering

4. **Report Builder** (`ii_researcher/reasoning/builders/report.py`)
   - Generates structured research reports
   - Supports basic and advanced report types
   - Handles subtopic generation and synthesis

---

## Quick Start

### Prerequisites

- Python 3.10+
- uv or pip for package management
- Access to an OpenAI-compatible LLM API

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ii-researcher

# Install dependencies using uv
uv sync

# Or using pip
pip install -e .
```

### Start the Server

#### Option 1: Using the startup script

```bash
# Start with HTTP transport (recommended for programmatic access)
./mcp/run_server.sh http 8765

# Start with stdio transport (for Claude Desktop)
./mcp/run_server.sh
```

#### Option 2: Direct Python execution

```bash
# Set required environment variables
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="http://localhost:4000"
export SEARCH_PROVIDER="duckduckgo"
export SCRAPER_PROVIDER="bs"

# Start with SSE transport
uv run python mcp/enhanced_server.py --transport sse --port 8765

# Start with stdio transport
uv run python mcp/enhanced_server.py --transport stdio
```

### Quick Test

```bash
# Test the server with the research client
python mcp/research_client.py "What is quantum computing?"

# Or test with HTTP directly
python mcp/test_client.py http http://localhost:8765
```

---

## Server Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | API key for LLM access | `empty` |
| `OPENAI_BASE_URL` | Base URL for OpenAI-compatible API | `http://localhost:4000` |
| `EMBEDDING_BASE_URL` | URL for embedding server | Same as `OPENAI_BASE_URL` |
| `R_MODEL` | Model name for reasoning | `r1` |
| `R_REPORT_MODEL` | Model name for report generation | `gpt-4o` |
| `R_TEMPERATURE` | LLM temperature | `0.2` |
| `SEARCH_PROVIDER` | Search provider: `tavily`, `serpapi`, `jina`, `duckduckgo` | `duckduckgo` |
| `SCRAPER_PROVIDER` | Scraper provider: `bs`, `firecrawl`, `browser`, `jina` | `firecrawl` |
| `COMPRESS_EMBEDDING_MODEL` | Model for content compression | `BAAI/bge-m3` |
| `COMPRESS_SIMILARITY_THRESHOLD` | Similarity threshold for compression | `0.30` |
| `USE_LLM_COMPRESSOR` | Enable LLM-based compression | `false` |

### Provider-Specific API Keys

| Provider | Environment Variable |
|----------|---------------------|
| Tavily | `TAVILY_API_KEY` |
| SerpAPI | `SERPAPI_API_KEY` |
| Jina | `JINA_API_KEY` |
| Firecrawl | `FIRECRAWL_API_KEY` |

### Example Configuration

```bash
# Full configuration example
export OPENAI_API_KEY="sk-..."
export OPENAI_BASE_URL="http://localhost:4000"
export EMBEDDING_BASE_URL="http://localhost:4001/v1"
export R_MODEL="gpt-4o"
export R_REPORT_MODEL="gpt-4o"
export SEARCH_PROVIDER="duckduckgo"
export SCRAPER_PROVIDER="bs"
export COMPRESS_EMBEDDING_MODEL="BAAI/bge-m3"
export COMPRESS_SIMILARITY_THRESHOLD="0.30"
```

---

## Available Tools

### 1. `deep_research`

Performs comprehensive multi-step research on a topic using the full ReasoningAgent pipeline.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `question` | string | Yes | The research question or topic |
| `report_type` | string | No | `"basic"` or `"advanced"` (default: `"advanced"`) |

**Response Schema:**

```json
{
  "report": "# Research Report\n\n## Introduction\n...",
  "sources": {
    "visited_urls": ["https://example.com/page1", "..."],
    "search_queries": ["query 1", "query 2", "..."]
  },
  "metadata": {
    "question": "Original research question",
    "report_type": "advanced",
    "duration_seconds": 45.2,
    "turns": 5,
    "timestamp": "2025-12-25T10:30:00.000000"
  }
}
```

**Example Usage:**

```python
result = await session.call_tool("deep_research", {
    "question": "What are the latest developments in quantum computing?",
    "report_type": "advanced"
})
```

### 2. `web_batch_search`

Executes multiple search queries in batch, returning aggregated results.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `queries` | list[string] | Yes | List of search queries (max 5) |
| `provider` | string | No | Override search provider |
| `max_results` | int | No | Results per query (1-10, default: 5) |

**Response Schema:**

```json
{
  "provider": "duckduckgo",
  "total_queries": 3,
  "total_results": 15,
  "results": [
    {
      "query": "quantum computing applications",
      "results": [
        {
          "title": "Page Title",
          "url": "https://example.com",
          "content": "Snippet text..."
        }
      ],
      "count": 5
    }
  ],
  "formatted_output": "Query: quantum computing...\nOutput 1:\n..."
}
```

### 3. `web_search`

Wrapper around `web_batch_search` for backward compatibility.

### 4. `web_scrape`

Scrapes content from web pages with optional embedding-based compression.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `urls` | list[string] | Yes | URLs to scrape (max 5) |
| `query` | string | No | Query for relevance filtering |

**Response Schema:**

```json
{
  "total_urls": 3,
  "successful": 3,
  "embedding_compression": true,
  "results": [
    {
      "url": "https://example.com",
      "title": "Page Title",
      "content": "Extracted and compressed content...",
      "success": true,
      "compression_used": true
    }
  ]
}
```

### 5. `web_visit_compress`

Similar to `web_scrape` but optimized for research with query context. Handles special URL formats like arxiv.org/abs links.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `urls` | list[string] | Yes | URLs to visit (max 5) |
| `query` | string | Yes | Query for content filtering |

### 6. `configure_research`

Dynamically configure research parameters at runtime.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search_provider` | string | No | `tavily`, `serpapi`, `jina`, `duckduckgo` |
| `max_search_results` | int | No | 1-20 |
| `max_search_queries` | int | No | 1-5 |
| `max_urls_to_visit` | int | No | 1-10 |
| `llm_temperature` | float | No | 0.0-1.0 |

**Response Schema:**

```json
{
  "updated": {
    "search_provider": "tavily",
    "max_search_results": 10
  },
  "current_config": {
    "search_provider": "tavily",
    "max_search_results": 10,
    "max_search_queries": 2,
    "max_urls_to_visit": 3,
    "llm_temperature": 0.2
  }
}
```

### 7. `get_server_status`

Returns server health and configuration information.

**Response Schema:**

```json
{
  "status": "healthy",
  "version": "2.1.0",
  "timestamp": "2025-12-25T10:30:00.000000",
  "config": {
    "llm_model": "gpt-4o",
    "llm_base_url": "http://localhost:4000",
    "report_model": "gpt-4o",
    "temperature": 0.2,
    "search_provider": "duckduckgo",
    "max_search_results": 4,
    "max_search_queries": 2,
    "max_urls_to_visit": 3
  },
  "embedding": {
    "enabled": true,
    "model": "BAAI/bge-m3",
    "base_url": "http://localhost:4001/v1",
    "similarity_threshold": 0.3
  },
  "api_keys_configured": {
    "openai": true,
    "tavily": false,
    "serpapi": false,
    "jina": false,
    "firecrawl": false
  },
  "scraper_provider": "bs"
}
```

---

## Integration Patterns

### Pattern 1: Claude Desktop Integration

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ii-researcher": {
      "command": "python",
      "args": ["-m", "mcp.enhanced_server"],
      "cwd": "/path/to/ii-researcher",
      "env": {
        "OPENAI_API_KEY": "your-api-key",
        "OPENAI_BASE_URL": "http://localhost:4000",
        "SEARCH_PROVIDER": "duckduckgo",
        "SCRAPER_PROVIDER": "bs"
      }
    }
  }
}
```

### Pattern 2: HTTP/SSE Client Integration

```python
from mcp.client.sse import sse_client
from mcp import ClientSession

async def research_with_mcp(question: str) -> dict:
    """Perform research using the MCP server."""
    async with sse_client("http://localhost:8765/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool("deep_research", {
                "question": question,
                "report_type": "advanced"
            })
            
            return json.loads(result.content[0].text)
```

### Pattern 3: Agentic Workflow Integration

```python
class ResearchAgent:
    """An agent that uses II-Researcher for information gathering."""
    
    def __init__(self, mcp_server_url: str):
        self.server_url = mcp_server_url
        self.session = None
    
    async def connect(self):
        """Establish connection to MCP server."""
        self.read, self.write = await sse_client(f"{self.server_url}/sse").__aenter__()
        self.session = await ClientSession(self.read, self.write).__aenter__()
        await self.session.initialize()
    
    async def research(self, topic: str) -> str:
        """Conduct research on a topic."""
        result = await self.session.call_tool("deep_research", {
            "question": topic,
            "report_type": "advanced"
        })
        return json.loads(result.content[0].text)["report"]
    
    async def quick_search(self, queries: list) -> list:
        """Perform quick batch searches."""
        result = await self.session.call_tool("web_batch_search", {
            "queries": queries,
            "max_results": 5
        })
        return json.loads(result.content[0].text)["results"]
    
    async def extract_content(self, urls: list, context: str) -> list:
        """Extract relevant content from URLs."""
        result = await self.session.call_tool("web_visit_compress", {
            "urls": urls,
            "query": context
        })
        return json.loads(result.content[0].text)["results"]
```

### Pattern 4: Multi-Agent Research System

```python
import asyncio
from dataclasses import dataclass
from typing import List

@dataclass
class ResearchTask:
    question: str
    priority: int = 1

class MultiAgentResearchSystem:
    """Coordinate multiple research tasks using II-Researcher."""
    
    def __init__(self, mcp_server_url: str, max_concurrent: int = 3):
        self.server_url = mcp_server_url
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _research_task(self, task: ResearchTask) -> dict:
        """Execute a single research task."""
        async with self.semaphore:
            async with sse_client(f"{self.server_url}/sse") as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool("deep_research", {
                        "question": task.question,
                        "report_type": "advanced"
                    })
                    return {
                        "question": task.question,
                        "result": json.loads(result.content[0].text)
                    }
    
    async def research_batch(self, tasks: List[ResearchTask]) -> List[dict]:
        """Execute multiple research tasks concurrently."""
        # Sort by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        # Execute concurrently with semaphore limiting
        results = await asyncio.gather(
            *[self._research_task(task) for task in sorted_tasks],
            return_exceptions=True
        )
        
        return [r for r in results if not isinstance(r, Exception)]
```

---

## Client Examples

### Python Client (Recommended)

```python
#!/usr/bin/env python3
"""Example: Using II-Researcher MCP Server in Python."""

import asyncio
import json
from mcp.client.sse import sse_client
from mcp import ClientSession

async def main():
    server_url = "http://localhost:8765"
    
    async with sse_client(f"{server_url}/sse") as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])
            
            # Check server status
            status = await session.call_tool("get_server_status", {})
            print("Server status:", json.loads(status.content[0].text))
            
            # Perform a quick search
            search_result = await session.call_tool("web_batch_search", {
                "queries": ["Python best practices 2025", "async programming patterns"],
                "max_results": 3
            })
            print("Search results:", json.loads(search_result.content[0].text))
            
            # Conduct deep research
            research_result = await session.call_tool("deep_research", {
                "question": "What are the key trends in AI development for 2025?",
                "report_type": "basic"
            })
            result_data = json.loads(research_result.content[0].text)
            print("\n=== Research Report ===")
            print(result_data["report"][:2000])
            print(f"\nDuration: {result_data['metadata']['duration_seconds']:.1f}s")
            print(f"Sources: {len(result_data['sources']['visited_urls'])} URLs")

if __name__ == "__main__":
    asyncio.run(main())
```

### HTTP/REST Client (Alternative)

```python
#!/usr/bin/env python3
"""Example: Direct HTTP access to MCP server."""

import httpx
import asyncio

async def call_mcp_tool(base_url: str, tool_name: str, arguments: dict) -> dict:
    """Call an MCP tool via HTTP."""
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{base_url}/mcp/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                },
                "id": 1
            }
        )
        return response.json()

async def main():
    base_url = "http://localhost:8765"
    
    # Perform web search
    result = await call_mcp_tool(base_url, "web_batch_search", {
        "queries": ["machine learning trends 2025"],
        "max_results": 5
    })
    print("Search result:", result)
    
    # Conduct research
    result = await call_mcp_tool(base_url, "deep_research", {
        "question": "What is the state of quantum computing?",
        "report_type": "basic"
    })
    print("Research result:", result)

if __name__ == "__main__":
    asyncio.run(main())
```

### Command-Line Usage

```bash
# Using the built-in research client
python mcp/research_client.py "What is quantum computing?" --type advanced

# With custom server URL
python mcp/research_client.py "AI ethics" --server http://my-server:8765

# JSON output for scripting
python mcp/research_client.py "Machine learning" --json | jq '.report'

# Save results to file
python mcp/research_client.py "Climate change solutions" --json > research.json
```

---

## Advanced Usage

### Custom Report Types

The server supports two report types:

1. **Basic Report**: Quick summary using a single LLM call
2. **Advanced Report**: Comprehensive multi-section report with:
   - Generated introduction
   - Auto-identified subtopics
   - Detailed content per subtopic
   - Formatted references

### Embedding-Based Content Compression

When `COMPRESS_EMBEDDING_MODEL` is configured, the server uses semantic similarity to filter scraped content:

```python
# Content compression flow
raw_content = scraper.scrape(url)  # Full page content

# Embedding compressor filters to relevant chunks
compressed = embedding_compressor.compress(
    raw_content,
    query="your research question",
    similarity_threshold=0.30  # Only keep chunks above this similarity
)
```

### Streaming Support

The ReasoningAgent supports streaming for real-time output:

```python
async def stream_research(question: str):
    agent = ReasoningAgent(
        question=question,
        report_type=ReportType.ADVANCED,
        stream_event=my_stream_handler  # Custom streaming callback
    )
    
    async def on_token(token: str):
        print(token, end="", flush=True)
    
    report = await agent.run(on_token=on_token, is_stream=True)
    return report
```

### Tool History Tracking

The server tracks all searches and visited URLs:

```python
# After research completes
sources = result["sources"]
print(f"Searched queries: {sources['search_queries']}")
print(f"Visited URLs: {sources['visited_urls']}")
```

---

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused` | Server not running | Start the MCP server |
| `API Key Error` | Missing or invalid API key | Set `OPENAI_API_KEY` environment variable |
| `Search provider error` | Provider API issues | Try different `SEARCH_PROVIDER` |
| `Timeout error` | Long-running research | Increase timeout in client |
| `No results` | Search query issues | Refine search queries |

### Error Response Format

```json
{
  "error": "Error message description",
  "report": null,
  "sources": {
    "visited_urls": [],
    "search_queries": []
  },
  "metadata": {
    "question": "Original question",
    "report_type": "advanced",
    "duration_seconds": 5.2,
    "error": true
  }
}
```

### Graceful Degradation

The server implements fallback strategies:

1. **Search fallback**: DuckDuckGo HTML parsing if API fails
2. **Scraper fallback**: BeautifulSoup if Firecrawl unavailable
3. **Compression passthrough**: Raw content if embedding server unavailable

---

## Best Practices

### 1. Resource Management

```python
# Always use context managers for connections
async with sse_client(server_url) as (read, write):
    async with ClientSession(read, write) as session:
        # Your code here
        pass
```

### 2. Timeout Configuration

```python
# Set appropriate timeouts for research tasks
async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minutes
    result = await client.post(...)
```

### 3. Error Recovery

```python
async def resilient_research(question: str, retries: int = 3) -> dict:
    for attempt in range(retries):
        try:
            return await do_research(question)
        except Exception as e:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 4. Rate Limiting

```python
# Use semaphores to limit concurrent requests
semaphore = asyncio.Semaphore(3)

async def rate_limited_research(question: str):
    async with semaphore:
        return await do_research(question)
```

### 5. Result Caching

```python
from functools import lru_cache
import hashlib

# Cache research results
research_cache = {}

async def cached_research(question: str) -> dict:
    cache_key = hashlib.md5(question.encode()).hexdigest()
    if cache_key in research_cache:
        return research_cache[cache_key]
    
    result = await do_research(question)
    research_cache[cache_key] = result
    return result
```

### 6. Logging and Monitoring

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# The server logs important events automatically
# Monitor these logs for debugging and performance analysis
```

---

## Troubleshooting

### Server Won't Start

1. Check Python version: `python --version` (requires 3.10+)
2. Verify dependencies: `uv sync` or `pip install -e .`
3. Check port availability: `lsof -i :8765`

### No Search Results

1. Verify `SEARCH_PROVIDER` is set correctly
2. Check API keys for paid providers
3. Try DuckDuckGo as fallback: `export SEARCH_PROVIDER=duckduckgo`

### Slow Research

1. Reduce `max_search_results` and `max_urls_to_visit`
2. Use `basic` report type for faster results
3. Check LLM API latency

### Memory Issues

1. Reduce `COMPRESS_MAX_INPUT_WORDS`
2. Limit concurrent research tasks
3. Use embedding compression to reduce content size

---

## API Reference

For complete API documentation, see the tool schemas in `enhanced_server.py`. Each tool includes:

- Parameter types and descriptions
- Return value schemas
- Usage examples in docstrings

---

## Contributing

Contributions are welcome! Please see the main repository's contributing guidelines.

---

## License

This project is licensed under the terms specified in the repository's LICENSE file.


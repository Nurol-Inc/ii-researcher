# II-Researcher MCP Server User's Guide

A practical guide for application developers to use II-Researcher's MCP tools for building agentic applications with deep research capabilities.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [MCP Tools Reference](#mcp-tools-reference)
4. [Usage Scenarios](#usage-scenarios)
5. [Building Agentic Applications](#building-agentic-applications)
6. [Working with Results](#working-with-results)
7. [Configuration & Tuning](#configuration--tuning)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

### What is II-Researcher MCP Server?

The II-Researcher MCP Server provides deep research capabilities through the Model Context Protocol (MCP). It allows AI agents and applications to:

- **Conduct autonomous research** - Multi-step reasoning with automatic web searches
- **Search the web** - Execute batch queries across multiple search providers
- **Extract web content** - Scrape and intelligently compress webpage content
- **Generate reports** - Create structured research reports with citations

### When to Use Each Tool

| Use Case | Recommended Tool |
|----------|------------------|
| Comprehensive research on a topic | `deep_research` |
| Quick fact-finding across multiple queries | `web_batch_search` |
| Extracting content from known URLs | `web_scrape` |
| Research-focused content extraction | `web_visit_compress` |
| Adjusting search behavior | `configure_research` |
| Health check / debugging | `get_server_status` |

---

## Getting Started

### Step 1: Start the MCP Server

**Option A: Quick Start with HTTP Transport**

```bash
cd ii-researcher

# Set minimum required environment variables
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="http://localhost:4000"
export SEARCH_PROVIDER="duckduckgo"
export SCRAPER_PROVIDER="bs"

# Start the server
uv run python mcp/enhanced_server.py --transport sse --port 8765
```

**Option B: Using the Startup Script**

```bash
cd ii-researcher
./mcp/run_server.sh http 8765
```

**Option C: For Claude Desktop (stdio transport)**

```bash
uv run python mcp/enhanced_server.py --transport stdio
```

### Step 2: Verify the Server is Running

```bash
# Using the test client
python mcp/test_client.py http http://localhost:8765

# Or using curl
curl -X POST http://localhost:8765/mcp/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### Step 3: Make Your First Research Call

```bash
# Using the research client
python mcp/research_client.py "What is quantum computing?" --type basic
```

---

## MCP Tools Reference

### Tool 1: `deep_research`

**Purpose:** Conduct comprehensive, autonomous research on any topic.

**How it works:**
1. Analyzes your research question
2. Generates and executes relevant search queries
3. Visits and extracts content from promising URLs
4. Synthesizes findings through multi-step reasoning
5. Generates a structured report with citations

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `question` | string | ✅ | - | The research question or topic |
| `report_type` | string | ❌ | `"advanced"` | `"basic"` for quick summary, `"advanced"` for comprehensive report |

**Example Call:**

```python
result = await session.call_tool("deep_research", {
    "question": "What are the environmental impacts of electric vehicles compared to traditional cars?",
    "report_type": "advanced"
})
```

**Response Structure:**

```json
{
  "report": "# Research Report\n\n## Introduction\n...",
  "sources": {
    "visited_urls": ["https://example.com/article1", "https://example.com/article2"],
    "search_queries": ["electric vehicle environmental impact", "EV vs ICE emissions"]
  },
  "metadata": {
    "question": "What are the environmental impacts...",
    "report_type": "advanced",
    "duration_seconds": 87.5,
    "turns": 6,
    "timestamp": "2025-12-25T10:30:00.000000"
  }
}
```

**Report Types Explained:**

| Type | Use When | Typical Duration | Output Length |
|------|----------|------------------|---------------|
| `basic` | Quick overview needed | 30-60 seconds | 500-1500 words |
| `advanced` | Comprehensive analysis required | 2-5 minutes | 2000-5000+ words |

---

### Tool 2: `web_batch_search`

**Purpose:** Execute multiple search queries efficiently in a single call.

**How it works:**
1. Accepts up to 5 search queries
2. Executes each query against the configured search provider
3. Returns aggregated results with titles, URLs, and snippets

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `queries` | list[string] | ✅ | - | List of search queries (max 5) |
| `provider` | string | ❌ | Server default | Override: `tavily`, `serpapi`, `jina`, `duckduckgo` |
| `max_results` | int | ❌ | `5` | Results per query (1-10) |

**Example Call:**

```python
result = await session.call_tool("web_batch_search", {
    "queries": [
        "Python async programming best practices",
        "asyncio vs threading Python",
        "Python concurrent programming patterns"
    ],
    "max_results": 5
})
```

**Response Structure:**

```json
{
  "provider": "duckduckgo",
  "total_queries": 3,
  "total_results": 15,
  "results": [
    {
      "query": "Python async programming best practices",
      "results": [
        {
          "title": "Async IO in Python: A Complete Walkthrough",
          "url": "https://realpython.com/async-io-python/",
          "content": "Learn how to use Python's asyncio module..."
        }
      ],
      "count": 5
    }
  ],
  "formatted_output": "Query: Python async programming...\nOutput 1:\nTitle: ..."
}
```

**Best Practices:**
- Use specific, focused queries for better results
- Vary query phrasing to get diverse results
- Limit to 3-5 queries for optimal performance

---

### Tool 3: `web_search`

**Purpose:** Alias for `web_batch_search` - provided for compatibility.

**Usage:** Identical to `web_batch_search`.

---

### Tool 4: `web_scrape`

**Purpose:** Extract and optionally compress content from web pages.

**How it works:**
1. Fetches content from specified URLs
2. Extracts readable text using configured scraper
3. If embedding model is configured, compresses content to relevant sections
4. Returns structured content for each URL

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `urls` | list[string] | ✅ | - | URLs to scrape (max 5) |
| `query` | string | ❌ | `""` | Query for relevance-based content filtering |

**Example Call:**

```python
result = await session.call_tool("web_scrape", {
    "urls": [
        "https://docs.python.org/3/library/asyncio.html",
        "https://realpython.com/async-io-python/"
    ],
    "query": "how to use asyncio for concurrent programming"
})
```

**Response Structure:**

```json
{
  "total_urls": 2,
  "successful": 2,
  "embedding_compression": true,
  "results": [
    {
      "url": "https://docs.python.org/3/library/asyncio.html",
      "title": "asyncio — Asynchronous I/O",
      "content": "asyncio is a library to write concurrent code...",
      "success": true,
      "compression_used": true
    }
  ]
}
```

**Content Compression:**
- When `COMPRESS_EMBEDDING_MODEL` is configured, content is filtered to sections semantically similar to your query
- Without embedding model, content is truncated to ~50,000 characters
- Use the `query` parameter to improve relevance filtering

---

### Tool 5: `web_visit_compress`

**Purpose:** Research-optimized content extraction with query context.

**How it works:**
1. Processes URLs (handles special formats like arxiv.org/abs)
2. Extracts content with query-based compression
3. Optimized for research workflows

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `urls` | list[string] | ✅ | - | URLs to visit (max 5) |
| `query` | string | ✅ | - | Query for content filtering |

**Special URL Handling:**
- `arxiv.org/abs/XXXX` → automatically converted to `arxiv.org/html/XXXX`

**Example Call:**

```python
result = await session.call_tool("web_visit_compress", {
    "urls": [
        "https://arxiv.org/abs/2301.00001",
        "https://papers.nips.cc/paper/2023/hash/abc123"
    ],
    "query": "transformer architecture attention mechanism"
})
```

---

### Tool 6: `configure_research`

**Purpose:** Dynamically adjust research parameters at runtime.

**Parameters:**

| Parameter | Type | Required | Range | Description |
|-----------|------|----------|-------|-------------|
| `search_provider` | string | ❌ | - | `tavily`, `serpapi`, `jina`, `duckduckgo` |
| `max_search_results` | int | ❌ | 1-20 | Results per search query |
| `max_search_queries` | int | ❌ | 1-5 | Queries per search operation |
| `max_urls_to_visit` | int | ❌ | 1-10 | URLs to visit per operation |
| `llm_temperature` | float | ❌ | 0.0-1.0 | LLM creativity/randomness |

**Example Call:**

```python
# Configure for thorough research
result = await session.call_tool("configure_research", {
    "max_search_results": 10,
    "max_urls_to_visit": 5,
    "llm_temperature": 0.3
})

# Configure for quick searches
result = await session.call_tool("configure_research", {
    "max_search_results": 3,
    "max_urls_to_visit": 2
})
```

**Response Structure:**

```json
{
  "updated": {
    "max_search_results": 10,
    "max_urls_to_visit": 5
  },
  "current_config": {
    "search_provider": "duckduckgo",
    "max_search_results": 10,
    "max_search_queries": 2,
    "max_urls_to_visit": 5,
    "llm_temperature": 0.3
  }
}
```

---

### Tool 7: `get_server_status`

**Purpose:** Check server health and current configuration.

**Parameters:** None

**Example Call:**

```python
result = await session.call_tool("get_server_status", {})
```

**Response Structure:**

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

## Usage Scenarios

### Scenario 1: Research Assistant Agent

Build an agent that answers complex questions with cited research.

```python
import asyncio
import json
from mcp.client.sse import sse_client
from mcp import ClientSession

async def research_assistant(question: str) -> str:
    """Answer a question with researched, cited information."""
    async with sse_client("http://localhost:8765/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Conduct deep research
            result = await session.call_tool("deep_research", {
                "question": question,
                "report_type": "advanced"
            })
            
            data = json.loads(result.content[0].text)
            return data["report"]

# Usage
report = asyncio.run(research_assistant(
    "What are the pros and cons of remote work for software developers?"
))
print(report)
```

### Scenario 2: Fact-Checking Agent

Build an agent that verifies claims by searching multiple sources.

```python
async def fact_checker(claim: str) -> dict:
    """Verify a claim by searching multiple sources."""
    async with sse_client("http://localhost:8765/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Generate verification queries
            queries = [
                f"{claim} evidence",
                f"{claim} fact check",
                f"is it true that {claim}"
            ]
            
            # Search for evidence
            search_result = await session.call_tool("web_batch_search", {
                "queries": queries,
                "max_results": 5
            })
            
            search_data = json.loads(search_result.content[0].text)
            
            # Extract URLs to investigate
            urls = []
            for query_result in search_data["results"]:
                for result in query_result["results"][:2]:
                    urls.append(result["url"])
            
            # Get detailed content from top sources
            if urls:
                scrape_result = await session.call_tool("web_scrape", {
                    "urls": urls[:5],
                    "query": claim
                })
                content_data = json.loads(scrape_result.content[0].text)
            else:
                content_data = {"results": []}
            
            return {
                "claim": claim,
                "sources_found": len(urls),
                "search_results": search_data,
                "detailed_content": content_data
            }
```

### Scenario 3: Content Aggregator

Build an agent that aggregates content from multiple sources on a topic.

```python
async def content_aggregator(topic: str, source_urls: list) -> dict:
    """Aggregate content from multiple sources on a topic."""
    async with sse_client("http://localhost:8765/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Extract content from all sources
            result = await session.call_tool("web_visit_compress", {
                "urls": source_urls,
                "query": topic
            })
            
            data = json.loads(result.content[0].text)
            
            # Organize by source
            aggregated = {
                "topic": topic,
                "sources": []
            }
            
            for item in data["results"]:
                if item["success"]:
                    aggregated["sources"].append({
                        "url": item["url"],
                        "title": item["title"],
                        "content_preview": item["content"][:500] + "..."
                    })
            
            return aggregated
```

### Scenario 4: Competitive Intelligence Agent

Build an agent that researches competitors.

```python
async def competitive_intel(company: str, competitors: list) -> dict:
    """Research a company and its competitors."""
    async with sse_client("http://localhost:8765/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Configure for thorough research
            await session.call_tool("configure_research", {
                "max_search_results": 10,
                "max_urls_to_visit": 5
            })
            
            results = {"company": company, "competitors": {}}
            
            # Research main company
            company_result = await session.call_tool("deep_research", {
                "question": f"What are {company}'s main products, market position, and recent developments?",
                "report_type": "basic"
            })
            results["company_analysis"] = json.loads(company_result.content[0].text)
            
            # Research each competitor
            for competitor in competitors:
                comp_result = await session.call_tool("web_batch_search", {
                    "queries": [
                        f"{competitor} vs {company}",
                        f"{competitor} market share",
                        f"{competitor} recent news"
                    ],
                    "max_results": 5
                })
                results["competitors"][competitor] = json.loads(comp_result.content[0].text)
            
            return results
```

---

## Building Agentic Applications

### Pattern 1: Simple Research Agent

```python
class SimpleResearchAgent:
    def __init__(self, server_url: str = "http://localhost:8765"):
        self.server_url = server_url
    
    async def research(self, question: str) -> str:
        async with sse_client(f"{self.server_url}/sse") as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("deep_research", {
                    "question": question,
                    "report_type": "advanced"
                })
                return json.loads(result.content[0].text)["report"]

# Usage
agent = SimpleResearchAgent()
report = asyncio.run(agent.research("Explain blockchain technology"))
```

### Pattern 2: Multi-Tool Agent

```python
class MultiToolResearchAgent:
    def __init__(self, server_url: str = "http://localhost:8765"):
        self.server_url = server_url
        self.session = None
    
    async def connect(self):
        self._context = sse_client(f"{self.server_url}/sse")
        self.read, self.write = await self._context.__aenter__()
        self._session_context = ClientSession(self.read, self.write)
        self.session = await self._session_context.__aenter__()
        await self.session.initialize()
    
    async def disconnect(self):
        if self.session:
            await self._session_context.__aexit__(None, None, None)
            await self._context.__aexit__(None, None, None)
    
    async def search(self, queries: list) -> dict:
        result = await self.session.call_tool("web_batch_search", {
            "queries": queries,
            "max_results": 5
        })
        return json.loads(result.content[0].text)
    
    async def scrape(self, urls: list, query: str = "") -> dict:
        result = await self.session.call_tool("web_scrape", {
            "urls": urls,
            "query": query
        })
        return json.loads(result.content[0].text)
    
    async def deep_research(self, question: str) -> dict:
        result = await self.session.call_tool("deep_research", {
            "question": question,
            "report_type": "advanced"
        })
        return json.loads(result.content[0].text)

# Usage
async def main():
    agent = MultiToolResearchAgent()
    await agent.connect()
    
    try:
        # Step 1: Quick search
        search_results = await agent.search(["AI trends 2025"])
        
        # Step 2: Deep dive on interesting URLs
        urls = [r["url"] for r in search_results["results"][0]["results"][:3]]
        content = await agent.scrape(urls, "AI trends")
        
        # Step 3: Comprehensive research
        report = await agent.deep_research("What are the key AI trends for 2025?")
        
        print(report["report"])
    finally:
        await agent.disconnect()

asyncio.run(main())
```

### Pattern 3: Parallel Research Agent

```python
import asyncio

class ParallelResearchAgent:
    def __init__(self, server_url: str, max_concurrent: int = 3):
        self.server_url = server_url
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _research_one(self, question: str) -> dict:
        async with self.semaphore:
            async with sse_client(f"{self.server_url}/sse") as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool("deep_research", {
                        "question": question,
                        "report_type": "basic"
                    })
                    return {
                        "question": question,
                        "result": json.loads(result.content[0].text)
                    }
    
    async def research_batch(self, questions: list) -> list:
        tasks = [self._research_one(q) for q in questions]
        return await asyncio.gather(*tasks, return_exceptions=True)

# Usage
agent = ParallelResearchAgent("http://localhost:8765")
questions = [
    "What is machine learning?",
    "What is deep learning?",
    "What is reinforcement learning?"
]
results = asyncio.run(agent.research_batch(questions))
```

---

## Working with Results

### Extracting Report Content

```python
result = await session.call_tool("deep_research", {...})
data = json.loads(result.content[0].text)

# Get the full report
report = data["report"]

# Get metadata
duration = data["metadata"]["duration_seconds"]
turns = data["metadata"]["turns"]

# Get sources
urls = data["sources"]["visited_urls"]
queries = data["sources"]["search_queries"]
```

### Processing Search Results

```python
result = await session.call_tool("web_batch_search", {...})
data = json.loads(result.content[0].text)

# Iterate through results
for query_result in data["results"]:
    print(f"Query: {query_result['query']}")
    for item in query_result["results"]:
        print(f"  - {item['title']}: {item['url']}")
```

### Handling Scraped Content

```python
result = await session.call_tool("web_scrape", {...})
data = json.loads(result.content[0].text)

# Check success rate
successful = data["successful"]
total = data["total_urls"]
print(f"Scraped {successful}/{total} URLs successfully")

# Process results
for item in data["results"]:
    if item["success"]:
        print(f"Title: {item['title']}")
        print(f"Content: {item['content'][:500]}...")
    else:
        print(f"Failed: {item['url']} - {item.get('error', 'Unknown error')}")
```

### Error Handling

```python
result = await session.call_tool("deep_research", {...})
data = json.loads(result.content[0].text)

if "error" in data:
    print(f"Research failed: {data['error']}")
    print(f"Duration before failure: {data['metadata']['duration_seconds']}s")
else:
    print("Research completed successfully")
    print(data["report"])
```

---

## Configuration & Tuning

### Search Provider Selection

| Provider | Pros | Cons | API Key Required |
|----------|------|------|------------------|
| `duckduckgo` | Free, no API key | Rate limits, less reliable | No |
| `tavily` | High quality, reliable | Paid service | Yes |
| `serpapi` | Google results | Paid service | Yes |
| `jina` | Good for technical content | Paid service | Yes |

### Performance Tuning

**For faster results:**
```python
await session.call_tool("configure_research", {
    "max_search_results": 3,
    "max_search_queries": 1,
    "max_urls_to_visit": 2
})
```

**For more thorough research:**
```python
await session.call_tool("configure_research", {
    "max_search_results": 10,
    "max_search_queries": 3,
    "max_urls_to_visit": 5
})
```

### Embedding Compression

When `COMPRESS_EMBEDDING_MODEL` is configured:
- Content is filtered to semantically relevant sections
- Reduces token usage for LLM processing
- Improves research quality by focusing on relevant content

**Recommended settings:**
```bash
export COMPRESS_EMBEDDING_MODEL="BAAI/bge-m3"
export COMPRESS_SIMILARITY_THRESHOLD="0.30"
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection refused | Server not running | Start the MCP server |
| Empty search results | Search provider issues | Try different provider |
| Slow research | Too many URLs/queries | Reduce limits with `configure_research` |
| Content extraction fails | Website blocking | Try different scraper provider |
| Report generation fails | LLM API issues | Check `OPENAI_BASE_URL` and API key |

### Debug Checklist

1. **Check server status:**
   ```python
   result = await session.call_tool("get_server_status", {})
   print(json.loads(result.content[0].text))
   ```

2. **Verify API keys:**
   ```bash
   echo $OPENAI_API_KEY
   echo $OPENAI_BASE_URL
   ```

3. **Test search provider:**
   ```python
   result = await session.call_tool("web_batch_search", {
       "queries": ["test query"],
       "max_results": 1
   })
   ```

4. **Check logs:**
   ```bash
   # Start server with debug logging
   uv run python mcp/enhanced_server.py --transport sse --log-level DEBUG
   ```

### Getting Help

- Check the server logs for detailed error messages
- Verify environment variables are set correctly
- Test individual tools before building complex workflows
- Use `get_server_status` to verify configuration

---

## Quick Reference

### Tool Summary

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `deep_research` | Autonomous research | `question`, `report_type` |
| `web_batch_search` | Multi-query search | `queries`, `max_results` |
| `web_search` | Alias for batch search | Same as above |
| `web_scrape` | Content extraction | `urls`, `query` |
| `web_visit_compress` | Research-focused scraping | `urls`, `query` |
| `configure_research` | Runtime configuration | Various limits |
| `get_server_status` | Health check | None |

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENAI_API_KEY` | LLM authentication | Required |
| `OPENAI_BASE_URL` | LLM endpoint | `http://localhost:4000` |
| `SEARCH_PROVIDER` | Search backend | `duckduckgo` |
| `SCRAPER_PROVIDER` | Scraping backend | `firecrawl` |
| `COMPRESS_EMBEDDING_MODEL` | Content compression | Optional |
| `DEEP_RESEARCH_TIMEOUT` | Timeout for deep research in seconds | `600` |
| `MAX_CONCURRENT_BROWSER_SCRAPES` | Max concurrent browser scrape operations | `5` |

### Concurrency Configuration

The server includes built-in protections against resource exhaustion when handling multiple concurrent research sessions:

**Deep Research Timeout** (`DEEP_RESEARCH_TIMEOUT`):
- Default: 600 seconds (10 minutes)
- Prevents research sessions from running indefinitely
- Returns a timeout error if exceeded

**Browser Scrape Limiting** (`MAX_CONCURRENT_BROWSER_SCRAPES`):
- Default: 5 concurrent browser instances
- Prevents resource exhaustion from too many browser processes
- Additional scrape requests queue until a slot is available

Example configuration for high-concurrency environments:

```bash
# Allow longer research sessions
export DEEP_RESEARCH_TIMEOUT=900  # 15 minutes

# Allow more concurrent browser scrapes
export MAX_CONCURRENT_BROWSER_SCRAPES=10
```

---

*For architecture details and advanced integration patterns, see the [Developer's Guide](DEVELOPERS_GUIDE.md).*


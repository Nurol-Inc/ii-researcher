# MCP Server Guide

Guide for running and using the II-Researcher MCP server (deep research over Model Context Protocol).

## Overview

The MCP server exposes:

- **deep_research** – Multi-step research with web search and report generation
- **web_batch_search** – Batch web search
- **web_scrape** / **web_visit_compress** – Content extraction
- **configure_research** – Runtime limits
- **get_server_status** – Health and config check

Transports: **stdio** (e.g. Claude Desktop) or **SSE/HTTP** (browser, scripts).

## Quick Start

### Run server (SSE, port 8765)

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="http://localhost:4000"
export SEARCH_PROVIDER=duckduckgo
export SCRAPER_PROVIDER=bs
uv run python mcp/enhanced_server.py --transport sse --port 8765
```

### Run with Docker (MCP only)

```bash
# env.test or .env must set OPENAI_BASE_URL (and OPENAI_API_KEY if required)
docker compose -f docker-compose-mcp.yml up -d
# SSE: http://localhost:8765
```

**Docker requirement:** The LLM API must be reachable at `OPENAI_BASE_URL`. If the API runs on the host, use `http://host.docker.internal:<port>/v1` so the container can reach it.

### CLI research client

```bash
python mcp/research_client.py "Your question?" --type advanced --server http://localhost:8765
```

## Browser GUI (mcp-gui.html)

Open `mcp/mcp-gui.html` in a browser. Set the MCP server URL (e.g. `http://server:8765`), enter a question, choose report type, and run. The GUI:

- Uses a single SSE connection for the session (avoids invalid session and disconnect errors)
- Shows **turnaround time** (end-to-end) and server duration in the result

Serve the file over HTTP if needed to avoid CORS (e.g. `python -m http.server 8080` in the repo root, then open `http://localhost:8080/mcp/mcp-gui.html`).

## Configuration

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENAI_API_KEY` | LLM auth | Required |
| `OPENAI_BASE_URL` | LLM endpoint | `http://localhost:4000` |
| `SEARCH_PROVIDER` | duckduckgo, tavily, serpapi, jina | duckduckgo |
| `SCRAPER_PROVIDER` | bs, firecrawl, browser, jina | firecrawl |
| `DEEP_RESEARCH_TIMEOUT` | Timeout (seconds) | 600 |
| `MAX_CONCURRENT_BROWSER_SCRAPES` | Max concurrent browser scrapes | 5 |

For Docker, use `host.docker.internal` in `OPENAI_BASE_URL` to reach an LLM on the host.

## Tools summary

| Tool | Purpose |
|------|---------|
| `deep_research` | Autonomous research; params: `question`, `report_type` (basic/advanced) |
| `web_batch_search` | Multi-query search; params: `queries`, `max_results` |
| `web_scrape` | Extract content from URLs |
| `web_visit_compress` | Research-focused scrape with compression |
| `configure_research` | Set limits (e.g. max URLs, queries) |
| `get_server_status` | Health and config |

## Troubleshooting

| Issue | Cause | Action |
|-------|--------|--------|
| Connection refused (LLM) | API not reachable at `OPENAI_BASE_URL` | Start API; from Docker use `host.docker.internal:<port>` in `OPENAI_BASE_URL` |
| Invalid session ID / 400 | Client sent session_id with trailing slash | Use current mcp-gui.html (single SSE, no trailing slash on message URL) |
| ClosedResourceError / 500 | Client closed SSE before response | Use single SSE connection (do not close after endpoint event) |
| Slow or timeout | Large research or network | Increase `DEEP_RESEARCH_TIMEOUT`; check search/scraper providers |

Server logs: `docker compose -f docker-compose-mcp.yml logs` (or run the server in the foreground with `--log-level DEBUG`).

# II-Researcher MCP

MCP server and clients for deep research. **Full guide:** [docs/guides/MCP.md](../docs/guides/MCP.md) (quick start, Docker, browser GUI, config, troubleshooting).

## Research client (CLI)

Command-line client for deep research. Start the MCP server first (see [docs/guides/MCP.md](../docs/guides/MCP.md)):

```bash
# Example: run server
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="http://localhost:4000"
export SEARCH_PROVIDER=duckduckgo
export SCRAPER_PROVIDER=bs
uv run python mcp/enhanced_server.py --transport sse --port 8765
```

Then run research:

```bash
# Basic usage - advanced report (default)
python mcp/research_client.py "What is quantum computing?"

# Basic report type
python mcp/research_client.py "Machine learning basics" --type basic

# Custom server URL
python mcp/research_client.py "AI ethics" --server http://localhost:8765

# JSON output for scripting
python mcp/research_client.py "Python programming" --json > results.json
```

## Command Line Options

```
usage: research_client.py [-h] [--question QUESTION] [--type {basic,advanced}]
                         [--server SERVER_URL] [--timeout TIMEOUT] [--json]
                         [question]

II-Researcher MCP Client - Perform deep research queries

positional arguments:
  question              Research question (can also use --question)

optional arguments:
  -h, --help            show this help message and exit
  --question QUESTION, -q QUESTION
                        Research question
  --type {basic,advanced}, --report-type {basic,advanced}
                        Report type (default: advanced)
  --server SERVER_URL, --server-url SERVER_URL
                        MCP server URL (default: http://localhost:8765)
  --timeout TIMEOUT     Timeout in seconds (default: 300)
  --json                Output results as JSON instead of formatted text
```

## Examples

### Basic Research

```bash
python mcp/research_client.py "What are the latest developments in renewable energy?"
```

### Technical Deep Dive

```bash
python mcp/research_client.py "How do transformers work in deep learning?" --type advanced
```

### Quick Overview

```bash
python mcp/research_client.py "Blockchain technology explained" --type basic
```

### Custom Server

```bash
python mcp/research_client.py "Climate change solutions" --server http://my-server.com:8765
```

### JSON Output for Automation

```bash
python mcp/research_client.py "Machine learning algorithms" --json | jq '.report' > report.md
```

### Scripting with Results

```bash
# Save results to file
python mcp/research_client.py "Quantum physics basics" --json > quantum_research.json

# Extract just the report content
python mcp/research_client.py "AI safety" --json | jq -r '.report' > ai_safety_report.md

# Get metadata only
python mcp/research_client.py "Robotics trends" --json | jq '.metadata'
```

## Environment Variables

- `MCP_SERVER_URL`: Default server URL (overrides `--server` default)

## Output Format

The client provides formatted output by default with:

- ✅ Research completion status
- 📊 Metadata (duration, research turns, timestamp)
- 🔗 Sources (search queries, URLs visited)
- 📄 Full research report with proper formatting

For automation, use `--json` flag to get structured data:

```json
{
  "report": "Full research report content...",
  "sources": {
    "visited_urls": ["url1", "url2"],
    "search_queries": ["query1", "query2"]
  },
  "metadata": {
    "question": "Research question",
    "report_type": "advanced",
    "duration_seconds": 45.2,
    "turns": 3,
    "timestamp": "2025-12-24T23:33:33.294257"
  },
  "client_metadata": {
    "server_url": "http://localhost:8765",
    "execution_time_seconds": 45.2,
    "timestamp": "2025-12-24T23:33:33.294257"
  }
}
```

## Error Handling

The client handles common errors gracefully:

- Server connection issues
- Timeout errors
- Invalid parameters
- Research failures

All errors are clearly displayed with helpful messages.

# II-Researcher Architecture Documentation

## Overview

II-Researcher is a powerful deep search agent system that performs intelligent web searches and generates comprehensive answers. The application follows a microservices architecture with multiple components that can run independently or together.

## System Architecture Diagram

```
┌────────────────────────────────────────────────────────────┐
│                         Client Layer                       │
├────────────────────────────────────────────────────────────┤
│  Web Browser  │  CLI Tool  │  MCP Client (Claude Desktop)  │
└────────┬──────┴──────┬─────┴────────────┬──────────────────┘
         │             │                  │
         │             │                  │
┌────────▼─────────────▼──────────────────▼──────────────────┐
│                      Service Layer                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Frontend   │  │  API Server  │  │  MCP Server  │      │
│  │   (Next.js)  │  │  (FastAPI)   │  │   (FastMCP)  │      │
│  │   Port 3000  │  │  Port 8000   │  │   Stdio/HTTP │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │              │
│         └─────────────────┴─────────────────┘              │
│                           │                                │
└───────────────────────────┼────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────┐
│                   Core Application Layer                   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Reasoning Agent (Core Engine)             │   │
│  │  • Multi-step reasoning                             │   │
│  │  • Reflection and analysis                          │   │
│  │  • Question decomposition                           │   │
│  │  • Report generation                                │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                  │
│  ┌──────────────────────▼─────────────────────────────┐    │
│  │              Tool Clients Layer                    │    │
│  │  ┌────────────────┐  ┌──────────────────┐          │    │
│  │  │ Search Client  │  │  Scraper Client  │          │    │
│  │  │ • Tavily       │  │  • Firecrawl     │          │    │
│  │  │ • SerpAPI      │  │  • BeautifulSoup │          │    │
│  │  │ • DuckDuckGo   │  │  • Browser       │          │    │
│  │  └────────────────┘  └──────────────────┘          │    │
│  │  ┌────────────────┐                                │    │
│  │  │   Compressor   │                                │    │
│  │  │ • Embedding    │                                │    │
│  │  │ • LLM-based    │                                │    │
│  │  └────────────────┘                                │    │
│  └────────────────────────────────────────────────────┘    │
│                                                            │
└────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│                    External Services Layer                 │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  LLM APIs    │  │ Search APIs  │  │ Scraper APIs │      │
│  │  • OpenAI    │  │ • Tavily     │  │ • Firecrawl  │      │
│  │  • DeepSeek  │  │ • SerpAPI    │  │ • Browser    │      │
│  │  • Custom    │  │ • DuckDuckGo │  │ • BS4        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                │              │
│         ▼                  ▼                ▼              │
│  ┌──────────────────────────────────────────────────┐      │
│  │         External Service Providers               │      │
│  │  • OpenAI API (gpt-4o, gpt-4o-mini)              │      │
│  │  • DeepSeek (deepseek-reasoner, deepseek-chat)   │      │
│  │  • OpenRouter (multi-model access)               │      │
│  │  • Custom LLM endpoints (OpenAI-compatible)      │      │
│  └──────────────────────────────────────────────────┘      │
│                                                            │
│  Note: LiteLLM or other LLM proxies can be run             │
│        separately and accessed via OPENAI_BASE_URL         │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend Service (Next.js)

**Technology:** Next.js 15.2.0 with React 19
**Port:** 3000
**Purpose:** Web-based user interface for the research agent

**Key Features:**
- Modern, responsive UI with dark/light theme support
- Real-time streaming of research results via Server-Sent Events (SSE)
- Interactive question input and answer display
- Built with Tailwind CSS and Radix UI components

**Dependencies:**
- Node.js 18+
- React 19
- Next.js 15.2.0
- Various UI libraries (Radix UI, Framer Motion, etc.)

**Communication:**
- Communicates with API Server via HTTP REST API
- Endpoint: `http://api:8000/search` (in Docker) or `http://localhost:8000/search` (local)

---

### 2. API Server (FastAPI)

**Technology:** FastAPI with Python 3.10+
**Port:** 8000
**Purpose:** RESTful API backend that orchestrates the research process

**Key Features:**
- Streaming endpoint (`/search`) for real-time research updates
- Server-Sent Events (SSE) support for live progress updates
- Asynchronous request handling
- CORS-enabled for cross-origin requests

**Dependencies:**
- FastAPI >= 0.100.0
- Uvicorn >= 0.29.0
- ii-researcher core package
- All Python dependencies from pyproject.toml

**Communication:**
- Accepts HTTP GET requests from Frontend
- Connects to LLM services via OpenAI-compatible API (configurable via OPENAI_BASE_URL)
- Uses ReasoningAgent from core layer

**Main Endpoint:**
```
GET /search?question=<query>&max_steps=<int>
Returns: text/event-stream (SSE)
```

---

### 3. MCP Server (Model Context Protocol)

**Technology:** FastMCP with Python 3.10+
**Port:** Stdio (default) or HTTP (8765)
**Purpose:** Integration with Claude Desktop and other MCP clients

**Key Features:**
- Exposes research capabilities as MCP tools
- Supports stdio and HTTP/SSE transports
- Integrated with Claude Desktop via `mcp install` command
- Can be used programmatically via MCP clients

**Dependencies:**
- mcp >= 1.1.0
- ii-researcher core package
- python-dotenv >= 1.0.0

**Communication:**
- Stdio mode: Direct communication with Claude Desktop
- HTTP mode: Server-Sent Events on configurable port
- Uses ReasoningAgent from core layer

**Available Tools:**
- `search(question: str) -> str`: Performs comprehensive web research

**Scripts:**
- `mcp/server.py`: Basic MCP server implementation
- `mcp/enhanced_server.py`: Enhanced server with additional features
- `mcp/run_server.sh`: Startup script with configuration

---

### 4. Core Application Layer (ii_researcher)

**Technology:** Python 3.10+
**Purpose:** Core research engine and business logic

**Main Components:**

#### a. Reasoning Agent (`ii_researcher.reasoning.agent`)
- Orchestrates the entire research process
- Implements multi-step reasoning workflow
- Handles question analysis and decomposition
- Generates comprehensive reports with references

#### b. Tool Clients (`ii_researcher.tool_clients`)

**Search Client** (`search_client.py`):
- Tavily Search API integration
- SerpAPI integration
- DuckDuckGo search (free, no API key)
- Configurable via `SEARCH_PROVIDER` environment variable

**Scraper Client** (`scrape_client.py`):
- Firecrawl API integration (premium)
- BeautifulSoup scraper (free)
- Browser-based scraping
- Tavily extract
- Configurable via `SCRAPER_PROVIDER` environment variable

**Compressor** (`tool_clients/compressor`):
- Embedding-based content compression
- LLM-based content compression (optional)
- Reduces context size for better performance
- Configurable thresholds and models

#### c. Configuration (`config.py`)
- Environment variable management
- Provider selection
- Timeout and performance settings
- Model configuration

#### d. CLI (`cli.py`)
- Command-line interface for direct usage
- Streaming output support
- Standalone research execution

**Key Dependencies:**
- baml-py == 0.77.0 (Structured outputs)
- pydantic >= 2.0.0 (Data validation)
- langchain-community >= 0.3.18 (Tool integrations)

---

## Service Communication Flow

### Web Interface Flow:
```
User Input → Frontend (3000) → API Server (8000) → ReasoningAgent
                                       ↓
                                  LLM APIs → External LLMs
                                       ↓
                              Search/Scraper APIs
                                       ↓
Frontend ← SSE Stream ← API Server ← ReasoningAgent ← Results
```

### CLI Flow:
```
CLI Command → ReasoningAgent → LLM APIs → External LLMs
                    ↓
              Search/Scraper APIs
                    ↓
           Console Output ← Results
```

### MCP Flow:
```
Claude Desktop → MCP Server (stdio) → ReasoningAgent
                                           ↓
                                    LLM APIs → External LLMs
                                           ↓
                                   Search/Scraper APIs
                                           ↓
Claude Desktop ← MCP Response ← ReasoningAgent ← Results
```

---

## Service Dependencies

### Startup Order for Full Stack:
1. **API Server** (8000) - Core backend service
2. **Frontend** (3000) - Depends on API Server
3. **MCP Server** (optional) - Independent of Frontend/API

**Note:** External LLM service (e.g., LiteLLM, OpenAI API) must be accessible before starting services.

### Service Independence:
- **CLI Tool**: Can run standalone with direct LLM access
- **MCP Server**: Can run independently from Frontend/API
- **Frontend + API**: Can run without MCP server
- **LLM Services**: Run externally (OpenAI API, LiteLLM proxy, or custom endpoints)

---

## Configuration & Environment Variables

### Core Configuration:
```bash
# LLM Configuration
OPENAI_API_KEY          # OpenAI API key
OPENAI_BASE_URL         # LLM API URL (e.g., http://localhost:4000 for LiteLLM, or https://api.openai.com/v1)

# Search Provider Selection
SEARCH_PROVIDER         # Options: 'serpapi' | 'tavily' | 'duckduckgo'
TAVILY_API_KEY          # Required if using Tavily
SERPAPI_API_KEY         # Required if using SerpAPI

# Scraper Provider Selection
SCRAPER_PROVIDER        # Options: 'firecrawl' | 'bs' | 'browser' | 'tavily_extract'
FIRECRAWL_API_KEY       # Required if using Firecrawl

# Compression Configuration
COMPRESS_EMBEDDING_MODEL      # Embedding model for compression
COMPRESS_SIMILARITY_THRESHOLD # Similarity threshold (0.0-1.0)
COMPRESS_MAX_OUTPUT_WORDS     # Max output words
COMPRESS_MAX_INPUT_WORDS      # Max input words
USE_LLM_COMPRESSOR           # Enable LLM-based compression

# Timeout Settings
SEARCH_PROCESS_TIMEOUT  # Search process timeout (seconds)
SEARCH_QUERY_TIMEOUT    # Query timeout (seconds)
SCRAPE_URL_TIMEOUT      # URL scraping timeout (seconds)
STEP_SLEEP              # Sleep between steps (milliseconds)

# Model Configuration (Pipeline mode)
STRATEGIC_LLM           # Model for strategic decisions
SMART_LLM               # Model for general tasks
FAST_LLM                # Model for compression

# Reasoning Model Configuration
R_MODEL                 # Reasoning model (e.g., deepseek-reasoner)
R_TEMPERATURE           # Temperature for reasoning
R_REPORT_MODEL          # Model for report generation
R_PRESENCE_PENALTY      # Presence penalty for reasoning
```

---

## Deployment Modes

### 1. Local Development
- All services run separately on host machine
- Manual startup of each service
- Direct access to all ports

### 2. Docker Compose (Unified Container)
- Single container with all project services (frontend, API, MCP)
- Automatic service orchestration
- Reduced resource overhead
- External LLM services (OpenAI API, LiteLLM if needed) run separately

### 3. Docker Compose (Planned - Unified Container)
- Single container with all services
- Selective service launching via entrypoint
- Reduced resource overhead for testing

### 4. CLI Only
- No web services required
- Direct Python execution
- Minimal resource usage

### 5. MCP Only
- MCP server for Claude Desktop integration
- No web interface needed
- Stdio or HTTP transport

---

## Data Flow

### Research Process Flow:
1. **Question Input**: User submits research question
2. **Question Analysis**: Agent analyzes and decomposes question
3. **Search Planning**: Generates search queries
4. **Web Search**: Executes searches via search provider
5. **Content Scraping**: Extracts content from URLs
6. **Content Compression**: Reduces content size while preserving relevance
7. **Reasoning**: Multi-step analysis and reasoning
8. **Report Generation**: Synthesizes final comprehensive answer
9. **Result Streaming**: Streams progress and final result to client

### Data Storage:
- **No persistent database**: Stateless design
- **In-memory processing**: All data processed in memory
- **No caching**: Each research query is fresh (can be added as enhancement)

---

## Security Considerations

### API Keys:
- All API keys passed via environment variables
- Never committed to version control
- Required keys depend on provider selection

### Network:
- CORS enabled on API server (currently allows all origins)
- Service-to-service communication in Docker network
- External API calls to search/scraper providers

### Recommendations:
- Use environment variable management tools (e.g., .env files)
- Restrict CORS origins in production
- Implement rate limiting for public deployments
- Use secrets management for production deployments

---

## Performance Characteristics

### Scalability:
- **Horizontal**: Each service can be scaled independently
- **Vertical**: Benefits from more CPU/memory for LLM processing
- **Async Design**: FastAPI handles multiple concurrent requests

### Resource Usage:
- **API Server**: ~200-300MB RAM (base)
- **Frontend**: ~50-100MB RAM (base)
- **MCP Server**: ~100-200MB RAM (base)
- **CLI Tool**: ~100-150MB RAM (base)

**Note:** External LLM services (OpenAI API, LiteLLM, etc.) have separate resource requirements.

### Bottlenecks:
- External API rate limits (search, scraper, LLM)
- LLM inference time
- Network latency for content scraping

---

## Monitoring & Logging

### Current Logging:
- Python logging framework (INFO level)
- Console output for all services
- Docker logs accessible via `docker compose logs`

### Recommended Additions:
- Structured logging (JSON format)
- Centralized log aggregation
- Performance metrics
- Error tracking
- Request tracing

---

## Testing

### Test Structure:
- Unit tests in `tests/` directory
- GitHub Actions CI pipeline
- Linting with flake8
- Test framework: pytest with pytest-asyncio

### CI/CD:
- **Test workflow**: Runs on push to main and PRs
- **Release workflow**: Publishes to PyPI on git tags
- **Versioning**: Based on git tags and pyproject.toml

---

## Future Enhancements

### Potential Improvements:
1. **Caching Layer**: Redis for search results and scraped content
2. **Database**: PostgreSQL for research history
3. **Authentication**: User management and API keys
4. **Rate Limiting**: Request throttling and quotas
5. **Observability**: Metrics, tracing, and monitoring
6. **Multi-tenancy**: Support for multiple users/organizations
7. **Result Persistence**: Save and retrieve past research
8. **Advanced Reasoning**: More sophisticated reasoning algorithms
9. **Plugin System**: Extensible tool integration

---

## Version Information

- **Current Version**: 0.1.5 (from pyproject.toml)
- **Python Version**: 3.10+
- **License**: See LICENSE file
- **Repository**: https://github.com/Intelligent-Internet/ii-researcher

---

## Support & Documentation

- **Main README**: `/README.md`
- **MCP User Guide**: `/mcp/USERS_GUIDE.md`
- **MCP Developer Guide**: `/mcp/DEVELOPERS_GUIDE.md`
- **Blog Post**: https://www.ii.inc/web/blog/post/ii-researcher
- **Issues**: GitHub Issues

---

*Last Updated: 2026-01-22*

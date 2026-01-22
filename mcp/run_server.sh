#!/bin/bash
# II-Researcher MCP Server Startup Script
#
# Usage:
#   ./run_server.sh              # Start with stdio transport 
#   ./run_server.sh http         # Start with HTTP transport on port 8765
#   ./run_server.sh http 9000    # Start with HTTP transport on custom port
#
# After starting the server, you can use the research client:
#   python mcp/research_client.py "Your research question here"

set -e

# Navigate to the ii-researcher directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# ============================================================================
# CONFIGURATION - Modify these for your setup
# ============================================================================

# LLM Configuration
export OPENAI_API_KEY="${OPENAI_API_KEY:-empty}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-http://192.168.10.86:8000/v1}"
export R_MODEL="${R_MODEL:-openai/gpt-oss-120b}"
export R_REPORT_MODEL="${R_REPORT_MODEL:-openai/gpt-oss-120b}"
export R_TEMPERATURE="${R_TEMPERATURE:-0.2}"

# Embedding Configuration
export EMBEDDING_BASE_URL="${EMBEDDING_BASE_URL:-http://192.168.10.86:8001/v1}"
export COMPRESS_EMBEDDING_MODEL="${COMPRESS_EMBEDDING_MODEL:-BAAI/bge-m3}"
export COMPRESS_SIMILARITY_THRESHOLD="${COMPRESS_SIMILARITY_THRESHOLD:-0.30}"

# Search Configuration
export SEARCH_PROVIDER="${SEARCH_PROVIDER:-duckduckgo}"

# Scraper Configuration  
export SCRAPER_PROVIDER="${SCRAPER_PROVIDER:-bs}"

# Optional API Keys (only needed if using specific providers)
# export TAVILY_API_KEY="your-tavily-key"
# export SERPAPI_API_KEY="your-serpapi-key"
# export JINA_API_KEY="your-jina-key"
# export FIRECRAWL_API_KEY="your-firecrawl-key"

# Compression settings
export USE_LLM_COMPRESSOR="${USE_LLM_COMPRESSOR:-false}"

# ============================================================================
# START SERVER
# ============================================================================

TRANSPORT="${1:-stdio}"
PORT="${2:-8765}"

echo "=============================================="
echo "II-Researcher MCP Server"
echo "=============================================="
echo "Transport: $TRANSPORT"
echo "LLM Base URL: $OPENAI_BASE_URL"
echo "LLM Model: $R_MODEL"
echo "Report Model: $R_REPORT_MODEL"
echo "Search Provider: $SEARCH_PROVIDER"
echo "Scraper Provider: $SCRAPER_PROVIDER"
echo "=============================================="

if [ "$TRANSPORT" = "http" ]; then
    echo "Starting HTTP server on port $PORT..."
    python3 mcp/enhanced_server.py --transport sse --port "$PORT" --log-level INFO
else
    echo "Starting stdio server ..."
    python3 mcp/enhanced_server.py --transport stdio --log-level INFO
fi


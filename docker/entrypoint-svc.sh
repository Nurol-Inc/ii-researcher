#!/bin/bash
# Service Layer Entrypoint
# Launches API or MCP services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to start API service
start_api() {
    log_info "Starting API service on port 8000..."
    cd /app
    exec python api.py
}

# Function to start MCP service
start_mcp() {
    log_info "Starting MCP service..."
    
    local transport="${MCP_TRANSPORT:-stdio}"
    local port="${MCP_PORT:-8765}"
    
    cd /app
    if [ "$transport" = "http" ]; then
        log_info "Starting MCP server in HTTP mode on port $port..."
        exec python mcp/enhanced_server.py --transport sse --port "$port" --log-level INFO
    else
        log_info "Starting MCP server in stdio mode..."
        exec python mcp/server.py
    fi
}

# Function to start CLI
start_cli() {
    log_info "Starting CLI mode..."
    
    if [ -z "$RESEARCH_QUESTION" ]; then
        log_error "RESEARCH_QUESTION environment variable is required for CLI mode"
        exit 1
    fi
    
    cd /app
    exec python ii_researcher/cli.py --question "$RESEARCH_QUESTION" --stream
}

# Main execution
main() {
    log_section "II-Researcher Service Layer Starting"
    
    local mode="${1:-${SERVICE_MODE:-api}}"
    
    log_info "Service Mode: $mode"
    log_info "Search Provider: ${SEARCH_PROVIDER:-serpapi}"
    log_info "Scraper Provider: ${SCRAPER_PROVIDER:-firecrawl}"
    echo ""
    
    case "$mode" in
        api)
            log_info "Starting API Server"
            start_api
            ;;
        
        mcp)
            log_info "Starting MCP Server"
            start_mcp
            ;;
        
        cli)
            log_info "Starting CLI"
            start_cli
            ;;
        
        bash|sh|shell)
            log_info "Starting interactive shell"
            exec /bin/bash
            ;;
        
        *)
            log_error "Unknown service mode: $mode"
            log_info "Available modes:"
            log_info "  api              - Start API server (default)"
            log_info "  mcp              - Start MCP server"
            log_info "  cli              - Start CLI (requires RESEARCH_QUESTION)"
            log_info "  bash|sh|shell    - Start interactive shell"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

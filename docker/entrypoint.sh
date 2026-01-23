#!/bin/bash
# II-Researcher Entrypoint Script
# Supports selective service launching in a single container

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

# Function to check required environment variables
check_env_vars() {
    local missing_vars=()
    
    # Check for OpenAI API key if not using custom base URL
    if [ -z "$OPENAI_API_KEY" ]; then
        log_warn "OPENAI_API_KEY is not set"
        missing_vars+=("OPENAI_API_KEY")
    fi
    
    # Check search provider configuration
    if [ "$SEARCH_PROVIDER" = "tavily" ] && [ -z "$TAVILY_API_KEY" ]; then
        log_warn "SEARCH_PROVIDER is 'tavily' but TAVILY_API_KEY is not set"
        missing_vars+=("TAVILY_API_KEY")
    fi
    
    if [ "$SEARCH_PROVIDER" = "serpapi" ] && [ -z "$SERPAPI_API_KEY" ]; then
        log_warn "SEARCH_PROVIDER is 'serpapi' but SERPAPI_API_KEY is not set"
        missing_vars+=("SERPAPI_API_KEY")
    fi
    
    # Check scraper provider configuration
    if [ "$SCRAPER_PROVIDER" = "firecrawl" ] && [ -z "$FIRECRAWL_API_KEY" ]; then
        log_warn "SCRAPER_PROVIDER is 'firecrawl' but FIRECRAWL_API_KEY is not set"
        missing_vars+=("FIRECRAWL_API_KEY")
    fi
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_warn "Some environment variables are not set. Services may not work correctly."
        log_warn "Missing: ${missing_vars[*]}"
    fi
}

# Function to display configuration
display_config() {
    log_section "II-Researcher Configuration"
    log_info "Service Mode: ${SERVICE_MODE:-all}"
    log_info "Search Provider: ${SEARCH_PROVIDER:-serpapi}"
    log_info "Scraper Provider: ${SCRAPER_PROVIDER:-firecrawl}"
    log_info "Node Environment: ${NODE_ENV:-production}"
    echo ""
}

# Function to start API service
start_api() {
    log_info "Starting API service on port 8000..."
    
    cd /app
    python api.py &
    API_PID=$!
    log_info "API service started with PID: $API_PID"
}

# Function to start Frontend service
start_frontend() {
    log_info "Starting Frontend service on port 3000..."
    
    # Auto-detect API URL if not set
    if [ -z "$API_URL" ] && [ -z "$NEXT_PUBLIC_API_URL" ]; then
        log_info "API_URL not set, using default: http://localhost:8000"
        export API_URL="http://localhost:8000"
    fi
    
    # For backwards compatibility with NEXT_PUBLIC_API_URL
    if [ ! -z "$NEXT_PUBLIC_API_URL" ] && [ -z "$API_URL" ]; then
        log_info "Using NEXT_PUBLIC_API_URL as API_URL for backwards compatibility"
        export API_URL="$NEXT_PUBLIC_API_URL"
    fi
    
    log_info "Frontend will use API URL: $API_URL"
    
    # Wait for API if it should be running
    if [ "$SERVICE_MODE" = "all" ] || [ "$SERVICE_MODE" = "frontend+api" ]; then
        log_info "Waiting for API to be ready..."
        for i in {1..30}; do
            if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
                log_info "API is ready!"
                break
            fi
            if [ $i -eq 30 ]; then
                log_warn "API health check timeout. Proceeding anyway..."
            fi
            sleep 2
        done
    fi
    
    cd /app/frontend
    PORT=3000 HOSTNAME=0.0.0.0 API_URL="$API_URL" node server.js &
    FRONTEND_PID=$!
    log_info "Frontend service started with PID: $FRONTEND_PID"
}

# Function to start MCP service
start_mcp() {
    log_info "Starting MCP service..."
    
    local transport="${MCP_TRANSPORT:-stdio}"
    local port="${MCP_PORT:-8765}"
    
    cd /app
    if [ "$transport" = "http" ]; then
        log_info "Starting MCP server in HTTP mode on port $port..."
        python mcp/enhanced_server.py --transport sse --port "$port" --log-level INFO &
        MCP_PID=$!
        log_info "MCP service started with PID: $MCP_PID"
    else
        log_info "MCP service requires stdio mode and cannot run in background"
        log_info "Use SERVICE_MODE=mcp with MCP_TRANSPORT=http for background mode"
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
    python ii_researcher/cli.py --question "$RESEARCH_QUESTION" --stream
}

# Function to handle shutdown
shutdown() {
    log_section "Shutting down services"
    
    if [ ! -z "$FRONTEND_PID" ]; then
        log_info "Stopping Frontend (PID: $FRONTEND_PID)..."
        kill -TERM "$FRONTEND_PID" 2>/dev/null || true
    fi
    
    if [ ! -z "$API_PID" ]; then
        log_info "Stopping API (PID: $API_PID)..."
        kill -TERM "$API_PID" 2>/dev/null || true
    fi
    
    if [ ! -z "$MCP_PID" ]; then
        log_info "Stopping MCP (PID: $MCP_PID)..."
        kill -TERM "$MCP_PID" 2>/dev/null || true
    fi
    
    log_info "All services stopped"
    exit 0
}

# Trap signals for graceful shutdown
trap shutdown SIGTERM SIGINT SIGQUIT

# Main execution
main() {
    log_section "II-Researcher Container Starting"
    
    # Display configuration
    display_config
    
    # Check environment variables
    check_env_vars
    
    # Determine service mode from first argument or environment variable
    local mode="${1:-${SERVICE_MODE:-all}}"
    
    log_section "Starting Services: $mode"
    
    case "$mode" in
        all)
            log_info "Starting all services (API + Frontend)"
            start_api
            sleep 3  # Give API time to start
            start_frontend
            ;;
        
        api)
            log_info "Starting API only"
            start_api
            ;;
        
        frontend)
            log_info "Starting Frontend only"
            start_frontend
            ;;
        
        mcp)
            log_info "Starting MCP server only"
            start_mcp
            ;;
        
        cli)
            log_info "Starting CLI mode"
            start_cli
            return  # CLI is foreground, will exit when done
            ;;
        
        supervisor)
            log_info "Starting with supervisord"
            exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
            ;;
        
        bash|sh|shell)
            log_info "Starting interactive shell"
            exec /bin/bash
            ;;
        
        *)
            log_error "Unknown service mode: $mode"
            log_info "Available modes:"
            log_info "  all              - Start all services (default)"
            log_info "  api              - Start API server only"
            log_info "  frontend         - Start Frontend only"
            log_info "  mcp              - Start MCP server only"
            log_info "  cli              - Start CLI (requires RESEARCH_QUESTION env var)"
            log_info "  supervisor       - Start with supervisord"
            log_info "  bash|sh|shell    - Start interactive shell"
            exit 1
            ;;
    esac
    
    # Display service status
    log_section "Service Status"
    if [ ! -z "$API_PID" ]; then
        log_info "✓ API running (PID: $API_PID) on http://localhost:8000"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        log_info "✓ Frontend running (PID: $FRONTEND_PID) on http://localhost:3000"
        log_info "  → API URL configured as: ${API_URL:-http://localhost:8000}"
    fi
    if [ ! -z "$MCP_PID" ]; then
        log_info "✓ MCP running (PID: $MCP_PID)"
    fi
    echo ""
    log_info "Press Ctrl+C to stop all services"
    
    # Wait for all background processes
    wait
}

# Run main function
main "$@"

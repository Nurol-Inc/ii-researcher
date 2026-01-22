# Container Update: Removed LiteLLM

**Date:** 2026-01-22  
**Change:** Removed 3rd-party LiteLLM service from container

---

## What Changed

The Docker container now **only includes services from the ii-researcher project**:

### ✅ Services Included (Project Services Only)
1. **Frontend** (Next.js) - Port 3000
2. **API Server** (FastAPI) - Port 8000  
3. **MCP Server** (FastMCP) - Port 8765
4. **CLI Tool** - On-demand

### ❌ Services Removed (3rd-Party)
- **LiteLLM** - No longer bundled in container

---

## Rationale

- **Separation of Concerns**: 3rd-party services (like LiteLLM) should run separately
- **Flexibility**: Users can choose their own LLM proxy or connect directly to LLM providers
- **Smaller Image**: Reduced container size and complexity
- **Clearer Boundaries**: Container only contains code from this project

---

## How to Use LLM Services

### Option 1: Run LiteLLM Separately (Recommended)

```bash
# Run LiteLLM in a separate container
docker run -d \
  --name litellm \
  -p 4000:4000 \
  -v $(pwd)/litellm_config.yaml:/app/config.yaml \
  -e OPENAI_API_KEY=your-key \
  ghcr.io/berriai/litellm:latest \
  --config /app/config.yaml

# Run ii-researcher with external LiteLLM
docker run -d \
  --name ii-researcher \
  -p 3000:3000 -p 8000:8000 \
  -e OPENAI_BASE_URL=http://litellm:4000 \
  --link litellm \
  nurol/ii-researcher:latest
```

### Option 2: Use Direct LLM API

```bash
# Connect directly to OpenAI or other LLM provider
docker run -d \
  --name ii-researcher \
  -p 3000:3000 -p 8000:8000 \
  -e OPENAI_API_KEY=your-openai-key \
  -e OPENAI_BASE_URL=https://api.openai.com/v1 \
  nurol/ii-researcher:latest
```

### Option 3: Use Local LLM Server

```bash
# Point to your own LLM server
docker run -d \
  --name ii-researcher \
  -p 3000:3000 -p 8000:8000 \
  -e OPENAI_BASE_URL=http://your-llm-server:8000 \
  nurol/ii-researcher:latest
```

---

## File Changes

### Modified Files

1. **docker/Dockerfile**
   - Removed LiteLLM installation
   - Removed litellm config creation
   - Removed port 4000 exposure
   - Removed OPENAI_BASE_URL default

2. **docker/entrypoint.sh**
   - Removed `start_litellm()` function
   - Removed LiteLLM health checks
   - Removed `litellm`, `api+litellm`, `frontend+api` modes
   - Updated service modes to: `all`, `api`, `frontend`, `mcp`, `cli`, `supervisor`, `bash`
   - Removed LiteLLM from shutdown handler

3. **docker/supervisord.conf**
   - Removed LiteLLM program section
   - API and Frontend start directly

4. **docker-compose.yml**
   - Removed port 4000 mapping
   - Updated documentation
   - Added note about running LiteLLM separately

---

## Service Modes (Updated)

| Mode | Services | Ports | Use Case |
|------|----------|-------|----------|
| `all` | Frontend + API | 3000, 8000 | Complete app (default) |
| `api` | API only | 8000 | Backend service |
| `frontend` | Frontend only | 3000 | Web UI |
| `mcp` | MCP server | 8765 (HTTP) | Claude integration |
| `cli` | CLI tool | - | One-off queries |
| `supervisor` | All with supervisord | 3000, 8000 | Production monitoring |
| `bash` | Interactive shell | - | Debugging |

**Removed modes:**
- ❌ `litellm`
- ❌ `api+litellm`
- ❌ `frontend+api` (merged into `all`)

---

## Docker Compose Example with External LiteLLM

```yaml
version: '3.8'

services:
  # LiteLLM service (separate)
  litellm:
    image: ghcr.io/berriai/litellm:latest
    container_name: litellm
    ports:
      - "4000:4000"
    volumes:
      - ./litellm_config.yaml:/app/config.yaml
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    command: --config /app/config.yaml
    restart: unless-stopped

  # II-Researcher (project services only)
  ii-researcher:
    image: nurol/ii-researcher:latest
    container_name: ii-researcher
    ports:
      - "3000:3000"
      - "8000:8000"
    environment:
      - OPENAI_BASE_URL=http://litellm:4000
      - SEARCH_PROVIDER=serpapi
      - SERPAPI_API_KEY=${SERPAPI_API_KEY}
      - SCRAPER_PROVIDER=firecrawl
      - FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
    depends_on:
      - litellm
    restart: unless-stopped
```

---

## Build Command

No changes to build command:

```bash
make build-local    # Build local image
make build-multi    # Build multi-arch
make push           # Build and push
```

---

## Migration Guide

If you were using the old unified container with LiteLLM:

### Before (Old):
```bash
docker run -d \
  -p 3000:3000 -p 8000:8000 -p 4000:4000 \
  --env-file .env \
  nurol/ii-researcher:latest
```

### After (New):
```bash
# Option 1: Run LiteLLM separately
docker run -d --name litellm -p 4000:4000 \
  -e OPENAI_API_KEY=your-key \
  ghcr.io/berriai/litellm:latest

docker run -d --name ii-researcher \
  -p 3000:3000 -p 8000:8000 \
  -e OPENAI_BASE_URL=http://litellm:4000 \
  --link litellm \
  nurol/ii-researcher:latest

# Option 2: Use direct API
docker run -d --name ii-researcher \
  -p 3000:3000 -p 8000:8000 \
  -e OPENAI_BASE_URL=https://api.openai.com/v1 \
  -e OPENAI_API_KEY=your-key \
  nurol/ii-researcher:latest
```

---

## Benefits

1. **Smaller Image**: ~500MB-1GB smaller without LiteLLM dependencies
2. **Faster Builds**: Less dependencies to install
3. **Better Separation**: Clear boundary between project and 3rd-party services
4. **More Flexible**: Choose any LLM provider or proxy
5. **Easier Updates**: Update LiteLLM independently
6. **Resource Efficiency**: Scale services independently

---

## Testing

```bash
# Build
make build-local

# Test with external LiteLLM
docker run -d --name litellm -p 4000:4000 \
  -e OPENAI_API_KEY=your-key \
  ghcr.io/berriai/litellm:latest

docker run -d --name ii-researcher \
  -p 3000:3000 -p 8000:8000 \
  -e OPENAI_BASE_URL=http://litellm:4000 \
  --link litellm \
  nurol/ii-researcher:latest

# Verify
curl http://localhost:4000/health   # LiteLLM
curl http://localhost:8000/docs     # API
curl http://localhost:3000          # Frontend
```

---

## Notes

- The container still requires an LLM service (LiteLLM, OpenAI API, or compatible endpoint)
- Set `OPENAI_BASE_URL` environment variable to point to your LLM service
- For local development, you can run LiteLLM locally or use a cloud API
- The healthcheck now checks API only (port 8000), not LiteLLM

---

*Updated: 2026-01-22*  
*Change Type: Architecture Simplification*  
*Impact: Non-breaking (requires external LLM service)*

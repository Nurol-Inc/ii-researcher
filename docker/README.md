# Docker Build Files for II-Researcher

This directory contains all Docker-related files for building and running II-Researcher containers.

---

## 📦 Docker Images

II-Researcher provides three image options:

### 1. All-in-One Image: `nurol/ii-researcher`
- **Contains:** Frontend + API + MCP + Core
- **Size:** ~2GB
- **Use Case:** Complete application, testing, simple deployments
- **File:** `Dockerfile`

### 2. Service Layer: `nurol/ii-researcher-svc`
- **Contains:** API + MCP + Core (no frontend)
- **Size:** ~900MB-1.1GB
- **Use Case:** Backend services, API deployments
- **File:** `Dockerfile.svc`

### 3. Core Layer: `nurol/ii-researcher-core`
- **Contains:** Reasoning Agent + Tool Clients only
- **Size:** ~800MB-1GB
- **Use Case:** Library usage, base for custom services
- **File:** `Dockerfile.core`

---

## 📁 Files Overview

### Active Dockerfiles

#### `Dockerfile` (All-in-One)
- **Purpose:** Unified container with all services
- **Multi-stage build:** Optimized for amd64 and arm64
- **Includes:** Frontend (Next.js), API (FastAPI), MCP server, Core logic
- **Usage:** `make build-local`

#### `Dockerfile.core` (Core Layer)
- **Purpose:** Foundation layer with core application logic
- **Includes:** Reasoning agent, search client, scraper client, compression
- **Usage:** `make build-core-local`

#### `Dockerfile.svc` (Service Layer)
- **Purpose:** Service layer built on core
- **Includes:** API server, MCP server, Frontend
- **Depends on:** Core layer image
- **Usage:** `make build-svc-local`

### Entrypoint Scripts

#### `entrypoint.sh` (All-in-One)
- **Purpose:** Entrypoint for unified container
- **Features:**
  - Selective service launching
  - Environment validation
  - Multiple service modes
- **Modes:** all, api, frontend, mcp, cli, supervisor, bash

#### `entrypoint-svc.sh` (Service Layer)
- **Purpose:** Entrypoint for service layer
- **Services:** API, MCP, Frontend (no core-only mode)
- **Modes:** all, api, frontend, mcp, cli, supervisor, bash

### Configuration Files

#### `supervisord.conf` (All-in-One)
- **Purpose:** Process management for unified container
- **Manages:** Frontend, API, MCP processes

#### `supervisord-svc.conf` (Service Layer)
- **Purpose:** Process management for service layer
- **Manages:** Frontend, API, MCP processes

### Legacy Files

#### `Dockerfile.api`
- **Status:** ⚠️ Legacy - kept for backward compatibility
- **Use:** Original API-only image (use unified image with `api` mode instead)

---

## 🎯 Service Modes (All-in-One & Service Layer)

| Mode | Services | Ports | Use Case |
|------|----------|-------|----------|
| `all` | Frontend + API + MCP | 3000, 8000, 8765 | Complete stack (default) |
| `api` | API only | 8000 | Scalable API instances |
| `frontend` | Frontend only | 3000 | Separate frontend |
| `mcp` | MCP server | 8765 (HTTP) | Claude Desktop integration |
| `cli` | CLI tool | - | One-off queries |
| `supervisor` | All with supervisord | 3000, 8000, 8765 | Production with monitoring |
| `bash` | Interactive shell | - | Debugging |

---

## 🏗️ Building Images

### Using Makefile (Recommended)

```bash
# From project root

# Build all-in-one image
make build-local

# Build layered architecture
make build-core-local     # Core layer
make build-svc-local      # Service layer (builds core first)
make build-all-local      # All three images

# Multi-arch builds and push
make push                 # All-in-one
make push-core            # Core layer
make push-svc             # Service layer (pushes core first)
make push-all             # All images
```

### Manual Build

```bash
# All-in-One
docker build -f docker/Dockerfile -t nurol/ii-researcher:latest .

# Core Layer
docker build -f docker/Dockerfile.core -t nurol/ii-researcher-core:latest .

# Service Layer (requires core image)
docker build -f docker/Dockerfile.svc \
  --build-arg IMAGE_NAME=nurol/ii-researcher \
  --build-arg IMAGE_VERSION=latest \
  -t nurol/ii-researcher-svc:latest .

# Multi-arch build
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f docker/Dockerfile \
  -t registry.tunnel.xellence.us/nurol/ii-researcher:latest \
  --push \
  .
```

---

## 🚀 Running Containers

### All-in-One Image

```bash
# Run all services (default)
docker run -d \
  --name ii-researcher \
  -p 3000:3000 -p 8000:8000 -p 8765:8765 \
  --env-file .env \
  nurol/ii-researcher:latest

# Run API only
docker run -d \
  --name ii-researcher-api \
  -p 8000:8000 \
  --env-file .env \
  nurol/ii-researcher:latest api

# Run frontend only
docker run -d \
  --name ii-researcher-frontend \
  -p 3000:3000 \
  --env-file .env \
  nurol/ii-researcher:latest frontend

# Run MCP server
docker run -d \
  --name ii-researcher-mcp \
  -p 8765:8765 \
  --env-file .env \
  nurol/ii-researcher:latest mcp

# Run CLI
docker run --rm \
  --env-file .env \
  -e RESEARCH_QUESTION="What is quantum computing?" \
  nurol/ii-researcher:latest cli
```

### Service Layer Image

```bash
# Run all services (API + MCP, no frontend)
docker run -d \
  --name ii-researcher-svc \
  -p 8000:8000 -p 8765:8765 \
  --env-file .env \
  nurol/ii-researcher-svc:latest

# Run API only
docker run -d \
  --name ii-researcher-api \
  -p 8000:8000 \
  --env-file .env \
  nurol/ii-researcher-svc:latest api
```

### Core Layer Image

```bash
# Use as Python library
docker run --rm -it \
  --env-file .env \
  nurol/ii-researcher-core:latest python

# Run CLI
docker run --rm \
  --env-file .env \
  -e RESEARCH_QUESTION="Explain machine learning" \
  nurol/ii-researcher-core:latest
```

---

## 🔧 Environment Variables

See `env.template` in the project root for all available environment variables.

### Required Variables

- `OPENAI_API_KEY`: OpenAI API key (or other LLM provider)
- `SEARCH_PROVIDER`: Search provider (serpapi, tavily, duckduckgo)
- `SCRAPER_PROVIDER`: Scraper provider (firecrawl, bs, browser, tavily_extract)
- API keys for selected providers

### Container-Specific Variables

- `SERVICE_MODE`: Service launch mode (default: all)
- `MCP_TRANSPORT`: MCP transport mode (stdio, http)
- `MCP_PORT`: MCP server port (default: 8765)
- `RESEARCH_QUESTION`: Question for CLI mode
- `OPENAI_BASE_URL`: Custom OpenAI-compatible API endpoint (optional)

---

## 🌐 Port Reference

| Port | Service | Description |
|------|---------|-------------|
| 3000 | Frontend | Next.js web interface |
| 8000 | API | FastAPI backend |
| 8765 | MCP | MCP server (HTTP mode) |

**Note:** Port 4000 (LiteLLM) is no longer used. Run LiteLLM separately if needed.

---

## 🏥 Health Checks

```bash
# Check container health
docker inspect ii-researcher | grep -A 10 Health

# Manual health checks
curl http://localhost:8000/docs    # API
curl http://localhost:8000         # API root
curl http://localhost:3000         # Frontend
```

---

## 📋 Logs

```bash
# View all logs
docker logs -f ii-researcher

# View service-specific logs (supervisor mode)
docker exec ii-researcher tail -f /var/log/ii-researcher/api_stdout.log
docker exec ii-researcher tail -f /var/log/ii-researcher/frontend_stdout.log
docker exec ii-researcher tail -f /var/log/ii-researcher/mcp_stdout.log
```

---

## 🔍 Troubleshooting

### Container exits immediately
```bash
# Check logs for errors
docker logs ii-researcher

# Run in foreground for debugging
docker run --rm -it --env-file .env nurol/ii-researcher:latest

# Start shell for inspection
docker run --rm -it --env-file .env nurol/ii-researcher:latest bash
```

### Services not accessible
```bash
# Check if services are running
docker exec ii-researcher ps aux

# Check environment variables
docker exec ii-researcher env | grep -E "OPENAI|SEARCH|SCRAPER"

# Test internal connectivity
docker exec ii-researcher curl http://localhost:8000
```

### Permission issues
```bash
# Ensure entrypoint is executable
chmod +x docker/entrypoint.sh
chmod +x docker/entrypoint-svc.sh
```

### Build fails
```bash
# Check Docker version
docker --version
docker buildx version

# Ensure buildx is set up
docker buildx create --use

# Clear build cache
make clean
```

---

## 📚 Additional Resources

### Documentation
- **Quick Start**: `/docs/docker/QUICKSTART.md`
- **Complete Guide**: `/docs/docker/DOCKER.md`
- **Architecture**: `/docs/architecture/ARCHITECTURE.md`
- **Layered Architecture**: `/docs/docker/LAYERED_ARCHITECTURE.md`

### Build Files
- **Makefile**: `/Makefile`
- **Docker Compose**: `/docker-compose.yml`
- **Environment Template**: `/env.template`

---

## ⚡ Build Optimization

The Dockerfiles use multi-stage builds to minimize image size:

### All-in-One (Dockerfile)
1. **base**: Base Python environment
2. **python-deps**: Python dependencies
3. **frontend-deps**: Node.js dependencies
4. **frontend-builder**: Next.js build
5. **node-runtime**: Node.js runtime for frontend
6. **runtime**: Final combined image

### Core Layer (Dockerfile.core)
1. **python-base**: Base Python environment
2. **python-deps-core**: Core dependencies
3. **core-runtime**: Final core image

### Service Layer (Dockerfile.svc)
1. **core-base**: Inherits from core image
2. **python-deps-svc**: Service-specific dependencies
3. **frontend-deps**: Node.js dependencies
4. **frontend-builder**: Next.js build
5. **node-runtime**: Node.js runtime
6. **svc-runtime**: Final service image

**Benefits:**
- Smaller final image size
- No build dependencies in runtime
- Optimized layer caching
- Multi-architecture support

---

## 🏷️ Version Management

Image versions are managed via git tags:

```bash
# Check current version
git describe --tags --abbrev=0

# Create new version
git tag v0.1.6
git push origin v0.1.6

# Build and push new version
make push             # All-in-one
make push-all         # All images
```

The Makefile automatically uses the git tag for version numbering (defaults to `v0.0.1` if no tag exists).

---

## 🎯 Which Image Should I Use?

### Use All-in-One (`nurol/ii-researcher`) if:
- ✅ You want the complete application
- ✅ Testing locally
- ✅ Simple single-container deployment
- ✅ Need frontend + backend together

### Use Service Layer (`nurol/ii-researcher-svc`) if:
- ✅ You only need backend services (API + MCP)
- ✅ Frontend hosted separately
- ✅ Building a custom frontend
- ✅ Want smaller backend image

### Use Core Layer (`nurol/ii-researcher-core`) if:
- ✅ Using as a Python library
- ✅ Building custom services on top
- ✅ CLI-only usage
- ✅ Need smallest possible image

---

*Last Updated: 2026-01-22*  
*Version: 0.1.5.1*

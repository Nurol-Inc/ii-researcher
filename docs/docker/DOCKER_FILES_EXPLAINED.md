# Docker Files Explanation

This document explains the purpose of each Dockerfile and docker-compose file in the project.

---

## Table of Contents
- [Dockerfiles](#dockerfiles)
- [Docker Compose Files](#docker-compose-files)
- [Quick Reference](#quick-reference)

---

## Dockerfiles

### 1. `docker/Dockerfile` (Main/Current)

**Purpose:** Unified multi-service container with all project services

**Contains:**
- Frontend (Next.js)
- API Server (FastAPI)
- MCP Server
- CLI Tool

**Key Features:**
- Multi-stage build for optimization
- Multi-architecture support (amd64, arm64)
- Selective service launching via entrypoint
- Production-ready

**Build Command:**
```bash
docker build -f docker/Dockerfile -t nurol/ii-researcher:latest .
# or
make build-local
```

**Use Cases:**
- Production deployments
- Testing full application stack
- Single container with all project services
- Multi-architecture builds for registry

**Architecture:**
```
Stage 1: frontend-builder → Build Next.js
Stage 2: python-base      → Base Python environment
Stage 3: python-deps      → Install dependencies
Stage 4: node-runtime     → Prepare Node.js runtime
Stage 5: runtime          → Final combined image
```

---

### 2. `docker/Dockerfile.api` (Legacy)

**Purpose:** API service only (original separate container approach)

**Contains:**
- API Server (FastAPI)
- Python dependencies from pyproject.toml

**Key Features:**
- Simple single-service image
- Smaller image size (~500MB)
- Used in legacy docker-compose setup

**Build Command:**
```bash
docker build -f docker/Dockerfile.api -t ii_researcher/api .
```

**Use Cases:**
- Legacy deployments
- Separate API scaling
- Microservices architecture with independent containers

**Status:** 
- ✅ Still functional
- ⚠️ Not recommended for new deployments (use main Dockerfile with `api` mode)
- 📦 Kept for backward compatibility

**Equivalent Modern Command:**
```bash
# Instead of using Dockerfile.api, use:
docker run nurol/ii-researcher:latest api
```

---

### 3. `docker/Dockerfile.litellm` (Legacy)

**Purpose:** LiteLLM proxy service only (now removed from project)

**Contains:**
- LiteLLM proxy server
- LiteLLM configuration

**Key Features:**
- Lightweight LiteLLM wrapper
- Used in legacy docker-compose setup

**Build Command:**
```bash
docker build -f docker/Dockerfile.litellm -t ii_researcher/litellm .
```

**Status:**
- ⚠️ **Deprecated** - LiteLLM removed from project containers
- 📦 Kept for reference only
- ❌ No longer used

**Replacement:**
Use official LiteLLM image instead:
```bash
docker run -d -p 4000:4000 \
  -v $(pwd)/litellm_config.yaml:/app/config.yaml \
  ghcr.io/berriai/litellm:latest \
  --config /app/config.yaml
```

---

### 4. `frontend/Dockerfile` (Frontend Service)

**Purpose:** Frontend-only container

**Contains:**
- Next.js application
- Built static assets
- Production server

**Key Features:**
- Optimized for frontend deployment
- Multi-stage build
- Standalone Next.js output

**Build Command:**
```bash
docker build -f frontend/Dockerfile -t ii_researcher/frontend ./frontend
```

**Use Cases:**
- Separate frontend deployment
- Static hosting
- CDN deployment

**Status:**
- ✅ Functional
- 🔄 Used in legacy docker-compose
- ⚠️ Prefer main Dockerfile with `frontend` mode for consistency

---

## Docker Compose Files

### 1. `docker-compose.yml` (Main/Current)

**Purpose:** Unified container deployment for testing

**Architecture:**
```yaml
services:
  ii-researcher:
    - Frontend (port 3000)
    - API (port 8000)
    - MCP (port 8765)
```

**Use Cases:**
- Local development testing
- Quick start for evaluation
- Single-server deployments
- CI/CD testing

**Start Command:**
```bash
docker compose up -d
```

**Key Features:**
- All project services in one container
- Environment variable configuration
- Health checks
- Restart policies
- No 3rd-party services (LiteLLM runs separately)

**When to Use:**
- ✅ Testing the full application
- ✅ Local development
- ✅ Simple single-server deployments
- ✅ CI/CD pipelines

---

### 2. `docker-compose-legacy.yml` (Legacy/Backup)

**Purpose:** Original separate-container architecture

**Architecture:**
```yaml
services:
  frontend:
    - Next.js only (port 3000)
  api:
    - FastAPI only (port 8000)
  litellm:
    - LiteLLM only (port 4000)
```

**Use Cases:**
- Microservices architecture
- Independent service scaling
- Legacy deployments
- Backward compatibility

**Start Command:**
```bash
docker compose -f docker-compose-legacy.yml up -d
```

**Key Features:**
- Three separate containers
- Independent scaling
- Service isolation
- Volume mounts for development

**When to Use:**
- ✅ Need to scale services independently
- ✅ Microservices deployment
- ✅ Legacy system compatibility
- ⚠️ More complex to manage
- ❌ LiteLLM section is outdated (remove or update)

**Status:**
- 🔄 Functional for frontend and API
- ⚠️ LiteLLM section needs update
- 📦 Kept for backward compatibility

---

### 3. `docker-compose-unified.yml` (Reference/Examples)

**Purpose:** Reference with multiple deployment scenarios

**Contains:**
- Main unified container setup
- Commented alternative scenarios:
  - Separate containers for each service
  - Backend services only
  - MCP server only
  - Scaled API with shared services

**Use Cases:**
- Documentation reference
- Copy/paste examples
- Different deployment patterns

**Key Features:**
- Multiple scenario examples
- Detailed comments
- Production patterns
- Scaling examples

**When to Use:**
- 📖 Reference for creating custom compose files
- 📋 Copy specific scenarios
- 🎓 Learning different deployment patterns
- ❌ Not meant to be run directly (uncomment desired scenario first)

---

## Quick Reference

### Which Dockerfile to Use?

| Scenario | Dockerfile | Command |
|----------|-----------|---------|
| **Production (Recommended)** | `docker/Dockerfile` | `make build-local` or `make push` |
| **All services together** | `docker/Dockerfile` | `docker run nurol/ii-researcher:latest all` |
| **API only** | `docker/Dockerfile` | `docker run nurol/ii-researcher:latest api` |
| **Frontend only** | `docker/Dockerfile` | `docker run nurol/ii-researcher:latest frontend` |
| **MCP only** | `docker/Dockerfile` | `docker run nurol/ii-researcher:latest mcp` |
| **CLI** | `docker/Dockerfile` | `docker run nurol/ii-researcher:latest cli` |
| **Legacy API** | `docker/Dockerfile.api` | Build separately (not recommended) |
| **Legacy Frontend** | `frontend/Dockerfile` | Build separately (not recommended) |

### Which Docker Compose to Use?

| Scenario | Compose File | Command |
|----------|-------------|---------|
| **Quick Start (Recommended)** | `docker-compose.yml` | `docker compose up -d` |
| **Testing** | `docker-compose.yml` | `docker compose up -d` |
| **Legacy/Microservices** | `docker-compose-legacy.yml` | `docker compose -f docker-compose-legacy.yml up -d` |
| **Reference/Examples** | `docker-compose-unified.yml` | Don't run directly - use as reference |

---

## Migration Path

### From Legacy to Current

**Old Way (Separate Containers):**
```yaml
services:
  frontend: ...
  api: ...
  litellm: ...
```

**New Way (Unified Container):**
```yaml
services:
  ii-researcher:
    # All project services in one container
    # LiteLLM runs separately if needed
```

**Benefits:**
- Simpler deployment
- Fewer containers to manage
- Better for testing
- Still supports service isolation via modes

---

## File Lifecycle Status

### ✅ Active (Use These)
- `docker/Dockerfile` - Main unified container
- `docker-compose.yml` - Current deployment

### 📦 Legacy (Backward Compatibility)
- `docker/Dockerfile.api` - Old API container
- `frontend/Dockerfile` - Old frontend container
- `docker-compose-legacy.yml` - Old separate containers

### 📖 Reference (Documentation)
- `docker-compose-unified.yml` - Examples and patterns

### ❌ Deprecated (Don't Use)
- `docker/Dockerfile.litellm` - LiteLLM removed from project

---

## Best Practices

### For Development
```bash
# Use main compose file
docker compose up -d
docker compose logs -f
```

### For Production
```bash
# Build with version tag
make push

# Deploy with external services
docker run -d \
  -p 3000:3000 -p 8000:8000 \
  -e OPENAI_BASE_URL=http://your-llm-service:4000 \
  registry.tunnel.xellence.us/nurol/ii-researcher:0.1.5.1
```

### For Testing Individual Services
```bash
# Test API only
docker run -d -p 8000:8000 nurol/ii-researcher:latest api

# Test Frontend only
docker run -d -p 3000:3000 nurol/ii-researcher:latest frontend
```

---

## Why Multiple Files?

### Dockerfiles

1. **docker/Dockerfile** (Main)
   - **Why:** One unified image with selective service launching
   - **Benefit:** Single build, multiple deployment options
   - **Trade-off:** Larger image (~2GB) but more flexible

2. **docker/Dockerfile.api** (Legacy)
   - **Why:** Smaller API-only image
   - **Benefit:** Lightweight (~500MB)
   - **Trade-off:** Less flexible, need multiple builds

3. **docker/Dockerfile.litellm** (Deprecated)
   - **Why:** Historical - LiteLLM was bundled
   - **Status:** No longer needed, use official LiteLLM image

### Docker Compose Files

1. **docker-compose.yml** (Main)
   - **Why:** Quick start for testing
   - **Benefit:** Simple, one command setup
   - **Trade-off:** All services together

2. **docker-compose-legacy.yml** (Legacy)
   - **Why:** Original microservices approach
   - **Benefit:** Independent scaling
   - **Trade-off:** More complex

3. **docker-compose-unified.yml** (Reference)
   - **Why:** Documentation and examples
   - **Benefit:** Shows multiple patterns
   - **Trade-off:** Not for direct use

---

## Recommendations

### ✅ Do This
- Use `docker/Dockerfile` for all builds
- Use `docker-compose.yml` for testing
- Use service modes (`all`, `api`, `frontend`, `mcp`, `cli`) for deployment flexibility
- Run LiteLLM separately if needed

### ❌ Don't Do This
- Don't use legacy Dockerfiles for new deployments
- Don't run `docker-compose-unified.yml` directly (it's reference only)
- Don't use `Dockerfile.litellm` (deprecated)

### 🎯 Migration
If using legacy setup:
1. Build new image: `make build-local`
2. Update compose file to use unified container
3. Run LiteLLM separately if needed
4. Test thoroughly
5. Remove old containers

---

*Last Updated: 2026-01-22*  
*For more information, see: docs/docker/DOCKER.md*

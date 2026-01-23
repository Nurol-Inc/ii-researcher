# Docker Files Explanation

This document explains the purpose of each Dockerfile and docker-compose file.

---

## Dockerfiles

### `docker/Dockerfile` (Main)

**Purpose:** Unified container with all project services

**Contains:** Frontend, API, MCP Server, CLI

**Architecture:**
- Multi-stage build (frontend-builder → python-deps → runtime)
- Multi-architecture (amd64, arm64)
- Selective service launching via entrypoint

**Build:**
```bash
make build-local
# or
docker build -f docker/Dockerfile -t nurol/ii-researcher:latest .
```

**Service Modes:**
```bash
docker run nurol/ii-researcher:latest all        # All services
docker run nurol/ii-researcher:latest api        # API only
docker run nurol/ii-researcher:latest frontend   # Frontend only
docker run nurol/ii-researcher:latest mcp        # MCP only
docker run nurol/ii-researcher:latest cli        # CLI mode
```

---

### `docker/Dockerfile.api` (Legacy)

**Purpose:** API service only (original separate container)

**Status:** ⚠️ Kept for backward compatibility, not recommended for new deployments

**Modern equivalent:** Use `docker run nurol/ii-researcher:latest api`

---

### `docker/Dockerfile.litellm` (Deprecated)

**Purpose:** LiteLLM proxy (removed from project)

**Status:** ❌ Deprecated - use official LiteLLM image:
```bash
docker run -d -p 4000:4000 ghcr.io/berriai/litellm:latest
```

---

### `frontend/Dockerfile` (Legacy)

**Purpose:** Frontend-only container

**Status:** ⚠️ Kept for legacy docker-compose, prefer main Dockerfile

---

## Docker Compose Files

### `docker-compose.yml` (Main)

**Purpose:** Quick start and testing

**Architecture:**
```yaml
services:
  ii-researcher:
    - Frontend (port 3001)
    - API (port 8001)
    - MCP (port 8765)
```

**Usage:**
```bash
docker compose up -d
```

**When to use:**
- ✅ Local development
- ✅ Testing
- ✅ Single-server deployments

---

### `docker-compose-legacy.yml` (Reference)

**Purpose:** Original separate-container architecture

**Architecture:**
```yaml
services:
  frontend: (port 3001)
  api: (port 8001)
```

**Usage:**
```bash
docker compose -f docker-compose-legacy.yml up -d
```

**When to use:**
- ✅ Independent service scaling
- ✅ Microservices architecture
- ⚠️ More complex setup

---

## Quick Reference

### Which Dockerfile?

| Scenario | Use | Command |
|----------|-----|---------|
| **Production** | `docker/Dockerfile` | `make build-local` |
| **All services** | `docker/Dockerfile` | `docker run ... all` |
| **Single service** | `docker/Dockerfile` | `docker run ... api/frontend/mcp` |

### Which Docker Compose?

| Scenario | File | Command |
|----------|------|---------|
| **Quick Start** | `docker-compose.yml` | `docker compose up -d` |
| **Legacy/Microservices** | `docker-compose-legacy.yml` | `docker compose -f docker-compose-legacy.yml up -d` |

---

## File Status

### ✅ Active
- `docker/Dockerfile` - Main unified container
- `docker-compose.yml` - Current deployment

### 📦 Legacy
- `docker/Dockerfile.api` - Old API container
- `frontend/Dockerfile` - Old frontend container
- `docker-compose-legacy.yml` - Old separate containers

### ❌ Deprecated
- `docker/Dockerfile.litellm` - Use official LiteLLM image

---

## Best Practices

### Development
```bash
docker compose up -d
docker compose logs -f
```

### Production
```bash
make push
docker run -d -p 3000:3000 -p 8000:8000 \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

### Individual Services
```bash
docker run -d -p 8000:8000 nurol/ii-researcher:latest api
docker run -d -p 3000:3000 nurol/ii-researcher:latest frontend
```

---

## Migration

**From Legacy (Separate Containers):**
```yaml
# Old
services:
  frontend: ...
  api: ...
  litellm: ...
```

**To Current (Unified):**
```yaml
# New
services:
  ii-researcher:
    # All services in one container
```

**Benefits:**
- Simpler deployment
- Fewer containers
- Better for testing
- Still supports service isolation

---

*Last Updated: 2026-01-22*

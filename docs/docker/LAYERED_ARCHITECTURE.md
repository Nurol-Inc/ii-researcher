# Layered Docker Architecture

**Date:** 2026-01-22  
**Change:** Added layered Docker architecture based on system design

---

## Overview

The II-Researcher project now supports **three Docker image strategies**:

1. **All-in-One Image** - Single image with all components (Frontend + Services + Core)
2. **Core Layer** - Foundation layer with reasoning agent and tool clients
3. **Service Layer** - API and MCP services built on Core layer

This layered approach follows the architecture documented in `docs/architecture/ARCHITECTURE.md`.

---

## Architecture Layers

```
┌──────────────────────────────────────────────────┐
│                 CLIENT LAYER                     │
│        (Web Browser, CLI, MCP Clients)           │
└────────────────────┬─────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────┐
│          SERVICE LAYER (Image: svc)              │
│      ┌──────────────┐  ┌──────────────┐          │
│      │  API Server  │  │  MCP Server  │          │
│      │  (FastAPI)   │  │  (FastMCP)   │          │
│      │  Port 8000   │  │  Port 8765   │          │
│      └──────────────┘  └──────────────┘          │
└────────────────────┬─────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────┐
│         CORE APPLICATION LAYER (Image: core)     │
│  ┌────────────────────────────────────────────┐  │
│  │       Reasoning Agent (Core Engine)        │  │
│  │  • Multi-step reasoning                    │  │
│  │  • Question decomposition                  │  │
│  │  • Report generation                       │  │
│  └────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────┐  │
│  │           Tool Clients                     │  │
│  │  • Search (Tavily, SerpAPI, DuckDuckGo)    │  │
│  │  • Scraper (Firecrawl, BS4, Browser)       │  │
│  │  • Compressor (Embedding, LLM)             │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

---

## Docker Images

### 1. Core Layer Image: `nurol/ii-researcher-core`

**Purpose:** Foundation layer containing the core application logic

**Contains:**
- Reasoning Agent
- Tool Clients (Search, Scraper, Compressor)
- Python dependencies
- ii_researcher Python package

**Does NOT contain:**
- Service layer (API, MCP)
- Frontend
- Entrypoint scripts for services

**Size:** ~800MB-1GB

**Dockerfile:** `docker/Dockerfile.core`

**Use Cases:**
- Base for custom service implementations
- Embedding in other Python applications
- Direct library usage
- Foundation for service layer

**Build:**
```bash
make build-core-local    # Local
make push-core           # Multi-arch to registry
```

**Run:**
```bash
# Python shell with core library
docker run -it nurol/ii-researcher-core:latest

# Use as library
docker run -it nurol/ii-researcher-core:latest python
>>> from ii_researcher.reasoning.agent import ReasoningAgent
>>> agent = ReasoningAgent(question="Your question")
```

---

### 2. Service Layer Image: `nurol/ii-researcher-svc`

**Purpose:** Service layer built on top of Core

**Contains:**
- Everything from Core layer
- API Server (FastAPI)
- MCP Server (FastMCP)
- Service entrypoint scripts
- Supervisor configuration

**Does NOT contain:**
- Frontend (Next.js)

**Size:** ~900MB-1.1GB

**Dockerfile:** `docker/Dockerfile.svc`

**Build Dependency:** Requires Core layer image

**Use Cases:**
- Backend services deployment
- API-only deployments
- MCP server deployments
- Microservices architecture

**Build:**
```bash
make build-svc-local     # Local (builds core first)
make push-svc            # Multi-arch to registry
```

**Run:**
```bash
# API Server
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  nurol/ii-researcher-svc:latest api

# MCP Server (HTTP mode)
docker run -d -p 8765:8765 \
  -e MCP_TRANSPORT=http \
  -e OPENAI_API_KEY=your-key \
  nurol/ii-researcher-svc:latest mcp

# CLI
docker run --rm \
  -e RESEARCH_QUESTION="What is AI?" \
  -e OPENAI_API_KEY=your-key \
  nurol/ii-researcher-svc:latest cli
```

---

### 3. All-in-One Image: `nurol/ii-researcher`

**Purpose:** Complete application with all components

**Contains:**
- Everything from Core and Service layers
- Frontend (Next.js)
- Full entrypoint with all service modes
- Supervisor configuration for all services

**Size:** ~2GB

**Dockerfile:** `docker/Dockerfile`

**Use Cases:**
- Complete application deployment
- Testing full stack
- Single-server deployments
- Docker Compose setups

**Build:**
```bash
make build-local         # Local
make push                # Multi-arch to registry
```

**Run:**
```bash
# All services
docker run -d -p 3000:3000 -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  nurol/ii-researcher:latest all

# Individual services (same as svc layer)
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  nurol/ii-researcher:latest api
```

---

## Docker Files Reference

| File | Purpose | Size | Contains |
|------|---------|------|----------|
| `docker/Dockerfile.core` | Core layer | ~800MB | Reasoning agent, tool clients |
| `docker/Dockerfile.svc` | Service layer | ~900MB | Core + API + MCP |
| `docker/Dockerfile` | All-in-one | ~2GB | Core + Services + Frontend |
| `docker/Dockerfile.api` | Legacy API | ~500MB | ⚠️ Deprecated |
| `docker/entrypoint-svc.sh` | Service entrypoint | - | For svc layer |
| `docker/entrypoint.sh` | All-in-one entrypoint | - | For all-in-one |
| `docker/supervisord-svc.conf` | Service supervisor | - | For svc layer |
| `docker/supervisord.conf` | All-in-one supervisor | - | For all-in-one |

---

## Makefile Targets

### Core Layer

```bash
make build-core-local    # Build core locally
make build-core-multi    # Build core multi-arch (no push)
make push-core           # Build and push core to registry
```

### Service Layer

```bash
make build-svc-local     # Build service locally (builds core first)
make build-svc-multi     # Build service multi-arch
make push-svc            # Build and push service (pushes core first)
```

### All-in-One

```bash
make build-local         # Build all-in-one locally
make build-multi         # Build all-in-one multi-arch
make push                # Build and push all-in-one
```

### Build All Layers

```bash
make build-all-local     # Build all three images locally
make push-all            # Build and push all three to registry
```

---

## Image Naming Convention

### Local Images
```
nurol/ii-researcher-core:0.1.5.1
nurol/ii-researcher-core:latest
nurol/ii-researcher-svc:0.1.5.1
nurol/ii-researcher-svc:latest
nurol/ii-researcher:0.1.5.1
nurol/ii-researcher:latest
```

### Registry Images
```
registry.tunnel.xellence.us/nurol/ii-researcher-core:0.1.5.1
registry.tunnel.xellence.us/nurol/ii-researcher-core:latest
registry.tunnel.xellence.us/nurol/ii-researcher-svc:0.1.5.1
registry.tunnel.xellence.us/nurol/ii-researcher-svc:latest
registry.tunnel.xellence.us/nurol/ii-researcher:0.1.5.1
registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

---

## Build Dependencies

```
┌─────────────────┐
│   Core Layer    │ ← Base layer (no dependencies)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Service Layer  │ ← Depends on Core layer
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   All-in-One    │ ← Depends on nothing (self-contained)
└─────────────────┘
```

**Note:** Service layer uses `FROM nurol/ii-researcher-core:latest` in its Dockerfile.

---

## Deployment Strategies

### Strategy 1: Layered Microservices

**Use layered images for maximum flexibility:**

```bash
# Deploy core as library (if needed)
docker run -d nurol/ii-researcher-core:latest python

# Deploy API service
docker run -d -p 8000:8000 \
  nurol/ii-researcher-svc:latest api

# Deploy MCP service
docker run -d -p 8765:8765 \
  nurol/ii-researcher-svc:latest mcp
```

**Benefits:**
- Clear separation of concerns
- Smaller service images
- Reusable core layer
- Independent scaling

---

### Strategy 2: All-in-One

**Use single image for simplicity:**

```bash
# Deploy everything
docker run -d -p 3000:3000 -p 8000:8000 \
  nurol/ii-researcher:latest all

# Or individual services from all-in-one
docker run -d -p 8000:8000 \
  nurol/ii-researcher:latest api
```

**Benefits:**
- Simpler deployment
- Single image to manage
- Flexible service modes
- Good for testing

---

### Strategy 3: Mixed

**Use different images for different needs:**

```bash
# Production API uses service layer
docker run -d -p 8000:8000 \
  nurol/ii-researcher-svc:latest api

# Testing uses all-in-one
docker run -d -p 3000:3000 -p 8000:8000 \
  nurol/ii-researcher:latest all
```

---

## When to Use Each Image

### Use Core Layer When:
- ✅ Building custom services
- ✅ Using as a Python library
- ✅ Need smallest possible image
- ✅ Creating your own service layer
- ✅ Embedding in other applications

### Use Service Layer When:
- ✅ Deploying backend services only
- ✅ Microservices architecture
- ✅ Don't need frontend
- ✅ Want clean separation from frontend
- ✅ Building on standard services

### Use All-in-One When:
- ✅ Testing full application
- ✅ Single-server deployment
- ✅ Docker Compose setup
- ✅ Quick start/evaluation
- ✅ Need all components together

---

## Build Examples

### Build Everything Locally

```bash
# Build all three images
make build-all-local

# Result:
# - nurol/ii-researcher-core:0.1.5.1
# - nurol/ii-researcher-svc:0.1.5.1
# - nurol/ii-researcher:0.1.5.1
```

### Build and Push to Registry

```bash
# Push all images
make push-all

# Or individually
make push-core     # Push core
make push-svc      # Push service (pushes core first)
make push          # Push all-in-one
```

### Build Only What You Need

```bash
# Just core
make build-core-local

# Just service (builds core too)
make build-svc-local

# Just all-in-one
make build-local
```

---

## Migration Guide

### From Legacy (Dockerfile.api)

**Old:**
```bash
docker build -f docker/Dockerfile.api -t myapi .
docker run -d -p 8000:8000 myapi
```

**New (use service layer):**
```bash
make build-svc-local
docker run -d -p 8000:8000 nurol/ii-researcher-svc:latest api
```

---

### From All-in-One to Layered

**Old:**
```bash
docker run -d -p 8000:8000 nurol/ii-researcher:latest api
```

**New:**
```bash
docker run -d -p 8000:8000 nurol/ii-researcher-svc:latest api
```

**Benefits:** Smaller image, faster pulls, clearer architecture

---

## Docker Compose Example

### Layered Architecture

```yaml
version: '3.8'

services:
  api:
    image: nurol/ii-researcher-svc:latest
    command: api
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
  
  mcp:
    image: nurol/ii-researcher-svc:latest
    command: mcp
    ports:
      - "8765:8765"
    environment:
      - MCP_TRANSPORT=http
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

### All-in-One

```yaml
version: '3.8'

services:
  ii-researcher:
    image: nurol/ii-researcher:latest
    command: all
    ports:
      - "3000:3000"
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

---

## Summary

✅ **Three Docker images created:**
- `nurol/ii-researcher-core` - Core application layer
- `nurol/ii-researcher-svc` - Service layer (API + MCP)
- `nurol/ii-researcher` - All-in-one image

✅ **Makefile targets added:**
- `make build-core-local`, `make push-core`
- `make build-svc-local`, `make push-svc`
- `make build-all-local`, `make push-all`

✅ **Architecture follows design:**
- Core → Service → Client layers
- Clean separation of concerns
- Reusable components

✅ **Benefits:**
- Flexibility in deployment
- Smaller images for specific needs
- Clear architectural boundaries
- Multiple deployment strategies

---

*Layered architecture implementation complete*  
*Date: 2026-01-22*

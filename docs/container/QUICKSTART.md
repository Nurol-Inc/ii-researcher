# II-Researcher Container Quick Start Guide

This guide provides quick instructions for building and deploying II-Researcher with Docker.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Build and Push](#build-and-push)
4. [Service Modes](#service-modes)
5. [Docker Compose](#docker-compose)
6. [Makefile Commands](#makefile-commands)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Docker 20.10+ installed
- Docker Buildx plugin (for multi-arch builds)
- Git (for version tagging)
- Make (optional, for Makefile commands)

---

## Quick Start

### 1. Create Environment File

Copy and configure the environment template:

```bash
# cp env.test .env
# Edit .env and add your API keys
```

**Minimal Configuration:**
```bash
OPENAI_API_KEY=your-openai-api-key
SEARCH_PROVIDER=duckduckgo  # Free option
SCRAPER_PROVIDER=bs         # Free option
```

### 2. Build Local Image

Using Makefile:
```bash
make build-local
```

Or manually:
```bash
docker build -f container/Dockerfile -t nurol/ii-researcher:latest .
```

### 3. Run the Container

```bash
docker run -d \
  --name ii-researcher \
  -p 3000:3000 \
  -p 8000:8000 \
  -p 8765:8765 \
  --env-file .env \
  nurol/ii-researcher:latest
```

### 4. Access Services

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000
- **MCP Server**: http://localhost:8765 (HTTP mode)

---

## Build and Push

### Build for Local Testing

```bash
make build-local
```

This creates:
- `nurol/ii-researcher:0.1.5.1` (version from git tag)
- `nurol/ii-researcher:latest`

### Build Layered Architecture

```bash
# Build all three images
make build-all-local

# Or individually
make build-core-local    # Core layer
make build-svc-local     # Service layer
make build-local         # All-in-one
```

### Build Multi-Architecture Images

```bash
make build-multi
```

Builds for both amd64 and arm64 (doesn't push to registry).

### Build and Push to Registry

```bash
# Push all-in-one
make push

# Push layered architecture
make push-all
```

Builds and pushes to `registry.tunnel.xellence.us/nurol/ii-researcher` for both architectures.

**Pushed images:**
- `registry.tunnel.xellence.us/nurol/ii-researcher:0.1.5.1`
- `registry.tunnel.xellence.us/nurol/ii-researcher:latest`
- `registry.tunnel.xellence.us/nurol/ii-researcher-core:0.1.5.1`
- `registry.tunnel.xellence.us/nurol/ii-researcher-svc:0.1.5.1`

---

## Service Modes

The unified container supports multiple service modes:

### Run All Services (Default)

```bash
docker run -d \
  --name ii-researcher \
  -p 3000:3000 -p 8000:8000 -p 8765:8765 \
  --env-file .env \
  nurol/ii-researcher:latest all
```

### Run Individual Services

**API Only:**
```bash
docker run -d \
  --name ii-researcher-api \
  -p 8000:8000 \
  --env-file .env \
  nurol/ii-researcher:latest api
```

**Frontend Only:**
```bash
docker run -d \
  --name ii-researcher-frontend \
  -p 3000:3000 \
  --env-file .env \
  -e NEXT_PUBLIC_API_URL=http://api-host:8000 \
  nurol/ii-researcher:latest frontend
```

**MCP Server:**
```bash
docker run -d \
  --name ii-researcher-mcp \
  -p 8765:8765 \
  --env-file .env \
  nurol/ii-researcher:latest mcp
```

### Run CLI Mode

```bash
docker run --rm \
  --env-file .env \
  -e RESEARCH_QUESTION="What is quantum computing?" \
  nurol/ii-researcher:latest cli
```

### Available Modes

| Mode | Command | Description |
|------|---------|-------------|
| `all` | `nurol/ii-researcher:latest all` | All services (default) |
| `api` | `nurol/ii-researcher:latest api` | API server only |
| `frontend` | `nurol/ii-researcher:latest frontend` | Frontend only |
| `mcp` | `nurol/ii-researcher:latest mcp` | MCP server |
| `cli` | `nurol/ii-researcher:latest cli` | CLI tool |
| `supervisor` | `nurol/ii-researcher:latest supervisor` | All services with supervisord |
| `bash` | `nurol/ii-researcher:latest bash` | Interactive shell |

---

## Docker Compose

### Using Docker Compose (Recommended)

The project includes a ready-to-use `docker-compose.yml`:

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

**Services started:**
- Frontend on port 3000
- API on port 8000
- MCP on port 8765

### Alternative Configurations

**Legacy separate containers:**
```bash
docker compose -f docker-compose-legacy.yml up -d
```

---

## Makefile Commands

The project includes a comprehensive Makefile for easy management.

### Display Help

```bash
make help
```

### Check Version

```bash
make version
```

Version is automatically determined from git tags (default: v0.0.1).

### Build Commands

```bash
# All-in-one image
make build-local    # Build for current architecture
make build-multi    # Build multi-arch (no push)
make push           # Build and push multi-arch

# Layered architecture
make build-core-local    # Build core layer
make build-svc-local     # Build service layer
make build-all-local     # Build all three images

make push-core           # Push core layer
make push-svc            # Push service layer (pushes core first)
make push-all            # Push all images
```

### Clean Commands

```bash
make clean          # Clean build cache
make clean-all      # Clean all Docker resources (interactive)
```

### Docker Compose Commands

```bash
make up             # Start services
make down           # Stop services
make logs           # View logs
```

### Info Commands

```bash
make info           # Display container information
make check          # Check Docker environment
```

---

## Troubleshooting

### Check Container Logs

```bash
docker logs -f ii-researcher
```

### Check Services Inside Container

```bash
docker exec ii-researcher ps aux
```

### Test Service Connectivity

```bash
# API
docker exec ii-researcher curl http://localhost:8000/docs

# Frontend
docker exec ii-researcher curl http://localhost:3000

# MCP
docker exec ii-researcher curl http://localhost:8765
```

### Interactive Shell

```bash
docker exec -it ii-researcher bash
```

### Common Issues

**Container exits immediately:**
```bash
# Run in foreground to see errors
docker run --rm -it --env-file .env nurol/ii-researcher:latest
```

**Missing API keys:**
```bash
# Verify environment variables
docker exec ii-researcher env | grep -E "OPENAI|SEARCH|SCRAPER"
```

**Port conflicts:**
```bash
# Use different ports
docker run -d \
  -p 13000:3000 \
  -p 18000:8000 \
  -p 18765:8765 \
  --env-file .env \
  nurol/ii-researcher:latest
```

**Service not starting:**
```bash
# Check specific service logs (supervisor mode)
docker exec ii-researcher tail -f /var/log/ii-researcher/api_stdout.log
docker exec ii-researcher tail -f /var/log/ii-researcher/api_stderr.log
```

---

## Version Management

### Create New Version

```bash
# Tag new version
git tag v0.1.6
git push origin v0.1.6

# Build and push
make push
```

### Check Current Version

```bash
make version
```

### Pull Specific Version

```bash
docker pull registry.tunnel.xellence.us/nurol/ii-researcher:0.1.5.1
```

---

## Registry Information

- **Registry**: `registry.tunnel.xellence.us`
- **Images**: 
  - `nurol/ii-researcher` (all-in-one)
  - `nurol/ii-researcher-core` (core layer)
  - `nurol/ii-researcher-svc` (service layer)
- **Architectures**: amd64, arm64

### Pull from Registry

```bash
# Pull all-in-one (latest)
docker pull registry.tunnel.xellence.us/nurol/ii-researcher:latest

# Pull specific version
docker pull registry.tunnel.xellence.us/nurol/ii-researcher:0.1.5.1

# Pull core layer
docker pull registry.tunnel.xellence.us/nurol/ii-researcher-core:latest

# Pull service layer
docker pull registry.tunnel.xellence.us/nurol/ii-researcher-svc:latest
```

### Run from Registry

```bash
docker run -d \
  --name ii-researcher \
  -p 3000:3000 -p 8000:8000 -p 8765:8765 \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

---

## Complete Example

Here's a complete workflow from scratch:

```bash
# 1. Clone repository
git clone https://github.com/Intelligent-Internet/ii-researcher.git
cd ii-researcher

# 2. Create environment file
# cp env.test .env
# Edit .env with your API keys

# 3. Build local image
make build-local

# 4. Test locally with docker-compose
docker compose up -d

# 5. Check logs
docker compose logs -f

# 6. Access services
# Frontend: http://localhost:3000
# API: http://localhost:8000/docs
# MCP: http://localhost:8765

# 7. Stop services
docker compose down

# 8. (Optional) Build and push to registry
make push

# 9. Clean up
make clean
```

---

## Additional Documentation

For more detailed information, see:

- **docs/architecture/ARCHITECTURE.md**: System architecture and component details
- **docs/container/CONTAINER.md**: Comprehensive Docker documentation
- **docs/container/LAYERED_ARCHITECTURE.md**: Layered architecture guide
- **container/README.md**: Docker build files documentation
- **README.md**: Main project documentation

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/Intelligent-Internet/ii-researcher/issues
- Documentation: See files above

---

*Last Updated: 2026-01-22*

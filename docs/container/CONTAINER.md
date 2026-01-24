# II-Researcher Container Documentation

## Table of Contents

- [Overview](#overview)
- [Container Architecture](#container-architecture)
- [Quick Start](#quick-start)
- [Service Modes](#service-modes)
- [Building Containers](#building-containers)
- [Running Containers](#running-containers)
- [Environment Variables](#environment-variables)
- [Multi-Architecture Support](#multi-architecture-support)
- [Docker Compose](#docker-compose)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

II-Researcher provides a unified Docker container that includes all services (Frontend, API, LiteLLM, MCP) in a single image. The container supports flexible deployment modes, allowing you to:

- Run all services together in one container
- Run individual services in separate containers
- Mix and match services based on your needs

**Registry Information:**
- Registry: `registry.tunnel.xellence.us`
- Image: `nurol/ii-researcher`
- Supported Architectures: `amd64`, `arm64`

---

## Container Architecture

### Unified Container Design

The container includes all necessary components:

```
┌──────────────────────────────────────────────────────────┐
│                  II-Researcher Container                 │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Frontend   │  │  API Server  │  │   LiteLLM    │    │
│  │   (Next.js)  │  │  (FastAPI)   │  │   (Proxy)    │    │
│  │   Port 3000  │  │  Port 8000   │  │  Port 4000   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                      │
│  │  MCP Server  │  │  CLI Tool    │                      │
│  │  Port 8765   │  │  (Optional)  │                      │
│  └──────────────┘  └──────────────┘                      │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │         Entrypoint Script (Selective Launch)       │  │
│  │  • all: Launch all services                        │  │
│  │  • litellm: LiteLLM only                           │  │
│  │  • api: API server only                            │  │
│  │  • frontend: Frontend only                         │  │
│  │  • mcp: MCP server only                            │  │
│  │  • api+litellm: API + LiteLLM                      │  │
│  │  • frontend+api: Frontend + API                    │  │
│  │  • cli: CLI mode                                   │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Container Layers

The Dockerfile uses multi-stage builds for optimization:

1. **Frontend Builder** - Builds Next.js frontend
2. **Python Base** - Base Python environment
3. **Python Dependencies** - Installs Python packages
4. **Node Runtime** - Prepares Node.js runtime
5. **Final Runtime** - Combines all components

---

## Quick Start

### 1. Pull the Image

```bash
# Pull latest version
docker pull registry.tunnel.xellence.us/nurol/ii-researcher:latest

# Pull specific version
docker pull registry.tunnel.xellence.us/nurol/ii-researcher:0.1.5
```

### 2. Create Environment File

Create a `.env` file with required configuration:

```bash
# Required: LLM Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=http://localhost:4000

# Search Provider (choose one)
SEARCH_PROVIDER=serpapi          # Options: serpapi, tavily, duckduckgo
SERPAPI_API_KEY=your-serpapi-key # If using serpapi
# TAVILY_API_KEY=your-tavily-key # If using tavily

# Scraper Provider (choose one)
SCRAPER_PROVIDER=firecrawl       # Options: firecrawl, bs, browser, tavily_extract
FIRECRAWL_API_KEY=your-firecrawl-key  # If using firecrawl

# Optional: Compression settings
COMPRESS_EMBEDDING_MODEL=text-embedding-3-large
COMPRESS_SIMILARITY_THRESHOLD=0.3
COMPRESS_MAX_OUTPUT_WORDS=4096
COMPRESS_MAX_INPUT_WORDS=32000
```

### 3. Run the Container

```bash
# Run all services
docker run -d \
  --name ii-researcher \
  -p 3000:3000 \
  -p 8000:8000 \
  -p 4000:4000 \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

### 4. Access Services

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000/docs
- **LiteLLM**: http://localhost:4000/health

---

## Service Modes

The container supports multiple service modes via the `SERVICE_MODE` environment variable or command argument.

### Mode: `all` (Default)

Starts all services (LiteLLM + API + Frontend)

```bash
docker run -d \
  --name ii-researcher \
  -p 3000:3000 -p 8000:8000 -p 4000:4000 \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest all
```

**Use Case:** Complete application stack for testing or single-server deployment

---

### Mode: `litellm`

Starts only the LiteLLM proxy service

```bash
docker run -d \
  --name ii-researcher-litellm \
  -p 4000:4000 \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest litellm
```

**Use Case:** Separate LLM proxy service for multiple API instances

---

### Mode: `api`

Starts only the API server

```bash
docker run -d \
  --name ii-researcher-api \
  -p 8000:8000 \
  --env-file .env \
  -e OPENAI_BASE_URL=http://litellm-host:4000 \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest api
```

**Use Case:** Scalable API deployment with external LiteLLM service

---

### Mode: `frontend`

Starts only the frontend service

```bash
docker run -d \
  --name ii-researcher-frontend \
  -p 3000:3000 \
  --env-file .env \
  -e NEXT_PUBLIC_API_URL=http://api-host:8000 \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest frontend
```

**Use Case:** Separate frontend deployment with external API

---

### Mode: `mcp`

Starts only the MCP server

```bash
# HTTP mode
docker run -d \
  --name ii-researcher-mcp \
  -p 8765:8765 \
  --env-file .env \
  -e MCP_TRANSPORT=http \
  -e MCP_PORT=8765 \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest mcp

# Stdio mode (for local integration)
docker run -it \
  --name ii-researcher-mcp \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest mcp
```

**Use Case:** MCP server for Claude Desktop or other MCP clients

---

### Mode: `api+litellm`

Starts API server and LiteLLM proxy together

```bash
docker run -d \
  --name ii-researcher-backend \
  -p 8000:8000 -p 4000:4000 \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest api+litellm
```

**Use Case:** Backend services without frontend

---

### Mode: `frontend+api`

Starts Frontend and API (requires external LiteLLM)

```bash
docker run -d \
  --name ii-researcher-web \
  -p 3000:3000 -p 8000:8000 \
  --env-file .env \
  -e OPENAI_BASE_URL=http://litellm-host:4000 \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest frontend+api
```

**Use Case:** Web interface with external LiteLLM service

---

### Mode: `cli`

Runs in CLI mode for single research query

```bash
docker run --rm \
  --env-file .env \
  -e RESEARCH_QUESTION="What is quantum computing?" \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest cli
```

**Use Case:** One-off research queries, scripting, automation

---

### Mode: `supervisor`

Starts all services using supervisord (alternative to default mode)

```bash
docker run -d \
  --name ii-researcher \
  -p 3000:3000 -p 8000:8000 -p 4000:4000 \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest supervisor
```

**Use Case:** Production deployment with process monitoring

---

### Mode: `bash` / `sh` / `shell`

Starts interactive shell for debugging

```bash
docker run -it --rm \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest bash
```

**Use Case:** Debugging, exploration, manual testing

---

## Building Containers

### Prerequisites

- Docker (20.10+)
- Docker Buildx (for multi-arch builds)
- Git (for version tagging)
- Make

### Build with Makefile

The project includes a comprehensive Makefile for building containers.

#### Display Help

```bash
make help
```

#### Check Version

```bash
make version
```

Version is automatically determined from git tags. Default is `v0.0.1` if no tag exists.

#### Build Local Image (Single Architecture)

```bash
# Build for local testing
make build-local
```

This builds an image for your current architecture (amd64 or arm64).

**Output:**
- `nurol/ii-researcher:0.1.5` (or your current version)
- `nurol/ii-researcher:latest`

#### Build Multi-Architecture Image

```bash
# Build for both amd64 and arm64 (doesn't push)
make build-multi
```

#### Build and Push to Registry

```bash
# Build and push multi-arch images
make push
```

This will:
1. Create a buildx builder if needed
2. Build images for amd64 and arm64
3. Push to `registry.tunnel.xellence.us/nurol/ii-researcher`
4. Tag with version and `latest`

**Pushed Images:**
- `registry.tunnel.xellence.us/nurol/ii-researcher:0.1.5`
- `registry.tunnel.xellence.us/nurol/ii-researcher:latest`

---

### Manual Build

#### Local Build

```bash
docker build \
  --file container/Dockerfile \
  --tag nurol/ii-researcher:0.1.5 \
  --tag nurol/ii-researcher:latest \
  .
```

#### Multi-Architecture Build

```bash
# Create builder (one-time setup)
docker buildx create --name ii-researcher-builder --use

# Build and push
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --file container/Dockerfile \
  --tag registry.tunnel.xellence.us/nurol/ii-researcher:0.1.5 \
  --tag registry.tunnel.xellence.us/nurol/ii-researcher:latest \
  --push \
  .
```

---

## Running Containers

### Basic Run

```bash
docker run -d \
  --name ii-researcher \
  -p 3000:3000 -p 8000:8000 -p 4000:4000 \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

### With Volume Mounts

```bash
# Mount custom litellm config
docker run -d \
  --name ii-researcher \
  -p 3000:3000 -p 8000:8000 -p 4000:4000 \
  --env-file .env \
  -v $(pwd)/my-litellm-config.yaml:/app/config/litellm_config.yaml \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

### With Resource Limits

```bash
docker run -d \
  --name ii-researcher \
  -p 3000:3000 -p 8000:8000 -p 4000:4000 \
  --env-file .env \
  --memory=4g \
  --cpus=2 \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

### With Restart Policy

```bash
docker run -d \
  --name ii-researcher \
  -p 3000:3000 -p 8000:8000 -p 4000:4000 \
  --env-file .env \
  --restart=unless-stopped \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

### View Logs

```bash
# View all logs
docker logs -f ii-researcher

# View last 100 lines
docker logs --tail 100 ii-researcher

# View logs with timestamps
docker logs -f --timestamps ii-researcher
```

### Execute Commands in Running Container

```bash
# Interactive shell
docker exec -it ii-researcher bash

# Run CLI command
docker exec ii-researcher python ii_researcher/cli.py --question "Your question"

# Check service status
docker exec ii-researcher ps aux
```

### Stop and Remove

```bash
# Stop container
docker stop ii-researcher

# Remove container
docker rm ii-researcher

# Stop and remove
docker rm -f ii-researcher
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM access | `sk-...` |

### LLM Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_BASE_URL` | LiteLLM proxy URL | `http://localhost:4000` |
| `STRATEGIC_LLM` | Model for strategic decisions | `gpt-4o` |
| `SMART_LLM` | Model for general tasks | `gpt-4o` |
| `FAST_LLM` | Model for compression | `gemini-lite` |
| `R_MODEL` | Reasoning model | `r1` |
| `R_TEMPERATURE` | Temperature for reasoning | `0.2` |
| `R_REPORT_MODEL` | Model for reports | `gpt-4o` |
| `R_PRESENCE_PENALTY` | Presence penalty | `0` |

### Search Configuration

| Variable | Description | Options | Default |
|----------|-------------|---------|---------|
| `SEARCH_PROVIDER` | Search provider | `serpapi`, `tavily`, `duckduckgo` | `serpapi` |
| `TAVILY_API_KEY` | Tavily API key (if using Tavily) | - | - |
| `SERPAPI_API_KEY` | SerpAPI key (if using SerpAPI) | - | - |

### Scraper Configuration

| Variable | Description | Options | Default |
|----------|-------------|---------|---------|
| `SCRAPER_PROVIDER` | Scraper provider | `firecrawl`, `bs`, `browser`, `tavily_extract` | `firecrawl` |
| `FIRECRAWL_API_KEY` | Firecrawl API key (if using Firecrawl) | - | - |

### Compression Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `COMPRESS_EMBEDDING_MODEL` | Embedding model | `text-embedding-3-large` |
| `COMPRESS_SIMILARITY_THRESHOLD` | Similarity threshold | `0.3` |
| `COMPRESS_MAX_OUTPUT_WORDS` | Max output words | `4096` |
| `COMPRESS_MAX_INPUT_WORDS` | Max input words | `32000` |
| `USE_LLM_COMPRESSOR` | Use LLM for compression | `false` |

### Timeout Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `SEARCH_PROCESS_TIMEOUT` | Search process timeout (seconds) | `300` |
| `SEARCH_QUERY_TIMEOUT` | Query timeout (seconds) | `20` |
| `SCRAPE_URL_TIMEOUT` | URL scraping timeout (seconds) | `30` |
| `STEP_SLEEP` | Sleep between steps (milliseconds) | `100` |

### Container-Specific Variables

| Variable | Description | Options | Default |
|----------|-------------|---------|---------|
| `SERVICE_MODE` | Service launch mode | `all`, `litellm`, `api`, `frontend`, `mcp`, `api+litellm`, `frontend+api`, `cli`, `supervisor`, `bash` | `all` |
| `MCP_TRANSPORT` | MCP transport mode | `stdio`, `http` | `stdio` |
| `MCP_PORT` | MCP server port | Any port | `8765` |
| `RESEARCH_QUESTION` | Question for CLI mode | Any text | - |
| `NODE_ENV` | Node environment | `production`, `development` | `production` |
| `NEXT_TELEMETRY_DISABLED` | Disable Next.js telemetry | `1`, `0` | `1` |

---

## Multi-Architecture Support

The container supports both `amd64` and `arm64` architectures.

### Building for Multiple Architectures

```bash
# Using Makefile
make push

# Using docker buildx directly
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag registry.tunnel.xellence.us/nurol/ii-researcher:latest \
  --push \
  .
```

### Pulling Architecture-Specific Images

Docker automatically pulls the correct architecture for your system:

```bash
# On amd64 system - pulls amd64 image
docker pull registry.tunnel.xellence.us/nurol/ii-researcher:latest

# On arm64 system - pulls arm64 image
docker pull registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

### Verify Architecture

```bash
# Check image architecture
docker image inspect registry.tunnel.xellence.us/nurol/ii-researcher:latest \
  | grep Architecture

# List all available architectures
docker buildx imagetools inspect registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

---

## Docker Compose

### Using Docker Compose (Unified Container)

The repository includes a `docker-compose.yml` for easy deployment.

#### Start Services

```bash
# Start all services in background
docker compose up -d

# Start with build
docker compose up --build -d

# View logs
docker compose logs -f
```

#### Configuration

The `docker-compose.yml` uses the unified container by default. Configure via `.env` file.

#### Stop Services

```bash
# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v
```

#### Scale Services

```bash
# Run multiple API instances
docker compose up -d --scale api=3
```

---

## Troubleshooting

### Common Issues

#### 1. Services Not Starting

**Problem:** Container starts but services are not accessible

**Solution:**
```bash
# Check logs
docker logs ii-researcher

# Check if services are running inside container
docker exec ii-researcher ps aux

# Check environment variables
docker exec ii-researcher env | grep -E "OPENAI|SEARCH|SCRAPER"
```

#### 2. LiteLLM Connection Issues

**Problem:** API cannot connect to LiteLLM

**Solution:**
```bash
# Check if LiteLLM is running
docker exec ii-researcher curl http://localhost:4000/health

# Verify OPENAI_BASE_URL
docker exec ii-researcher env | grep OPENAI_BASE_URL

# Check LiteLLM logs
docker logs ii-researcher | grep litellm
```

#### 3. Missing API Keys

**Problem:** Services fail due to missing API keys

**Solution:**
```bash
# Verify .env file exists and is correctly formatted
cat .env

# Recreate container with correct env file
docker rm -f ii-researcher
docker run -d \
  --name ii-researcher \
  -p 3000:3000 -p 8000:8000 -p 4000:4000 \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

#### 4. Port Conflicts

**Problem:** Cannot bind to port (already in use)

**Solution:**
```bash
# Check what's using the port
lsof -i :8000  # or :3000, :4000

# Use different ports
docker run -d \
  --name ii-researcher \
  -p 13000:3000 \
  -p 18000:8000 \
  -p 14000:4000 \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

#### 5. Container Exits Immediately

**Problem:** Container starts and exits right away

**Solution:**
```bash
# Check logs for error messages
docker logs ii-researcher

# Try running in foreground
docker run --rm -it \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest

# Start in shell mode to debug
docker run --rm -it \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest bash
```

### Health Checks

```bash
# Check container health
docker inspect ii-researcher | grep -A 10 Health

# Test endpoints manually
curl http://localhost:4000/health  # LiteLLM
curl http://localhost:8000/docs    # API
curl http://localhost:3000         # Frontend
```

### Performance Issues

```bash
# Check resource usage
docker stats ii-researcher

# Increase resources
docker run -d \
  --name ii-researcher \
  --memory=8g \
  --cpus=4 \
  -p 3000:3000 -p 8000:8000 -p 4000:4000 \
  --env-file .env \
  registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

---

## Best Practices

### Production Deployment

1. **Use Specific Version Tags**
   ```bash
   # Good
   registry.tunnel.xellence.us/nurol/ii-researcher:0.1.5
   
   # Avoid in production
   registry.tunnel.xellence.us/nurol/ii-researcher:latest
   ```

2. **Set Resource Limits**
   ```bash
   docker run -d \
     --memory=4g \
     --cpus=2 \
     --restart=unless-stopped \
     ...
   ```

3. **Use External LiteLLM**
   - Run LiteLLM in a separate container
   - Share among multiple API instances
   - Scale API independently

4. **Enable Health Checks**
   - Monitor container health
   - Set up alerts
   - Use orchestration tools (Kubernetes, Docker Swarm)

5. **Secure API Keys**
   - Use Docker secrets or environment injection
   - Never commit `.env` files
   - Rotate keys regularly

6. **Monitor Logs**
   - Use log aggregation (ELK, Splunk)
   - Set up log rotation
   - Monitor for errors

### Development

1. **Use Volume Mounts**
   ```bash
   docker run -d \
     -v $(pwd):/app \
     -p 3000:3000 -p 8000:8000 -p 4000:4000 \
     --env-file .env \
     nurol/ii-researcher:latest
   ```

2. **Interactive Mode**
   ```bash
   docker run -it --rm \
     --env-file .env \
     nurol/ii-researcher:latest bash
   ```

3. **Local Registry**
   - Use local image tags
   - Don't push to production registry

### Makefile Usage

```bash
# Development workflow
make build-local    # Build
make test           # Test locally
make clean          # Clean up

# Production workflow
make version        # Check version
make push           # Build and push multi-arch
make clean          # Clean up build cache
```

---

## Cleaning Up

### Clean Build Cache

```bash
# Using Makefile
make clean

# Manually
docker buildx prune -f
docker builder prune -f
docker image prune -f
```

### Clean All Docker Resources

```bash
# Using Makefile (interactive)
make clean-all

# Manually
docker system prune -a --volumes
```

### Remove Specific Images

```bash
# Remove local images
docker rmi nurol/ii-researcher:latest

# Remove registry images (locally)
docker rmi registry.tunnel.xellence.us/nurol/ii-researcher:0.1.5
docker rmi registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

---

## Additional Resources

- **Main Documentation**: [README.md](README.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **MCP User Guide**: [mcp/USERS_GUIDE.md](mcp/USERS_GUIDE.md)
- **MCP Developer Guide**: [mcp/DEVELOPERS_GUIDE.md](mcp/DEVELOPERS_GUIDE.md)
- **GitHub Repository**: https://github.com/Intelligent-Internet/ii-researcher

---

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

*Last Updated: 2026-01-22*

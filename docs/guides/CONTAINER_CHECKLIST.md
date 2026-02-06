# Docker Testing Checklist

Quick reference for testing Docker builds and deployments.

---

## Local Testing

### Build and Run
```bash
# Create environment file
cp env.test .env
# Edit .env with your API keys

# Build
make build-local

# Test
docker compose up -d
docker compose logs -f

# Verify services
curl http://localhost:3001  # Frontend
curl http://localhost:8001/docs  # API
curl http://localhost:8765  # MCP (SSE)

# MCP: full guide and troubleshooting → [MCP.md](MCP.md)

# Stop
docker compose down
make clean
```

### Test Individual Services
```bash
# API only
docker run -d -p 8000:8000 --env-file .env nurol/ii-researcher:latest api

# Frontend only
docker run -d -p 3000:3000 --env-file .env nurol/ii-researcher:latest frontend

# MCP only (see [MCP.md](MCP.md) for compose-mcp and OPENAI_BASE_URL)
docker run -d -p 8765:8765 --env-file .env nurol/ii-researcher:latest mcp

# CLI mode
docker run --rm -e RESEARCH_QUESTION="test" --env-file .env nurol/ii-researcher:latest cli
```

---

## Multi-Architecture Build

```bash
# Check buildx
docker buildx ls

# Build multi-arch
make build-multi

# Build and push
make push
```

---

## Registry Testing

```bash
# Create version tag
git tag v0.1.6
git push origin v0.1.6

# Check version
make version

# Push to registry
make push

# Pull and test
docker pull registry.tunnel.xellence.us/nurol/ii-researcher:latest
docker run -d --env-file .env registry.tunnel.xellence.us/nurol/ii-researcher:latest
```

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs ii-researcher

# Try foreground mode
docker run --rm -it --env-file .env nurol/ii-researcher:latest

# Try shell mode
docker run --rm -it --env-file .env nurol/ii-researcher:latest bash
```

### Services not accessible
```bash
# Check running services
docker exec ii-researcher ps aux

# Test internal connectivity
docker exec ii-researcher curl http://localhost:8000/docs
```

### Build fails
```bash
# Clean and retry
make clean-all
make check
make build-local
```

---

*Last Updated: 2026-01-22*

# II-Researcher Documentation

Complete documentation for understanding, deploying, and using II-Researcher.

---

## 📚 Documentation Structure

```
docs/
├── architecture/          # System architecture and design
│   └── ARCHITECTURE.md
├── container/             # Container and deployment guides
│   ├── CONTAINER.md       # Complete Docker guide
│   ├── QUICKSTART.md      # Quick start
│   ├── ENV_FILE_GUIDE.md  # Environment configuration
│   └── CONTAINER_FILES_EXPLAINED.md  # File purposes
├── design/                # Design documents (for review)
│   └── MCP_NUROL_LLM_HEADERS_PASSTHROUGH.md  # Pass Nurol auth headers to LLM
└── guides/                # Testing and reference
    ├── CONTAINER_CHECKLIST.md  # Docker testing checklist
    └── MCP.md             # MCP quick start, Docker, GUI, troubleshooting
```

---

## 🚀 Quick Start

**New to II-Researcher?**

1. **[Quick Start](container/QUICKSTART.md)** - Get running in 5 minutes
2. **[Architecture](architecture/ARCHITECTURE.md)** - Understand the system
3. **[Container Guide](container/CONTAINER.md)** - Complete deployment

---

## 📖 Core Documentation

### Architecture
- **[ARCHITECTURE.md](architecture/ARCHITECTURE.md)** - System components, communication flows, deployment modes

### Docker
- **[CONTAINER.md](container/CONTAINER.md)** - Complete deployment guide with all service modes
- **[QUICKSTART.md](container/QUICKSTART.md)** - 4-step quick start
- **[ENV_FILE_GUIDE.md](container/ENV_FILE_GUIDE.md)** - Environment configuration
- **[CONTAINER_FILES_EXPLAINED.md](container/CONTAINER_FILES_EXPLAINED.md)** - Which files to use when

### MCP Server
- **[MCP.md](guides/MCP.md)** - MCP quick start, Docker (compose-mcp), browser GUI, config, troubleshooting

### Design (for review)
- **[MCP Nurol LLM headers pass-through](design/MCP_NUROL_LLM_HEADERS_PASSTHROUGH.md)** - Forward Authorization and application headers from SSE to LLM calls

### Testing
- **[CONTAINER_CHECKLIST.md](guides/CONTAINER_CHECKLIST.md)** - Testing procedures and troubleshooting

---

## 🎯 Common Tasks

### Get Started
```bash
cp env.test .env
make build-local
docker compose up -d
```
📖 [QUICKSTART.md](container/QUICKSTART.md)

### Build & Deploy
```bash
make build-local    # Local build
make push           # Multi-arch + push
```
📖 [CONTAINER.md](container/CONTAINER.md)

### Run Individual Services
```bash
docker run nurol/ii-researcher:latest api        # API only
docker run nurol/ii-researcher:latest frontend  # Frontend only
docker run nurol/ii-researcher:latest mcp       # MCP only
```
📖 [CONTAINER.md](container/CONTAINER.md) - Service Modes

### MCP only (Docker)
```bash
docker compose -f docker-compose-mcp.yml up -d   # MCP at http://localhost:8765
```
📖 [MCP.md](guides/MCP.md) - Requires OPENAI_BASE_URL (use host.docker.internal for host API)

### Troubleshoot
📖 [CONTAINER.md](container/CONTAINER.md) - Troubleshooting  
📖 [CONTAINER_CHECKLIST.md](guides/CONTAINER_CHECKLIST.md) - Testing

---

## 📞 Getting Help

1. **Quick start:** [QUICKSTART.md](container/QUICKSTART.md)
2. **Troubleshooting:** [CONTAINER.md](container/CONTAINER.md)#troubleshooting
3. **Testing:** [CONTAINER_CHECKLIST.md](guides/CONTAINER_CHECKLIST.md)

---

## 🔗 External Resources

- **Main README:** [/README.md](../README.md)
- **Docker Docs:** https://docs.docker.com
- **LiteLLM:** https://docs.litellm.ai

---

*Last updated: 2026-02-05*

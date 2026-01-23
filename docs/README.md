# II-Researcher Documentation

Complete documentation for understanding, deploying, and using II-Researcher.

---

## 📚 Documentation Structure

```
docs/
├── architecture/          # System architecture and design
│   └── ARCHITECTURE.md
├── docker/               # Docker and deployment guides
│   ├── DOCKER.md         # Complete Docker guide
│   ├── QUICKSTART.md     # Quick start
│   ├── ENV_FILE_GUIDE.md # Environment configuration
│   └── DOCKER_FILES_EXPLAINED.md  # File purposes
└── guides/               # Testing and reference
    └── DOCKER_CHECKLIST.md  # Testing checklist
```

---

## 🚀 Quick Start

**New to II-Researcher?**

1. **[Quick Start](docker/QUICKSTART.md)** - Get running in 5 minutes
2. **[Architecture](architecture/ARCHITECTURE.md)** - Understand the system
3. **[Docker Guide](docker/DOCKER.md)** - Complete deployment

---

## 📖 Core Documentation

### Architecture
- **[ARCHITECTURE.md](architecture/ARCHITECTURE.md)** - System components, communication flows, deployment modes

### Docker
- **[DOCKER.md](docker/DOCKER.md)** - Complete deployment guide with all service modes
- **[QUICKSTART.md](docker/QUICKSTART.md)** - 4-step quick start
- **[ENV_FILE_GUIDE.md](docker/ENV_FILE_GUIDE.md)** - Environment configuration
- **[DOCKER_FILES_EXPLAINED.md](docker/DOCKER_FILES_EXPLAINED.md)** - Which files to use when

### Testing
- **[DOCKER_CHECKLIST.md](guides/DOCKER_CHECKLIST.md)** - Testing procedures and troubleshooting

---

## 🎯 Common Tasks

### Get Started
```bash
cp env.test .env
make build-local
docker compose up -d
```
📖 [QUICKSTART.md](docker/QUICKSTART.md)

### Build & Deploy
```bash
make build-local    # Local build
make push           # Multi-arch + push
```
📖 [DOCKER.md](docker/DOCKER.md)

### Run Individual Services
```bash
docker run nurol/ii-researcher:latest api        # API only
docker run nurol/ii-researcher:latest frontend   # Frontend only
docker run nurol/ii-researcher:latest mcp        # MCP only
```
📖 [DOCKER.md](docker/DOCKER.md) - Service Modes

### Troubleshoot
📖 [DOCKER.md](docker/DOCKER.md) - Troubleshooting  
📖 [DOCKER_CHECKLIST.md](guides/DOCKER_CHECKLIST.md) - Testing

---

## 📞 Getting Help

1. **Quick start:** [QUICKSTART.md](docker/QUICKSTART.md)
2. **Troubleshooting:** [DOCKER.md](docker/DOCKER.md)#troubleshooting
3. **Testing:** [DOCKER_CHECKLIST.md](guides/DOCKER_CHECKLIST.md)

---

## 🔗 External Resources

- **Main README:** [/README.md](../README.md)
- **Docker Docs:** https://docs.docker.com
- **LiteLLM:** https://docs.litellm.ai

---

*Last Updated: 2026-01-22*

# II-Researcher Documentation

Welcome to the II-Researcher documentation! This folder contains comprehensive documentation for understanding, deploying, and using the II-Researcher application.

---

## 📚 Documentation Structure

```
docs/
├── architecture/          # System architecture and design
│   └── ARCHITECTURE.md   # Complete system architecture
├── docker/               # Docker and deployment guides
│   ├── DOCKER.md         # Comprehensive Docker guide
│   ├── QUICKSTART.md     # Quick start guide
│   ├── BUILD_VERIFICATION.md
│   ├── CHANGELOG_LITELLM_REMOVAL.md
│   └── DOCKER_FILES_EXPLAINED.md
└── guides/               # User and developer guides
    ├── DOCKER_SUMMARY.md
    └── DOCKER_CHECKLIST.md
```

---

## 🚀 Quick Start

**New to II-Researcher?** Start here:

1. **[Quick Start Guide](docker/QUICKSTART.md)** - Get running in 5 minutes
2. **[Architecture Overview](architecture/ARCHITECTURE.md)** - Understand the system
3. **[Docker Guide](docker/DOCKER.md)** - Complete Docker deployment

---

## 📖 Documentation Categories

### Architecture Documentation

**Location:** `docs/architecture/`

- **[ARCHITECTURE.md](architecture/ARCHITECTURE.md)** - Complete system architecture
  - 5 service components (Frontend, API, LiteLLM, MCP, CLI)
  - Service communication flows
  - Dependencies and startup order
  - Configuration details
  - Deployment modes

**When to read:**
- ✅ Understanding how the system works
- ✅ Planning deployment architecture
- ✅ Contributing to the project
- ✅ Troubleshooting issues

---

### Docker Documentation

**Location:** `docs/docker/`

#### Core Documentation

1. **[DOCKER.md](docker/DOCKER.md)** (~900 lines)
   - Complete Docker deployment guide
   - All service modes with examples
   - Building containers
   - Environment variables reference
   - Multi-architecture support
   - Troubleshooting guide

2. **[QUICKSTART.md](docker/QUICKSTART.md)** (~400 lines)
   - Get started in 4 steps
   - Quick command reference
   - Common scenarios
   - Complete workflow example

3. **[DOCKER_FILES_EXPLAINED.md](docker/DOCKER_FILES_EXPLAINED.md)**
   - Purpose of each Dockerfile
   - Purpose of each docker compose file
   - Which file to use when
   - Migration guide

#### Reference Documentation

4. **[BUILD_VERIFICATION.md](docker/BUILD_VERIFICATION.md)**
   - Pre-build verification checklist
   - Build process details
   - Troubleshooting build issues

5. **[CHANGELOG_LITELLM_REMOVAL.md](docker/CHANGELOG_LITELLM_REMOVAL.md)**
   - Changes made to remove LiteLLM from container
   - Migration guide
   - How to run LiteLLM separately

**When to read:**
- ✅ Docker deployments
- ✅ Container builds
- ✅ Multi-architecture builds
- ✅ Production deployment

---

### Guides

**Location:** `docs/guides/`

1. **[DOCKER_SUMMARY.md](guides/DOCKER_SUMMARY.md)** (~600 lines)
   - Complete implementation summary
   - All files created
   - Deployment scenarios
   - Testing checklist
   - Next steps

2. **[DOCKER_CHECKLIST.md](guides/DOCKER_CHECKLIST.md)** (~350 lines)
   - Implementation checklist
   - Testing procedures
   - Before committing checklist
   - Quick command reference

**When to read:**
- ✅ Project overview
- ✅ Implementation details
- ✅ Testing procedures
- ✅ Deployment preparation

---

## 🎯 Common Tasks

### I Want To...

#### Get Started Quickly
👉 Read: [QUICKSTART.md](docker/QUICKSTART.md)
```bash
# 4 steps to get running
cp env.template .env
make build-local
docker compose up -d
# Access: http://localhost:3000
```

#### Understand the Architecture
👉 Read: [ARCHITECTURE.md](architecture/ARCHITECTURE.md)
- System diagram
- Service components
- Communication flows

#### Build Docker Containers
👉 Read: [DOCKER.md](docker/DOCKER.md) - Building Containers section
```bash
make build-local    # Local build
make push           # Multi-arch + push to registry
```

#### Deploy to Production
👉 Read: [DOCKER.md](docker/DOCKER.md) - Deployment sections
- Service modes
- Environment configuration
- Best practices

#### Understand Docker Files
👉 Read: [DOCKER_FILES_EXPLAINED.md](docker/DOCKER_FILES_EXPLAINED.md)
- Which Dockerfile to use
- Which docker-compose to use
- Legacy vs. current

#### Troubleshoot Issues
👉 Read: [DOCKER.md](docker/DOCKER.md) - Troubleshooting section
- Common issues
- Solutions
- Debug commands

#### Run Individual Services
👉 Read: [DOCKER.md](docker/DOCKER.md) - Service Modes section
```bash
docker run nurol/ii-researcher:latest api        # API only
docker run nurol/ii-researcher:latest frontend   # Frontend only
docker run nurol/ii-researcher:latest mcp        # MCP only
```

#### Use with LiteLLM
👉 Read: [CHANGELOG_LITELLM_REMOVAL.md](docker/CHANGELOG_LITELLM_REMOVAL.md)
```bash
# Run LiteLLM separately
docker run -d -p 4000:4000 ghcr.io/berriai/litellm:latest
# Run ii-researcher with external LiteLLM
docker run -d -p 3000:3000 -p 8000:8000 \
  -e OPENAI_BASE_URL=http://litellm:4000 \
  nurol/ii-researcher:latest
```

---

## 📊 Documentation Stats

| Category | Files | Total Lines | Purpose |
|----------|-------|-------------|---------|
| Architecture | 1 | ~500 | System understanding |
| Docker | 5 | ~2,300 | Deployment & building |
| Guides | 2 | ~1,000 | Implementation & testing |
| **Total** | **8** | **~3,800** | Complete documentation |

---

## 🗺️ Documentation Roadmap

### Current Status: ✅ Complete

All major documentation is complete and covers:
- ✅ System architecture
- ✅ Docker deployment
- ✅ Building containers
- ✅ Service modes
- ✅ Environment configuration
- ✅ Troubleshooting
- ✅ Quick start
- ✅ Reference materials

### Future Enhancements

Potential additions:
- [ ] API reference documentation
- [ ] MCP integration guide
- [ ] Frontend development guide
- [ ] Contributing guidelines
- [ ] Performance tuning guide
- [ ] Security best practices
- [ ] Kubernetes deployment guide
- [ ] Video tutorials

---

## 🔍 Search Documentation

### By Topic

**Architecture:**
- System design → [ARCHITECTURE.md](architecture/ARCHITECTURE.md)
- Service components → [ARCHITECTURE.md](architecture/ARCHITECTURE.md)#component-details
- Communication flows → [ARCHITECTURE.md](architecture/ARCHITECTURE.md)#service-communication-flow

**Docker:**
- Quick start → [QUICKSTART.md](docker/QUICKSTART.md)
- Complete guide → [DOCKER.md](docker/DOCKER.md)
- File explanations → [DOCKER_FILES_EXPLAINED.md](docker/DOCKER_FILES_EXPLAINED.md)
- Build verification → [BUILD_VERIFICATION.md](docker/BUILD_VERIFICATION.md)

**Deployment:**
- Service modes → [DOCKER.md](docker/DOCKER.md)#service-modes
- Environment vars → [DOCKER.md](docker/DOCKER.md)#environment-variables
- Multi-arch builds → [DOCKER.md](docker/DOCKER.md)#multi-architecture-support

**Troubleshooting:**
- Common issues → [DOCKER.md](docker/DOCKER.md)#troubleshooting
- Build issues → [BUILD_VERIFICATION.md](docker/BUILD_VERIFICATION.md)
- LiteLLM changes → [CHANGELOG_LITELLM_REMOVAL.md](docker/CHANGELOG_LITELLM_REMOVAL.md)

---

## 📝 Document Conventions

### File Naming
- `UPPERCASE.md` - Major documentation files
- `lowercase.md` - Supporting or draft files

### Document Structure
All major docs include:
- Table of Contents
- Clear sections
- Code examples
- Quick reference tables
- Last updated date

### Code Examples
- ✅ Complete, runnable examples
- ✅ Comments for clarity
- ✅ Both success and error cases shown

---

## 🤝 Contributing to Documentation

Found an error or want to improve the docs?

1. **Small fixes:** Edit directly
2. **Major changes:** Discuss in issues first
3. **New sections:** Follow existing structure
4. **Code examples:** Test before adding

**Documentation Style:**
- Clear and concise
- Examples for every concept
- Avoid jargon where possible
- Use tables for comparisons
- Include troubleshooting tips

---

## 📞 Getting Help

1. **Check documentation:** Most questions are answered here
2. **Search docs:** Use Ctrl+F in relevant doc
3. **Quick start:** [QUICKSTART.md](docker/QUICKSTART.md) for basics
4. **Troubleshooting:** [DOCKER.md](docker/DOCKER.md)#troubleshooting
5. **Issues:** GitHub Issues for bugs/questions

---

## 🔗 External Resources

### Project Links
- **Main README:** [/README.md](../README.md)
- **GitHub:** https://github.com/Intelligent-Internet/ii-researcher
- **Blog Post:** https://www.ii.inc/web/blog/post/ii-researcher

### Related Documentation
- **Docker:** https://docs.docker.com
- **Next.js:** https://nextjs.org/docs
- **FastAPI:** https://fastapi.tiangolo.com
- **LiteLLM:** https://docs.litellm.ai

---

## 📋 Quick Command Reference

```bash
# Documentation structure
cd docs/
ls -R

# Read documentation (examples)
cat docs/docker/QUICKSTART.md
less docs/architecture/ARCHITECTURE.md

# Search documentation
grep -r "service mode" docs/
grep -r "OPENAI_API_KEY" docs/

# Build and deploy
make build-local           # Build container
docker compose up -d       # Start services
docker compose logs -f     # View logs
```

---

## 📚 Recommended Reading Order

### For New Users
1. [QUICKSTART.md](docker/QUICKSTART.md) - Get started fast
2. [ARCHITECTURE.md](architecture/ARCHITECTURE.md) - Understand the system
3. [DOCKER.md](docker/DOCKER.md) - Deep dive into deployment

### For Deployers
1. [DOCKER.md](docker/DOCKER.md) - Complete deployment guide
2. [DOCKER_FILES_EXPLAINED.md](docker/DOCKER_FILES_EXPLAINED.md) - File purposes
3. [DOCKER_CHECKLIST.md](guides/DOCKER_CHECKLIST.md) - Deployment checklist

### For Developers
1. [ARCHITECTURE.md](architecture/ARCHITECTURE.md) - System design
2. [DOCKER_SUMMARY.md](guides/DOCKER_SUMMARY.md) - Implementation details
3. [DOCKER.md](docker/DOCKER.md) - Container structure

### For Troubleshooting
1. [DOCKER.md](docker/DOCKER.md)#troubleshooting - Common issues
2. [BUILD_VERIFICATION.md](docker/BUILD_VERIFICATION.md) - Build problems
3. [CHANGELOG_LITELLM_REMOVAL.md](docker/CHANGELOG_LITELLM_REMOVAL.md) - Recent changes

---

*Documentation maintained by the II-Researcher team*  
*Last Updated: 2026-01-22*  
*Questions? See [GitHub Issues](https://github.com/Intelligent-Internet/ii-researcher/issues)*

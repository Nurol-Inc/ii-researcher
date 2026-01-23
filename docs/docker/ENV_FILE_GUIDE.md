# Environment File Configuration Guide

This guide explains how to use environment files (`.env`) to configure II-Researcher Docker deployments.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Environment Variables Reference](#environment-variables-reference)
- [Configuration Examples](#configuration-examples)
- [Multiple Environments](#multiple-environments)
- [Troubleshooting](#troubleshooting)

## Overview

All Docker Compose files use `env.test` by default for configuration management:

- **`env.test`** - Test/example configuration (version controlled, used by default)
- **`.env`** - Your local configuration (gitignored, overrides env.test if present)

This approach provides:

✅ **Works Out of the Box** - `env.test` provides test values, runs without setup  
✅ **Safe for Git** - Example values committed, real secrets in `.env` (gitignored)  
✅ **Centralized Config** - All settings in one place  
✅ **Multiple Environments** - Easy dev/test/prod switching  
✅ **Better Security** - Actual API keys never committed

## Quick Start

### Option 1: Quick Test (No Setup)

Docker Compose uses `env.test` automatically with placeholder values:

```bash
# Just run - no setup needed!
docker compose up -d
```

**Note:** Services requiring real API keys will fail with test placeholders.

### Option 2: Local Development (Recommended)

Create `.env` with your real API keys:

```bash
# Copy env.test to .env
cp env.test .env

# Edit .env with your actual API keys
nano .env
```

### 2. Configure Required Variables

### Configure Required Variables

At minimum, set these in your `.env` file:

```bash
# Required: OpenAI API Key
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Required: LLM Base URL (if using external LiteLLM)
OPENAI_BASE_URL=http://host.docker.internal:4000

# Required: Search Provider & API Key
SEARCH_PROVIDER=serpapi
SERPAPI_API_KEY=your-serpapi-key-here

# Required: Scraper Provider & API Key
SCRAPER_PROVIDER=firecrawl
FIRECRAWL_API_KEY=your-firecrawl-key-here
```

### Launch Services

```bash
# Uses .env if it exists, otherwise falls back to env.test
docker compose up -d
```

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `OPENAI_BASE_URL` | LLM API endpoint | `http://localhost:4000` |
| `SEARCH_PROVIDER` | Search provider to use | `serpapi`, `tavily`, `duckduckgo` |
| `SERPAPI_API_KEY` | SerpAPI key (if using SerpAPI) | `abc123...` |
| `TAVILY_API_KEY` | Tavily key (if using Tavily) | `tvly-...` |
| `SCRAPER_PROVIDER` | Web scraper to use | `firecrawl`, `bs`, `browser` |
| `FIRECRAWL_API_KEY` | Firecrawl key (if using Firecrawl) | `fc-...` |

### Optional LLM Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `STRATEGIC_LLM` | Strategic reasoning model | `gpt-4o` |
| `SMART_LLM` | Smart analysis model | `gpt-4o` |
| `FAST_LLM` | Fast processing model | `gemini-lite` |
| `R_MODEL` | Reasoning model | `r1` |
| `R_TEMPERATURE` | Reasoning temperature | `0.2` |
| `R_REPORT_MODEL` | Report generation model | `gpt-4o` |
| `R_PRESENCE_PENALTY` | Presence penalty | `0` |

### Optional Performance Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `SEARCH_PROCESS_TIMEOUT` | Overall search timeout (seconds) | `300` |
| `SEARCH_QUERY_TIMEOUT` | Per-query timeout (seconds) | `20` |
| `SCRAPE_URL_TIMEOUT` | URL scraping timeout (seconds) | `30` |
| `STEP_SLEEP` | Sleep between steps (milliseconds) | `100` |

### Optional Compression Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `COMPRESS_EMBEDDING_MODEL` | Embedding model for compression | `text-embedding-3-large` |
| `COMPRESS_SIMILARITY_THRESHOLD` | Similarity threshold | `0.3` |
| `COMPRESS_MAX_OUTPUT_WORDS` | Max output words | `4096` |
| `COMPRESS_MAX_INPUT_WORDS` | Max input words | `32000` |
| `USE_LLM_COMPRESSOR` | Use LLM for compression | `false` |

### Optional Container Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_ENV` | Node.js environment | `production` |
| `NEXT_PUBLIC_API_URL` | Frontend API URL | `http://localhost:8000` |
| `NEXT_TELEMETRY_DISABLED` | Disable Next.js telemetry | `1` |
| `SERVICE_MODE` | Container service mode | `all` |
| `MCP_TRANSPORT` | MCP transport protocol | `stdio` |
| `MCP_PORT` | MCP HTTP port | `8765` |

## Configuration Examples

### Example 1: Development Setup (Free Tier)

```bash
# .env.dev
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=http://host.docker.internal:4000

# Use free providers
SEARCH_PROVIDER=duckduckgo
SCRAPER_PROVIDER=bs

# Development settings
NODE_ENV=development
STEP_SLEEP=100
SEARCH_PROCESS_TIMEOUT=60
```

Run with:
```bash
docker compose --env-file .env.dev up -d
```

### Example 2: Production Setup (Paid Services)

```bash
# .env.prod
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1

# Use premium providers
SEARCH_PROVIDER=serpapi
SERPAPI_API_KEY=your-serpapi-key
SCRAPER_PROVIDER=firecrawl
FIRECRAWL_API_KEY=your-firecrawl-key

# Production optimization
STRATEGIC_LLM=gpt-4o
SMART_LLM=gpt-4o
FAST_LLM=gpt-4o-mini
SEARCH_PROCESS_TIMEOUT=300
SCRAPE_URL_TIMEOUT=60

# Production settings
NODE_ENV=production
COMPRESS_MAX_OUTPUT_WORDS=8192
USE_LLM_COMPRESSOR=true
```

Run with:
```bash
docker compose --env-file .env.prod up -d
```

### Example 3: Testing Setup with External LiteLLM

```bash
# .env.test
OPENAI_API_KEY=sk-your-openai-key

# Point to external LiteLLM
OPENAI_BASE_URL=http://host.docker.internal:4000

# Test providers
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=your-tavily-key
SCRAPER_PROVIDER=firecrawl
FIRECRAWL_API_KEY=your-firecrawl-key

# Test-specific settings
SEARCH_PROCESS_TIMEOUT=120
SEARCH_QUERY_TIMEOUT=15
STEP_SLEEP=50
```

Run external LiteLLM first:
```bash
docker run -d -p 4000:4000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  ghcr.io/berriai/litellm:latest
```

Then run ii-researcher:
```bash
docker compose --env-file .env.test up -d
```

## Multiple Environments

### Managing Multiple Configuration Files

Create separate env files for different environments:

```bash
env.test              # Test/example config (version controlled, default)
env.template          # Alternative template (reference)
.env                  # Local development (gitignored, overrides env.test)
.env.dev              # Development (gitignored)
.env.staging          # Staging (gitignored)
.env.prod             # Production (gitignored)
```

**Important:**
- `env.test` is version controlled with safe placeholder values
- All `.env*` files are gitignored for security
- `.env` takes precedence if it exists

### Switching Between Environments

```bash
# Default - uses env.test (or .env if it exists)
docker compose up -d

# Development
docker compose --env-file .env.dev up -d

# Staging
docker compose --env-file .env.staging up -d

# Production
docker compose --env-file .env.prod up -d
```

### Using Environment-Specific Compose Files

Combine env files with different compose files:

```bash
# Unified container for dev/test
docker compose -f docker-compose.yml --env-file .env.dev up -d

# Separate containers for production
docker compose -f docker-compose-legacy.yml --env-file .env.prod up -d
```

## Troubleshooting

### Issue: Environment Variables Not Loading

**Symptom:** Container starts but configuration is wrong

**Solutions:**

1. Check which file is being used:
   ```bash
   # Docker Compose precedence:
   # 1. --env-file flag (if specified)
   # 2. .env in current directory
   # 3. env.test (configured in docker-compose.yml)
   
   ls -la env.test .env
   ```

2. Verify file format:
   ```bash
   # No spaces around = sign
   # Correct:
   OPENAI_API_KEY=sk-123456
   
   # Incorrect:
   OPENAI_API_KEY = sk-123456
   ```

3. Check for quotes:
   ```bash
   # Usually not needed, but sometimes required for special characters
   OPENAI_API_KEY="sk-123456"
   ```

### Issue: API Keys Not Working

**Symptom:** Authentication errors in logs

**Solutions:**

1. Verify key format:
   ```bash
   cat .env | grep API_KEY
   # Ensure no extra spaces or newlines
   ```

2. Check key is set:
   ```bash
   docker compose config | grep API_KEY
   # Should show the actual key value (be careful with sensitive output)
   ```

3. Restart containers after changing .env:
   ```bash
   docker compose down
   docker compose up -d
   ```

### Issue: Variables Not Overriding Defaults

**Symptom:** Custom values in .env are ignored

**Solutions:**

1. Understand precedence (highest to lowest):
   - Environment variables in `docker compose run -e VAR=value`
   - Environment section in docker-compose.yml
   - env_file in docker-compose.yml
   - Dockerfile ENV

2. Check for overrides in docker-compose.yml:
   ```yaml
   # This will override .env values
   environment:
     - SERVICE_MODE=all
   ```

3. Remove overrides if you want .env to take precedence

### Issue: Cannot Find External Services

**Symptom:** Container cannot connect to host services (like external LiteLLM)

**Solutions:**

1. Use `host.docker.internal` in .env:
   ```bash
   OPENAI_BASE_URL=http://host.docker.internal:4000
   ```

2. Verify extra_hosts in docker-compose.yml:
   ```yaml
   extra_hosts:
     - "host.docker.internal:host-gateway"
   ```

3. Test connectivity from container:
   ```bash
   docker compose exec ii-researcher curl http://host.docker.internal:4000/health
   ```

### Issue: Sensitive Data in Git

**Symptom:** Accidentally committed .env file

**Solutions:**

1. Verify .gitignore:
   ```bash
   cat .gitignore | grep .env
   # Should contain: .env*
   # Note: env.test is OK to commit (placeholder values only)
   ```

2. Remove .env from git if committed:
   ```bash
   git rm --cached .env
   git commit -m "Remove .env from repository"
   ```

3. Rotate exposed API keys immediately

**Note:** Only `env.test` should be committed. All other `.env*` files are gitignored.

## Best Practices

1. **Version Control Strategy**
   - ✅ Commit `env.test` with placeholder values
   - ✅ Keep `env.template` as reference documentation
   - ❌ Never commit `.env` or `.env.*` with real API keys

2. **Use env.test as Base** - Copy `env.test` for local `.env` or environment-specific configs

3. **Test First** - Verify deployment works with `env.test` before using real keys

4. **Document Requirements** - Keep `env.test` and `env.template` updated with all variables

5. **Use Separate Configs** - Different `.env.*` files for dev/staging/prod

6. **Validate on Startup** - Check for required variables before running

7. **Rotate Keys Regularly** - Especially for production environments

8. **Use Secrets Management** - For production, consider Docker secrets or vault

## See Also

- [Docker Compose Quick Start](QUICKSTART.md)
- [Docker Deployment Guide](DOCKER.md)
- [Architecture Documentation](../architecture/ARCHITECTURE.md)
- [Main README](../../README.md)

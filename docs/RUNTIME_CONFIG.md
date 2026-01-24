# Runtime Configuration Implementation

## Overview

The ii-researcher frontend now supports **runtime configuration** for the API URL. This allows changing the API URL by modifying an environment variable and restarting the container - **no rebuild required**.

## Problem Solved

- **Before**: `NEXT_PUBLIC_API_URL` was hardcoded at build time, causing `undefined` errors when accessing from different IPs
- **After**: `API_URL` is configurable at runtime, works on any hostname/IP without rebuilding

## Implementation Details

### Code Changes

#### 1. Frontend Runtime Configuration (`frontend/app/layout.tsx`)
- Added `export const dynamic = 'force-dynamic'` to prevent build-time rendering
- Injects `window.__RUNTIME_CONFIG__` into HTML with server-side environment variables
- Reads `API_URL` (preferred) or falls back to `NEXT_PUBLIC_API_URL` (backwards compatibility)

#### 2. Configuration Helper (`frontend/lib/config.ts`)
- New helper function `getApiUrl()` to read runtime config from `window.__RUNTIME_CONFIG__`
- Type-safe access with TypeScript definitions
- Multi-level fallback: runtime config → build-time var → default

#### 3. Frontend API Calls (`frontend/app/page.tsx`)
- Replaced direct `process.env.NEXT_PUBLIC_API_URL` with `getApiUrl()`
- Now uses runtime-injected configuration

#### 4. Environment Configuration (`env.template`, `env.test`)
- Changed from `NEXT_PUBLIC_API_URL` to `API_URL`
- Added documentation and examples for different use cases
- Fixed incomplete URL in `env.test` (`http://localhost:` → `http://localhost:8000`)

#### 5. Container Entrypoint (`container/entrypoint.sh`)
- Auto-detects and passes `API_URL` to frontend Node.js process
- Backwards compatible with `NEXT_PUBLIC_API_URL`
- Logs configured API URL for debugging

#### 6. Package Update (`pyproject.toml`, `ii_researcher/tool_clients/search_client.py`)
- Migrated from deprecated `duckduckgo-search` to `ddgs` package
- Updated import statements to eliminate runtime warnings

## Configuration

### Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `API_URL` | Backend API URL (runtime) | `http://10.1.1.45:8001` | Yes |
| `NEXT_PUBLIC_API_URL` | Legacy API URL (build-time) | `http://localhost:8000` | No (backwards compat) |

### Docker Compose Configuration

```yaml
services:
  ii-researcher:
    image: nurol/ii-researcher:latest
    environment:
      - API_URL=http://10.1.1.45:8001  # Change this without rebuilding!
      - SERVICE_MODE=all
    ports:
      - "3001:3000"  # Frontend
      - "8001:8000"  # API
```

### Usage Examples

**External Access (IP Address)**
```bash
API_URL=http://10.1.1.45:8001
```

**Local Access**
```bash
API_URL=http://localhost:8001
```

**Domain Name**
```bash
API_URL=http://research.example.com:8001
```

**Behind Reverse Proxy**
```bash
API_URL=/api
```

## Verification

### 1. Check Runtime Config Injection
Open browser developer tools, view page source:
```html
<script>window.__RUNTIME_CONFIG__ = {"apiUrl":"http://10.1.1.45:8001"};</script>
```

### 2. Verify API Calls
Submit a question, check Network tab:
- Expected: `http://10.1.1.45:8001/search?question=...`
- Not: `http://localhost:8000/...` or `undefined/...`

### 3. Check Container Logs
```bash
docker logs ii-researcher | grep "API URL"
# Expected output:
# [INFO] Frontend will use API URL: http://10.1.1.45:8001
# [INFO]   → API URL configured as: http://10.1.1.45:8001
```

## Technical Notes

- **Force Dynamic Rendering**: Prevents Next.js from pre-rendering pages at build time
- **Server-Side Injection**: Configuration injected on each request, ensuring runtime values
- **Next.js Standalone**: Compatible with standalone output mode
- **No CORS Issues**: Configuration embedded in HTML, no additional API calls needed
- **Backwards Compatible**: Existing `NEXT_PUBLIC_API_URL` usage still works

## Migration Guide

### For Existing Deployments

1. Update environment configuration:
   ```bash
   # In env.test or .env
   # Change:
   NEXT_PUBLIC_API_URL=http://localhost:8000
   # To:
   API_URL=http://your-ip:8001
   ```

2. Rebuild and restart:
   ```bash
   docker compose build
   docker compose up -d
   ```

3. Verify configuration:
   ```bash
   docker logs ii-researcher | grep "API URL"
   ```

### For Pre-Built Images

Once the image is published with these changes:
```bash
# Just update and restart - no rebuild needed!
docker compose pull
docker compose up -d
```

## Additional Fixes

### DuckDuckGo Package Update

Migrated from deprecated `duckduckgo-search` to `ddgs`:
- Updated `pyproject.toml`: `ddgs>=1.0.0`
- Updated import in `search_client.py`: `from ddgs import DDGS`
- Eliminates runtime deprecation warning

### vLLM Endpoint Configuration

Fixed 404 error with vLLM integration:
- Updated `OPENAI_BASE_URL` to include `/v1` prefix
- Changed from: `http://host.docker.internal:8120`
- Changed to: `http://host.docker.internal:8120/v1`
- Ensures correct OpenAI-compatible API endpoint resolution

## Files Changed

- `frontend/app/layout.tsx` - Runtime config injection
- `frontend/lib/config.ts` - Configuration helper (new)
- `frontend/app/page.tsx` - Use runtime config
- `env.template` - Updated variable name and documentation
- `env.test` - Updated variable name, fixed URL, added examples
- `container/entrypoint.sh` - Pass API_URL to frontend process
- `pyproject.toml` - Updated ddgs package
- `ii_researcher/tool_clients/search_client.py` - Updated import

## Status

✅ **Implemented and Tested**
- Runtime configuration works correctly
- API URL changes without rebuild (verified)
- Backwards compatible with existing configurations
- DuckDuckGo package updated
- vLLM endpoint fixed

---

**Last Updated**: January 23, 2026  
**Version**: 0.1.5+runtime-config

# Multi-stage Dockerfile for II-Researcher
# Supports running all services in a single container or individual services
# Multi-architecture support: amd64, arm64

# ============================================================================
# Version Arguments
# ============================================================================
ARG PYTHON_VERSION=3.12.12
ARG DEBIAN_VERSION=bookworm
ARG NODE_VERSION=25.3.0-alpine3.22

# ============================================================================
# Stage 1: Frontend Builder
# ============================================================================
FROM node:${NODE_VERSION} AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package.json frontend/yarn.lock* frontend/package-lock.json* frontend/pnpm-lock.yaml* ./

# Install dependencies
RUN apk add --no-cache libc6-compat && \
    if [ -f yarn.lock ]; then yarn --frozen-lockfile; \
    elif [ -f package-lock.json ]; then npm ci; \
    elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm i --frozen-lockfile; \
    else echo "Lockfile not found." && exit 1; \
    fi

# Copy frontend source code
COPY frontend/ ./

# Build frontend
RUN if [ -f yarn.lock ]; then yarn build; \
    elif [ -f package-lock.json ]; then npm run build; \
    elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm run build; \
    else echo "Lockfile not found." && exit 1; \
    fi

# ============================================================================
# Stage 2: Python Base
# ============================================================================
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_VERSION} AS python-base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Stage 3: Python Dependencies
# ============================================================================
FROM python-base AS python-deps

WORKDIR /tmp

# Copy Python dependency files
COPY pyproject.toml ./

# Install Python dependencies (project only, no 3rd-party services)
RUN pip install --upgrade pip setuptools wheel && \
    pip install . && \
    pip install uvicorn

# ============================================================================
# Stage 4: Node.js Runtime (for frontend)
# ============================================================================
FROM node:${NODE_VERSION} AS node-runtime

# Create frontend user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

WORKDIR /app/frontend

# Copy built frontend from builder
COPY --from=frontend-builder --chown=nextjs:nodejs /app/frontend/public ./public
COPY --from=frontend-builder --chown=nextjs:nodejs /app/frontend/.next/standalone ./
COPY --from=frontend-builder --chown=nextjs:nodejs /app/frontend/.next/static ./.next/static

# ============================================================================
# Stage 5: Final Runtime Image
# ============================================================================
FROM python-base AS runtime

# Build arguments
ARG VERSION=0.0.1
ARG GIT_COMMIT=unknown
ARG BUILD_DATE=unknown

# Labels
LABEL org.opencontainers.image.title="II-Researcher" \
      org.opencontainers.image.description="Deep search agent with multiple services" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.vendor="Intelligent Internet" \
      org.opencontainers.image.source="https://github.com/Intelligent-Internet/ii-researcher"

# Install Node.js for frontend
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create application directory structure
WORKDIR /app

# Copy Python dependencies from deps stage
ENV PYTHON_SHORT_VERSION=${PYTHON_VERSION%.*}
COPY --from=python-deps /usr/local/lib/python${PYTHON_SHORT_VERSION}/site-packages /usr/local/lib/python${PYTHON_SHORT_VERSION}/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Copy application code
COPY pyproject.toml ./
COPY ii_researcher/ ./ii_researcher/
COPY api.py ./
COPY mcp/ ./mcp/

# Install the package
RUN pip install --no-deps -e .

# Copy frontend from node-runtime stage
COPY --from=node-runtime /app/frontend ./frontend

# Copy entrypoint script
COPY container/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy supervisor configuration
COPY container/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create logs directory
RUN mkdir -p /var/log/supervisor /var/log/ii-researcher

# Expose ports
# 3000 - Frontend
# 8000 - API Server
# 8765 - MCP Server (HTTP mode)
EXPOSE 3000 8000 8765

# Environment variables with defaults
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PYTHONUNBUFFERED=1 \
    SERVICE_MODE=all

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden)
CMD ["all"]

# Makefile for II-Researcher
# Builds and manages Docker containers for multi-architecture deployment

# ============================================================================
# Configuration
# ============================================================================

# Container registry and image name
REGISTRY := registry.tunnel.xellence.us
IMAGE_NAME := nurol/ii-researcher
IMAGE_NAME_CORE := nurol/ii-researcher-core
IMAGE_NAME_SVC := nurol/ii-researcher-svc
PLATFORMS := linux/amd64,linux/arm64

# Get version from git tag, default to v0.0.1 if no tag exists
GIT_TAG := $(shell git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.1")
VERSION := $(GIT_TAG)

# Remove 'v' prefix if present for image tag
IMAGE_VERSION := $(patsubst v%,%,$(VERSION))
FULL_IMAGE := $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_VERSION)
LATEST_IMAGE := $(REGISTRY)/$(IMAGE_NAME):latest
FULL_IMAGE_CORE := $(REGISTRY)/$(IMAGE_NAME_CORE):$(IMAGE_VERSION)
LATEST_IMAGE_CORE := $(REGISTRY)/$(IMAGE_NAME_CORE):latest
FULL_IMAGE_SVC := $(REGISTRY)/$(IMAGE_NAME_SVC):$(IMAGE_VERSION)
LATEST_IMAGE_SVC := $(REGISTRY)/$(IMAGE_NAME_SVC):latest

# Docker build context
DOCKER_DIR := docker
DOCKERFILE := $(DOCKER_DIR)/Dockerfile
DOCKERFILE_CORE := $(DOCKER_DIR)/Dockerfile.core
DOCKERFILE_SVC := $(DOCKER_DIR)/Dockerfile.svc

# Build arguments
BUILD_DATE := $(shell date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# ============================================================================
# Phony Targets
# ============================================================================

.PHONY: all version help build-local build-multi push clean clean-all test \
        build-core-local build-core-multi push-core \
        build-svc-local build-svc-multi push-svc \
        build-all-local push-all

# ============================================================================
# Default Target
# ============================================================================

all: build-local

# ============================================================================
# Help Target
# ============================================================================

help:
	@echo "II-Researcher Docker Build System"
	@echo "=================================="
	@echo ""
	@echo "Main targets:"
	@echo "  make version        - Display current version from git tag"
	@echo "  make build-local    - Build all-in-one image (current architecture)"
	@echo "  make build-multi    - Build all-in-one multi-arch images"
	@echo "  make push           - Build and push all-in-one to registry"
	@echo "  make clean          - Clean up Docker build cache"
	@echo "  make test           - Run container locally for testing"
	@echo ""
	@echo "Layered architecture targets:"
	@echo "  make build-core-local  - Build Core layer (local)"
	@echo "  make build-svc-local   - Build Service layer (local)"
	@echo "  make build-all-local   - Build all layers (local)"
	@echo "  make push-core         - Build and push Core layer"
	@echo "  make push-svc          - Build and push Service layer"
	@echo "  make push-all          - Build and push all layers"
	@echo ""
	@echo "Configuration:"
	@echo "  Registry:      $(REGISTRY)"
	@echo "  All-in-one:    $(IMAGE_NAME)"
	@echo "  Core:          $(IMAGE_NAME_CORE)"
	@echo "  Service:       $(IMAGE_NAME_SVC)"
	@echo "  Version:       $(VERSION)"
	@echo "  Platforms:     $(PLATFORMS)"
	@echo ""
	@echo "Examples:"
	@echo "  make build-local          # Build all-in-one image"
	@echo "  make build-all-local      # Build layered architecture"
	@echo "  make push-all             # Push all to registry"

# ============================================================================
# Version Target
# ============================================================================

version:
	@echo "Current version: $(VERSION)"
	@echo "Image tag: $(IMAGE_VERSION)"
	@echo "Full image: $(FULL_IMAGE)"
	@echo "Git commit: $(GIT_COMMIT)"
	@echo "Build date: $(BUILD_DATE)"

# ============================================================================
# Build Targets
# ============================================================================

# Build local image for testing (single architecture)
build-local:
	@echo "============================================"
	@echo "Building local container image for testing"
	@echo "Version: $(VERSION)"
	@echo "Image: $(IMAGE_NAME):$(IMAGE_VERSION)"
	@echo "============================================"
	@docker build \
		--file $(DOCKERFILE) \
		--build-arg VERSION=$(IMAGE_VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--tag $(IMAGE_NAME):$(IMAGE_VERSION) \
		--tag $(IMAGE_NAME):latest \
		.
	@echo ""
	@echo "✓ Local image built successfully!"
	@echo "  Image: $(IMAGE_NAME):$(IMAGE_VERSION)"
	@echo "  Image: $(IMAGE_NAME):latest"
	@echo ""
	@echo "To test the image:"
	@echo "  make test"
	@echo "  or"
	@echo "  docker compose up"

# Build multi-architecture images (without pushing)
build-multi:
	@echo "============================================"
	@echo "Building multi-architecture images"
	@echo "Version: $(VERSION)"
	@echo "Platforms: $(PLATFORMS)"
	@echo "============================================"
	@docker buildx build \
		--platform $(PLATFORMS) \
		--file $(DOCKERFILE) \
		--build-arg VERSION=$(IMAGE_VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--tag $(FULL_IMAGE) \
		--tag $(LATEST_IMAGE) \
		.
	@echo ""
	@echo "✓ Multi-architecture images built successfully!"
	@echo "  Note: Images are built but not pushed to registry"
	@echo "  Use 'make push' to build and push to registry"

# ============================================================================
# Push Target
# ============================================================================

# Build and push multi-architecture images to registry
push:
	@echo "============================================"
	@echo "Building and pushing to registry"
	@echo "Version: $(VERSION)"
	@echo "Registry: $(REGISTRY)"
	@echo "Image: $(IMAGE_NAME):$(IMAGE_VERSION)"
	@echo "Platforms: $(PLATFORMS)"
	@echo "============================================"
	@echo ""
	@echo "Creating buildx builder if not exists..."
	@docker buildx create --name ii-researcher-builder --use 2>/dev/null || docker buildx use ii-researcher-builder
	@echo ""
	@echo "Building and pushing multi-architecture images..."
	@docker buildx build \
		--platform $(PLATFORMS) \
		--file $(DOCKERFILE) \
		--build-arg VERSION=$(IMAGE_VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--tag $(FULL_IMAGE) \
		--tag $(LATEST_IMAGE) \
		--push \
		.
	@echo ""
	@echo "✓ Images pushed successfully!"
	@echo "  $(FULL_IMAGE)"
	@echo "  $(LATEST_IMAGE)"
	@echo ""
	@echo "To pull and run the image:"
	@echo "  docker pull $(FULL_IMAGE)"
	@echo "  docker run -p 3000:3000 -p 8000:8000 -p 4000:4000 --env-file .env $(FULL_IMAGE)"

# ============================================================================
# Test Target
# ============================================================================

# Run container locally for testing
test:
	@echo "============================================"
	@echo "Running container for testing"
	@echo "Image: $(IMAGE_NAME):$(IMAGE_VERSION)"
	@echo "============================================"
	@echo ""
	@echo "Starting container with all services..."
	@echo "Frontend will be available at: http://localhost:3000"
	@echo "API will be available at: http://localhost:8000"
	@echo "LiteLLM will be available at: http://localhost:4000"
	@echo ""
	@docker run -it --rm \
		-p 3000:3000 \
		-p 8000:8000 \
		-p 4000:4000 \
		--env-file .env \
		$(IMAGE_NAME):$(IMAGE_VERSION)

# ============================================================================
# Clean Targets
# ============================================================================

# Clean up Docker build cache and dangling images
clean:
	@echo "============================================"
	@echo "Cleaning Docker build cache..."
	@echo "============================================"
	@echo ""
	@echo "Removing build cache..."
	@docker buildx prune -f
	@echo ""
	@echo "Removing dangling images..."
	@docker image prune -f
	@echo ""
	@echo "Removing dangling build cache..."
	@docker builder prune -f
	@echo ""
	@echo "✓ Docker build cache cleaned!"
	@echo ""
	@echo "Remaining images:"
	@docker images | grep -E "($(IMAGE_NAME)|REPOSITORY)" || echo "  No ii-researcher images found"

# Clean all Docker resources including volumes and networks
clean-all: clean
	@echo "============================================"
	@echo "Cleaning all Docker resources..."
	@echo "============================================"
	@echo ""
	@echo "WARNING: This will remove:"
	@echo "  - All stopped containers"
	@echo "  - All unused networks"
	@echo "  - All unused volumes"
	@echo "  - All dangling images"
	@echo ""
	@printf "Continue? [y/N] "; \
	read REPLY; \
	case "$$REPLY" in \
		[Yy]*) \
			echo "Removing all unused containers..."; \
			docker container prune -f; \
			echo ""; \
			echo "Removing all unused networks..."; \
			docker network prune -f; \
			echo ""; \
			echo "Removing all unused volumes..."; \
			docker volume prune -f; \
			echo ""; \
			echo "Removing all dangling images..."; \
			docker image prune -a -f; \
			echo ""; \
			echo "✓ All Docker resources cleaned!"; \
			;; \
		*) \
			echo "Clean cancelled."; \
			;; \
	esac

# ============================================================================
# Docker Compose Targets
# ============================================================================

# Start services with docker-compose
up:
	@echo "Starting services with docker-compose..."
	@docker compose up -d
	@echo ""
	@echo "✓ Services started!"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API: http://localhost:8000"
	@echo "  MCP: http://localhost:8765"

# Stop services
down:
	@echo "Stopping services..."
	@docker compose down
	@echo "✓ Services stopped!"

# View logs
logs:
	@docker compose logs -f

# ============================================================================
# Development Targets
# ============================================================================

# Install development dependencies
dev-install:
	@echo "Installing development dependencies..."
	@pip install -e ".[dev]"
	@echo "✓ Development dependencies installed!"

# Run tests
dev-test:
	@echo "Running tests..."
	@pytest tests/
	@echo "✓ Tests completed!"

# Run linter
dev-lint:
	@echo "Running linter..."
	@flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "✓ Linting completed!"

# Format code
dev-format:
	@echo "Formatting code..."
	@black .
	@isort .
	@echo "✓ Code formatted!"

# ============================================================================
# Info Targets
# ============================================================================

# Display container information
info:
	@echo "II-Researcher Container Information"
	@echo "===================================="
	@echo ""
	@echo "Version Information:"
	@echo "  Git Tag:       $(GIT_TAG)"
	@echo "  Image Version: $(IMAGE_VERSION)"
	@echo "  Git Commit:    $(GIT_COMMIT)"
	@echo "  Build Date:    $(BUILD_DATE)"
	@echo ""
	@echo "Image Configuration:"
	@echo "  Registry:      $(REGISTRY)"
	@echo "  Image Name:    $(IMAGE_NAME)"
	@echo "  Full Image:    $(FULL_IMAGE)"
	@echo "  Latest Tag:    $(LATEST_IMAGE)"
	@echo "  Platforms:     $(PLATFORMS)"
	@echo ""
	@echo "Local Images:"
	@docker images | grep -E "($(IMAGE_NAME)|REPOSITORY)" || echo "  No local images found"
	@echo ""
	@echo "Running Containers:"
	@docker ps --filter ancestor=$(IMAGE_NAME) --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  No running containers"

# Check Docker environment
check:
	@echo "Checking Docker environment..."
	@echo ""
	@echo "Docker version:"
	@docker --version
	@echo ""
	@echo "Docker Buildx:"
	@docker buildx version
	@echo ""
	@echo "Available builders:"
	@docker buildx ls
	@echo ""
	@echo "Current git tag: $(GIT_TAG)"
	@echo "Image version: $(IMAGE_VERSION)"
	@echo ""
	@echo "✓ Environment check complete!"

# ============================================================================
# Layered Architecture Build Targets
# ============================================================================

# Build Core Layer (local)
build-core-local:
	@echo "============================================"
	@echo "Building Core Layer (local)"
	@echo "Version: $(VERSION)"
	@echo "Image: $(IMAGE_NAME_CORE):$(IMAGE_VERSION)"
	@echo "============================================"
	@docker build \
		--file $(DOCKERFILE_CORE) \
		--build-arg VERSION=$(IMAGE_VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--tag $(IMAGE_NAME_CORE):$(IMAGE_VERSION) \
		--tag $(IMAGE_NAME_CORE):latest \
		.
	@echo ""
	@echo "✓ Core layer built successfully!"
	@echo "  Image: $(IMAGE_NAME_CORE):$(IMAGE_VERSION)"
	@echo "  Image: $(IMAGE_NAME_CORE):latest"

# Build Core Layer (multi-arch)
build-core-multi:
	@echo "============================================"
	@echo "Building Core Layer (multi-arch)"
	@echo "Version: $(VERSION)"
	@echo "Platforms: $(PLATFORMS)"
	@echo "============================================"
	@docker buildx build \
		--platform $(PLATFORMS) \
		--file $(DOCKERFILE_CORE) \
		--build-arg VERSION=$(IMAGE_VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--tag $(FULL_IMAGE_CORE) \
		--tag $(LATEST_IMAGE_CORE) \
		.
	@echo ""
	@echo "✓ Core layer multi-arch images built!"

# Push Core Layer
push-core:
	@echo "============================================"
	@echo "Building and pushing Core Layer"
	@echo "Version: $(VERSION)"
	@echo "Platforms: $(PLATFORMS)"
	@echo "============================================"
	@docker buildx create --name ii-researcher-builder --use 2>/dev/null || docker buildx use ii-researcher-builder
	@docker buildx build \
		--platform $(PLATFORMS) \
		--file $(DOCKERFILE_CORE) \
		--build-arg VERSION=$(IMAGE_VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--tag $(FULL_IMAGE_CORE) \
		--tag $(LATEST_IMAGE_CORE) \
		--push \
		.
	@echo ""
	@echo "✓ Core layer pushed successfully!"
	@echo "  $(FULL_IMAGE_CORE)"
	@echo "  $(LATEST_IMAGE_CORE)"

# Build Service Layer (local) - depends on core
build-svc-local: build-core-local
	@echo "============================================"
	@echo "Building Service Layer (local)"
	@echo "Version: $(VERSION)"
	@echo "Image: $(IMAGE_NAME_SVC):$(IMAGE_VERSION)"
	@echo "============================================"
	@docker build \
		--file $(DOCKERFILE_SVC) \
		--build-arg CORE_IMAGE=$(IMAGE_NAME_CORE):latest \
		--build-arg VERSION=$(IMAGE_VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--tag $(IMAGE_NAME_SVC):$(IMAGE_VERSION) \
		--tag $(IMAGE_NAME_SVC):latest \
		.
	@echo ""
	@echo "✓ Service layer built successfully!"
	@echo "  Image: $(IMAGE_NAME_SVC):$(IMAGE_VERSION)"
	@echo "  Image: $(IMAGE_NAME_SVC):latest"

# Build Service Layer (multi-arch)
build-svc-multi:
	@echo "============================================"
	@echo "Building Service Layer (multi-arch)"
	@echo "Version: $(VERSION)"
	@echo "Platforms: $(PLATFORMS)"
	@echo "============================================"
	@docker buildx build \
		--platform $(PLATFORMS) \
		--file $(DOCKERFILE_SVC) \
		--build-arg CORE_IMAGE=$(LATEST_IMAGE_CORE) \
		--build-arg VERSION=$(IMAGE_VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--tag $(FULL_IMAGE_SVC) \
		--tag $(LATEST_IMAGE_SVC) \
		.
	@echo ""
	@echo "✓ Service layer multi-arch images built!"

# Push Service Layer - requires core to be pushed first
push-svc: push-core
	@echo "============================================"
	@echo "Building and pushing Service Layer"
	@echo "Version: $(VERSION)"
	@echo "Platforms: $(PLATFORMS)"
	@echo "============================================"
	@docker buildx create --name ii-researcher-builder --use 2>/dev/null || docker buildx use ii-researcher-builder
	@docker buildx build \
		--platform $(PLATFORMS) \
		--file $(DOCKERFILE_SVC) \
		--build-arg CORE_IMAGE=$(LATEST_IMAGE_CORE) \
		--build-arg VERSION=$(IMAGE_VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--tag $(FULL_IMAGE_SVC) \
		--tag $(LATEST_IMAGE_SVC) \
		--push \
		.
	@echo ""
	@echo "✓ Service layer pushed successfully!"
	@echo "  $(FULL_IMAGE_SVC)"
	@echo "  $(LATEST_IMAGE_SVC)"

# Build all layers locally
build-all-local: build-core-local build-svc-local build-local
	@echo ""
	@echo "============================================"
	@echo "✓ All layers built successfully!"
	@echo "============================================"
	@echo "Images created:"
	@echo "  Core:       $(IMAGE_NAME_CORE):$(IMAGE_VERSION)"
	@echo "  Service:    $(IMAGE_NAME_SVC):$(IMAGE_VERSION)"
	@echo "  All-in-one: $(IMAGE_NAME):$(IMAGE_VERSION)"

# Push all layers
push-all: push-core push-svc push
	@echo ""
	@echo "============================================"
	@echo "✓ All layers pushed successfully!"
	@echo "============================================"
	@echo "Registry images:"
	@echo "  Core:       $(FULL_IMAGE_CORE)"
	@echo "  Service:    $(FULL_IMAGE_SVC)"
	@echo "  All-in-one: $(FULL_IMAGE)"


# Docker Build and Push Guide

This document details how to build and push multiplatform Docker images for Suggesterr to Docker Hub.

## Prerequisites

1. Docker Desktop installed with buildx support
2. Docker Hub account with push access to the repository
3. Logged into Docker Hub (`docker login`)

## Building Multiplatform Images

### 1. Set Up Docker Buildx

First, create and use a buildx builder instance for multiplatform builds:

```bash
# Create a new builder instance
docker buildx create --name multiplatform-builder --use --bootstrap

# Or use existing builder
docker buildx use multiplatform-builder

# Verify builder is ready
docker buildx inspect --bootstrap
```

The builder should show support for multiple platforms including:
- linux/amd64
- linux/arm64
- linux/arm/v7
- linux/arm/v6

### 2. Build and Push in One Command

The most efficient way is to build and push simultaneously:

```bash
# Build and push multiplatform image
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f Dockerfile.allinone \
  -t casey073/suggesterr:test \
  --push \
  .
```

**Breakdown of the command:**
- `--platform linux/amd64,linux/arm64`: Build for both AMD64 and ARM64 architectures
- `-f Dockerfile.allinone`: Use the all-in-one Dockerfile (includes PostgreSQL, Redis, Nginx)
- `-t casey073/suggesterr:test`: Tag the image
- `--push`: Push to Docker Hub after building
- `.`: Build context is current directory

### 3. Alternative: Build Locally First

If you want to test locally before pushing:

```bash
# Build for current platform only and load to local Docker
docker buildx build \
  -f Dockerfile.allinone \
  -t casey073/suggesterr:test \
  --load \
  .

# Test the image
docker run --rm -d --name test-container \
  -p 8080:8000 \
  -e DEBUG=True \
  -e TMDB_API_KEY=test \
  -e GOOGLE_GEMINI_API_KEY=test \
  casey073/suggesterr:test

# Check logs
docker logs test-container

# Test health endpoint
curl http://localhost:8080/health/

# Clean up
docker stop test-container
```

## Available Dockerfiles

### Dockerfile.allinone (Recommended)
- **Purpose**: All-in-one container for easy deployment
- **Includes**: PostgreSQL, Redis, Nginx, Django app
- **Use case**: Home servers, single-node deployments
- **Size**: ~1.5GB compressed

### Dockerfile (Standard)
- **Purpose**: Application-only container
- **Requires**: External PostgreSQL and Redis
- **Use case**: Kubernetes, Docker Swarm, microservices
- **Size**: ~500MB compressed

## Pushing Different Tags

```bash
# Latest tag (use with caution in production)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f Dockerfile.allinone \
  -t casey073/suggesterr:latest \
  --push \
  .

# Version tag
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f Dockerfile.allinone \
  -t casey073/suggesterr:v1.0.0 \
  --push \
  .

# Multiple tags in one build
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f Dockerfile.allinone \
  -t casey073/suggesterr:latest \
  -t casey073/suggesterr:v1.0.0 \
  -t casey073/suggesterr:stable \
  --push \
  .
```

## Verifying the Push

### 1. Check Image Manifest

```bash
# Inspect the multiplatform manifest on Docker Hub
docker buildx imagetools inspect casey073/suggesterr:test
```

This shows all platforms available for the image.

### 2. Test Pull and Run

```bash
# Remove local image
docker rmi casey073/suggesterr:test

# Pull from Docker Hub
docker pull casey073/suggesterr:test

# Run the pulled image
docker run --rm -d --name verify-container \
  -p 8081:8000 \
  -e DEBUG=True \
  -e TMDB_API_KEY=test \
  -e GOOGLE_GEMINI_API_KEY=test \
  casey073/suggesterr:test

# Verify it's running
docker logs verify-container
curl http://localhost:8081/health/

# Clean up
docker stop verify-container
```

## Build Arguments and Optimizations

### Using Build Cache

```bash
# Build with cache mount for pip packages
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f Dockerfile.allinone \
  -t casey073/suggesterr:test \
  --cache-from type=registry,ref=casey073/suggesterr:buildcache \
  --cache-to type=registry,ref=casey073/suggesterr:buildcache,mode=max \
  --push \
  .
```

### Build Arguments

```bash
# Pass build arguments
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f Dockerfile.allinone \
  -t casey073/suggesterr:test \
  --build-arg PYTHON_VERSION=3.11 \
  --push \
  .
```

## Troubleshooting

### Builder Issues

```bash
# List all builders
docker buildx ls

# Remove problematic builder
docker buildx rm multiplatform-builder

# Create fresh builder
docker buildx create --name multiplatform-builder --use
```

### Platform-Specific Issues

```bash
# Build for single platform to debug
docker buildx build \
  --platform linux/arm64 \
  -f Dockerfile.allinone \
  -t casey073/suggesterr:test-arm64 \
  --load \
  .
```

### Authentication Issues

```bash
# Re-login to Docker Hub
docker logout
docker login --username casey073
```

## CI/CD Integration

For GitHub Actions or other CI/CD:

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v2

- name: Login to Docker Hub
  uses: docker/login-action@v2
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}

- name: Build and push
  uses: docker/build-push-action@v4
  with:
    context: .
    file: ./Dockerfile.allinone
    platforms: linux/amd64,linux/arm64
    push: true
    tags: |
      casey073/suggesterr:latest
      casey073/suggesterr:${{ github.sha }}
```

## Best Practices

1. **Always test locally** before pushing to production tags
2. **Use specific version tags** instead of only `:latest`
3. **Document build commands** in your release notes
4. **Monitor image sizes** - multiplatform builds can be large
5. **Use build cache** for faster subsequent builds
6. **Verify both platforms** work correctly after building

## Common Environment Variables for Testing

```bash
# Minimal test configuration
docker run --rm -d \
  -p 8000:8000 \
  -e DEBUG=True \
  -e TMDB_API_KEY=your-key \
  -e GOOGLE_GEMINI_API_KEY=your-key \
  -e ALLOWED_HOSTS=localhost,127.0.0.1 \
  casey073/suggesterr:test

# Full configuration example
docker run --rm -d \
  -p 8000:8000 \
  -e DEBUG=False \
  -e TMDB_API_KEY=your-key \
  -e GOOGLE_GEMINI_API_KEY=your-key \
  -e ALLOWED_HOSTS=example.com,www.example.com \
  -e DJANGO_SUPERUSER_USERNAME=admin \
  -e DJANGO_SUPERUSER_PASSWORD=secure-password \
  -e DJANGO_SUPERUSER_EMAIL=admin@example.com \
  -e JELLYFIN_URL=http://jellyfin:8096 \
  -e JELLYFIN_API_KEY=your-jellyfin-key \
  -v /path/to/config:/config \
  casey073/suggesterr:latest
```
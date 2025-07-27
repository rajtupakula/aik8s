#!/bin/bash

# Expert LLM System - Docker Build Script
# Builds optimized Docker images for different environments

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[BUILD]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default values
IMAGE_NAME="expert-llm-system"
TAG="latest"
BUILD_TYPE="production"
PUSH_TO_REGISTRY=false
REGISTRY=""
NO_CACHE=false

# Help function
show_help() {
    cat << EOF
Expert LLM System - Docker Build Script

Usage: $0 [OPTIONS]

Options:
    -n, --name NAME         Image name (default: expert-llm-system)
    -t, --tag TAG          Image tag (default: latest)
    -b, --build-type TYPE  Build type: production, development (default: production)
    -r, --registry URL     Push to registry after build
    -p, --push             Push to registry (requires -r)
    --no-cache             Build without using cache
    -h, --help             Show this help message

Examples:
    $0                                          # Build production image
    $0 -t v1.0.0                              # Build with specific tag
    $0 -b development                          # Build development image
    $0 -r docker.io/myorg -p                  # Build and push to registry
    $0 --no-cache -t latest                   # Build without cache

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -b|--build-type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -p|--push)
            PUSH_TO_REGISTRY=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate build type
if [[ ! "$BUILD_TYPE" =~ ^(production|development)$ ]]; then
    print_error "Invalid build type: $BUILD_TYPE. Must be 'production' or 'development'"
    exit 1
fi

# Set full image name
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$TAG"
else
    FULL_IMAGE_NAME="$IMAGE_NAME:$TAG"
fi

print_status "Building Expert LLM System Docker image..."
print_status "Image: $FULL_IMAGE_NAME"
print_status "Build type: $BUILD_TYPE"

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    print_error "Dockerfile not found in current directory"
    exit 1
fi

# Build arguments
BUILD_ARGS=""
if [ "$NO_CACHE" = true ]; then
    BUILD_ARGS="--no-cache"
fi

# Set target based on build type
case $BUILD_TYPE in
    "production")
        TARGET="application"
        ;;
    "development")
        TARGET="application"
        BUILD_ARGS="$BUILD_ARGS --build-arg INSTALL_DEV=true"
        ;;
esac

# Build the image
print_status "Starting Docker build..."
if docker build $BUILD_ARGS \
    --target $TARGET \
    --tag "$FULL_IMAGE_NAME" \
    --label "build.date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --label "build.type=$BUILD_TYPE" \
    --label "git.commit=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
    .; then
    
    print_success "Docker build completed successfully!"
else
    print_error "Docker build failed!"
    exit 1
fi

# Show image information
print_status "Image information:"
docker images "$FULL_IMAGE_NAME" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Test the image
print_status "Testing the built image..."
if docker run --rm "$FULL_IMAGE_NAME" health; then
    print_success "Image health check passed!"
else
    print_warning "Image health check failed, but continuing..."
fi

# Push to registry if requested
if [ "$PUSH_TO_REGISTRY" = true ]; then
    if [ -z "$REGISTRY" ]; then
        print_error "Registry URL required for push operation"
        exit 1
    fi
    
    print_status "Pushing image to registry: $REGISTRY"
    if docker push "$FULL_IMAGE_NAME"; then
        print_success "Image pushed successfully!"
    else
        print_error "Failed to push image to registry"
        exit 1
    fi
fi

# Create deployment helper script
print_status "Creating deployment helper script..."
cat > deploy-docker.sh << EOF
#!/bin/bash
# Auto-generated deployment script for Expert LLM System

set -e

echo "Deploying Expert LLM System..."

# Pull latest image (if from registry)
if [[ "$FULL_IMAGE_NAME" == *"/"* ]]; then
    docker pull "$FULL_IMAGE_NAME"
fi

# Stop existing container
docker stop expert-llm-system 2>/dev/null || true
docker rm expert-llm-system 2>/dev/null || true

# Run new container
docker run -d \\
    --name expert-llm-system \\
    --restart unless-stopped \\
    -p 8501:8501 \\
    -v expert-data:/app/data \\
    -v expert-logs:/app/logs \\
    -e LOG_LEVEL=INFO \\
    "$FULL_IMAGE_NAME"

echo "✅ Expert LLM System deployed successfully!"
echo "🌐 Access the dashboard at: http://localhost:8501"

# Show logs
echo "📋 Showing container logs..."
docker logs -f expert-llm-system
EOF

chmod +x deploy-docker.sh

print_success "Build process completed!"
print_status "Next steps:"
echo "  1. Test locally: docker run -p 8501:8501 $FULL_IMAGE_NAME"
echo "  2. Use docker-compose: docker-compose up"
echo "  3. Deploy with: ./deploy-docker.sh"
echo "  4. Access dashboard: http://localhost:8501"

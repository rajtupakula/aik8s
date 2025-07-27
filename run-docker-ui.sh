#!/bin/bash

# Expert LLM System - Docker UI Runner
# This script builds and runs the UI completely in Docker

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[DOCKER-UI]${NC} $1"
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

# Stop and remove existing container if it exists
print_status "Cleaning up existing containers..."
docker stop expert-llm-ui 2>/dev/null || true
docker rm expert-llm-ui 2>/dev/null || true

# Build the Docker image
print_status "Building Docker image..."
docker build -t expert-llm-system .

# Run the container
print_status "Starting Expert LLM System UI container..."
docker run -d \
    --name expert-llm-ui \
    -p 8501:8501 \
    -v "$(pwd)/src/data:/app/src/data" \
    -v "$(pwd)/logs:/app/logs" \
    expert-llm-system

# Wait a moment for the container to start
sleep 3

# Check if container is running
if docker ps | grep -q expert-llm-ui; then
    print_success "Container started successfully!"
    print_success "🌐 UI is now available at: http://localhost:8501"
    echo ""
    print_status "Container logs:"
    docker logs expert-llm-ui
    echo ""
    print_status "To view live logs: docker logs -f expert-llm-ui"
    print_status "To stop the container: docker stop expert-llm-ui"
else
    print_error "Failed to start container. Checking logs..."
    docker logs expert-llm-ui
    exit 1
fi

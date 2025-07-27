#!/bin/bash

# Simple Docker UI Starter
# Starts the Expert LLM System UI in Docker

echo "🐳 Starting Expert LLM System UI in Docker..."
echo "🔄 This will use the Docker image with all dependencies pre-installed"

# Stop any existing container
docker stop expert-llm-ui 2>/dev/null || true
docker rm expert-llm-ui 2>/dev/null || true

# Run the container
docker run -d \
    --name expert-llm-ui \
    -p 8501:8501 \
    expert-llm-system:latest

# Wait for container to start
sleep 5

# Check status
if docker ps | grep -q expert-llm-ui; then
    echo "✅ Expert LLM System UI is now running!"
    echo "🌐 Access the UI at: http://localhost:8501"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs: docker logs -f expert-llm-ui"
    echo "   Stop UI:   docker stop expert-llm-ui"
    echo ""
    docker logs expert-llm-ui --tail 20
else
    echo "❌ Failed to start container. Showing logs:"
    docker logs expert-llm-ui
fi

#!/bin/bash

# Expert LLM System - Quick Docker UI
# The simplest way to run the UI with Docker

echo "🚀 Quick Start - Expert LLM System UI"
echo ""

# Check if image exists
if ! docker images | grep -q expert-llm-system; then
    echo "❌ Docker image not found. Building now..."
    docker build -t expert-llm-system .
fi

echo "🔄 Starting container..."

# Clean up any existing container
docker stop expert-llm-ui 2>/dev/null || true
docker rm expert-llm-ui 2>/dev/null || true

# Run the new container
docker run -d \
    --name expert-llm-ui \
    -p 8501:8501 \
    -e STREAMLIT_SERVER_PORT=8501 \
    -e STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    -e STREAMLIT_SERVER_HEADLESS=true \
    expert-llm-system

echo "⏳ Waiting for UI to start..."
sleep 10

# Check if it's running
if docker ps | grep -q expert-llm-ui; then
    echo ""
    echo "✅ SUCCESS! Expert LLM System UI is running!"
    echo ""
    echo "🌐 Open your browser to: http://localhost:8501"
    echo ""
    echo "📋 Management commands:"
    echo "   • View logs:  docker logs -f expert-llm-ui"
    echo "   • Stop UI:    docker stop expert-llm-ui"
    echo "   • Restart:    docker restart expert-llm-ui"
    echo ""
    echo "📝 Recent logs:"
    docker logs expert-llm-ui --tail 10
else
    echo ""
    echo "❌ Container failed to start. Error logs:"
    docker logs expert-llm-ui
fi

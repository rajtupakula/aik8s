#!/bin/bash

echo "🚀 Starting Expert LLM System UI from Kubernetes"
echo "================================================"

# Stop any existing Docker containers
echo "🛑 Stopping Docker containers..."
docker stop expert-llm-ui 2>/dev/null || true
docker rm expert-llm-ui 2>/dev/null || true

# Check Kubernetes deployment status
echo "📊 Checking Kubernetes deployment..."
kubectl get pods -n expert-llm-system

# Verify service is available
echo "🌐 Checking service..."
kubectl get svc -n expert-llm-system

echo ""
echo "🔗 Setting up port forwarding..."
echo "   Access URL: http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""

# Start port forwarding
kubectl port-forward -n expert-llm-system svc/expert-llm-service 8501:8501

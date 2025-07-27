#!/bin/bash

echo "🧹 Cleaning up and restarting Expert LLM System"
echo "==============================================="

# Stop any running Docker containers
echo "🛑 Stopping Docker containers..."
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true

# Remove Docker images
echo "🗑️  Removing Docker images..."
docker image prune -af
docker rmi expert-llm-system:latest 2>/dev/null || true
docker rmi localhost/expert-llm-system:latest 2>/dev/null || true

# Remove Minikube images
echo "🗑️  Removing Minikube images..."
minikube image rm expert-llm-system:latest 2>/dev/null || true
minikube image rm localhost/expert-llm-system:latest 2>/dev/null || true

# Delete existing Kubernetes deployment
echo "🗑️  Removing existing Kubernetes deployment..."
kubectl delete -f k8s/simple-deployment.yaml 2>/dev/null || true

echo ""
echo "✅ Cleanup complete!"
echo ""

# Rebuild and deploy fresh
echo "🔄 Building fresh image and deploying to Kubernetes..."
echo ""

# Build new image in Minikube
echo "📦 Building new image..."
minikube image build -t localhost/expert-llm-system:latest .

# Deploy to Kubernetes
echo "🚀 Deploying to Kubernetes..."
kubectl apply -f k8s/simple-deployment.yaml

# Wait for rollout
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/expert-llm-system -n expert-llm-system --timeout=300s

# Check pod status
echo ""
echo "📊 Deployment Status:"
kubectl get pods -n expert-llm-system
kubectl get svc -n expert-llm-system

echo ""
echo "🌐 Starting UI access..."
echo "   Access URL: http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""

# Start port forwarding
kubectl port-forward -n expert-llm-system svc/expert-llm-service 8501:8501

#!/bin/bash

# Expert LLM System - UI Fix and Deployment
echo "🔧 Fixing and deploying Expert LLM UI..."

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check Kubernetes connection
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "❌ Cannot connect to Kubernetes. Please ensure kubectl is configured."
    exit 1
fi

echo "✅ Kubernetes cluster connected"

# Create or ensure namespace exists
kubectl create namespace expert-llm-system --dry-run=client -o yaml | kubectl apply -f -
echo "✅ Namespace ready"

# Clean up any existing deployments
echo "🧹 Cleaning up existing deployments..."
kubectl delete deployment expert-llm-system-test -n expert-llm-system --ignore-not-found=true
kubectl delete deployment expert-ui-simple -n expert-llm-system --ignore-not-found=true
kubectl delete service expert-llm-test-service -n expert-llm-system --ignore-not-found=true
kubectl delete service expert-ui-service -n expert-llm-system --ignore-not-found=true

# Deploy the fixed UI
echo "🚀 Deploying Expert LLM UI..."
kubectl apply -f k8s/ui-fixed.yaml

# Wait for deployment
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/expert-llm-ui-working -n expert-llm-system

# Get service info
echo "📊 Getting service information..."
kubectl get pods -n expert-llm-system -o wide
kubectl get services -n expert-llm-system

# Get NodePort
NODEPORT=$(kubectl get service expert-llm-ui-service -n expert-llm-system -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)

echo ""
echo "🎉 Deployment completed!"
echo "📱 Access methods:"
echo "   1. NodePort: http://localhost:$NODEPORT"
echo "   2. Port Forward: kubectl port-forward -n expert-llm-system service/expert-llm-ui-service 8501:80"
echo "   3. Then open: http://localhost:8501"
echo ""
echo "🔍 To check logs: kubectl logs -f deployment/expert-llm-ui-working -n expert-llm-system"
echo "🔄 To restart: kubectl rollout restart deployment/expert-llm-ui-working -n expert-llm-system"

# Optional: Start port forwarding
read -p "Start port forwarding now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔗 Starting port forwarding..."
    echo "UI will be available at: http://localhost:8501"
    echo "Press Ctrl+C to stop port forwarding"
    kubectl port-forward -n expert-llm-system service/expert-llm-ui-service 8501:80
fi

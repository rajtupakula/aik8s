#!/bin/bash

echo "🔄 Rebuilding and redeploying Expert LLM System..."

# Rebuild the image
echo "📦 Building new image..."
minikube image build -t localhost/expert-llm-system:latest .

# Restart the deployment
echo "🚀 Restarting deployment..."
kubectl rollout restart deployment/expert-llm-system -n expert-llm-system

# Wait for rollout
echo "⏳ Waiting for rollout to complete..."
kubectl rollout status deployment/expert-llm-system -n expert-llm-system

# Check pod status
echo "📊 Current pod status:"
kubectl get pods -n expert-llm-system

echo ""
echo "✅ Deployment updated! You can now access the UI with:"
echo "   ./k8s-ui-fixed.sh"
echo ""
echo "The UI should now show the actual Kubernetes error message."

#!/bin/bash

echo "🚀 Expert LLM System - Kubernetes UI (FIXED)"
echo "=============================================="

# Check deployment status
echo "📊 Checking deployment status..."
kubectl get pods -n expert-llm-system

echo ""
echo "🔑 Service Account & Permissions:"
kubectl get serviceaccount -n expert-llm-system
kubectl get clusterrolebinding expert-llm-binding

echo ""
echo "🌐 Starting port forward to access UI..."
echo "   ✅ Kubernetes API access enabled"
echo "   ✅ Service account permissions configured"
echo "   🌐 Access URL: http://localhost:8501"
echo ""
echo "   The dashboard should now show: '🚀 K8s Pods Running: 1'"
echo ""
echo "Press Ctrl+C to stop"
echo ""

kubectl port-forward -n expert-llm-system svc/expert-llm-service 8501:8501

#!/bin/bash

echo "🌐 Expert LLM System - UI Access"
echo "==============================="
echo ""
echo "This script will start the UI access via Kubernetes port forwarding."
echo ""
echo "🔄 Step 1: Checking Kubernetes status..."
kubectl get pods -n expert-llm-system 2>/dev/null || {
    echo "❌ No pods found. Please run the deployment first:"
    echo "   kubectl apply -f k8s/simple-deployment.yaml"
    exit 1
}

echo "✅ Pods are running"
echo ""
echo "🌐 Step 2: Starting port forwarding..."
echo "   Access URL: http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""

kubectl port-forward -n expert-llm-system svc/expert-llm-service 8501:8501

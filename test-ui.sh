#!/bin/bash

# Quick UI Test Script
echo "🧪 Testing Expert LLM UI..."

# Test 1: Check if namespace exists
echo "1. Checking namespace..."
if kubectl get namespace expert-llm-system >&/dev/null; then
    echo "✅ Namespace exists"
else
    echo "❌ Namespace missing - creating..."
    kubectl create namespace expert-llm-system
fi

# Test 2: Check if deployment exists and is ready
echo "2. Checking deployment status..."
if kubectl get deployment expert-llm-ui-working -n expert-llm-system >&/dev/null; then
    STATUS=$(kubectl get deployment expert-llm-ui-working -n expert-llm-system -o jsonpath='{.status.readyReplicas}')
    if [ "$STATUS" = "1" ]; then
        echo "✅ Deployment ready"
    else
        echo "⚠️ Deployment not ready, current status:"
        kubectl get pods -n expert-llm-system
    fi
else
    echo "❌ Deployment not found"
fi

# Test 3: Check service
echo "3. Checking service..."
if kubectl get service expert-llm-ui-service -n expert-llm-system >&/dev/null; then
    NODEPORT=$(kubectl get service expert-llm-ui-service -n expert-llm-system -o jsonpath='{.spec.ports[0].nodePort}')
    echo "✅ Service available on NodePort: $NODEPORT"
else
    echo "❌ Service not found"
fi

# Test 4: Test connectivity
echo "4. Testing connectivity..."
POD_NAME=$(kubectl get pods -n expert-llm-system -l app=expert-llm-ui -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$POD_NAME" ]; then
    echo "Testing connection to pod: $POD_NAME"
    if kubectl exec -n expert-llm-system "$POD_NAME" -- curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 | grep -q "200"; then
        echo "✅ UI is responding"
    else
        echo "⚠️ UI may not be fully ready yet"
        echo "Pod logs:"
        kubectl logs -n expert-llm-system "$POD_NAME" --tail=10
    fi
else
    echo "❌ No pod found"
fi

echo ""
echo "🎯 Next steps:"
echo "   Run: kubectl port-forward -n expert-llm-system service/expert-llm-ui-service 8501:80"
echo "   Then open: http://localhost:8501"

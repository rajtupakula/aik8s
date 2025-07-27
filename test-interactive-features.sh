#!/bin/bash

echo "🎯 Testing Interactive kubectl Features"
echo "======================================"

# Get current pod name
CURRENT_POD=$(kubectl get pods -n expert-llm-system --no-headers -o custom-columns=":metadata.name" | grep expert-llm-system | head -1)

echo "Current pod: $CURRENT_POD"
echo ""

echo "📊 Testing kubectl get commands..."
echo "1. All pods:"
kubectl get pods --all-namespaces

echo ""
echo "2. All services:"
kubectl get services --all-namespaces

echo ""
echo "3. Cluster nodes:"
kubectl get nodes

echo ""
echo "📋 Testing describe command..."
kubectl describe pod $CURRENT_POD -n expert-llm-system

echo ""
echo "📜 Testing logs command..."
kubectl logs $CURRENT_POD -n expert-llm-system --tail=20

echo ""
echo "🔍 Testing events..."
kubectl get events -n expert-llm-system --sort-by='.lastTimestamp'

echo ""
echo "🎯 Interactive features ready!"
echo "Now test in the UI:"
echo "- Smart Pod Correlation with pod: $CURRENT_POD"
echo "- Root Cause Analysis with various error patterns"
echo "- Timestamp correlation analysis"

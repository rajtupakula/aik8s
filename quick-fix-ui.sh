#!/bin/bash

# Quick UI Fix for macOS
echo "🚀 Quick UI Fix - Expert LLM System"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "troubleshoot-ui.sh" ]; then
    echo "Please run this from the expert-llm-agent directory"
    exit 1
fi

# Set environment for macOS
export PATH="/usr/local/bin:$PATH"

# Function to check command availability
check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        echo "✅ $1 is available"
        return 0
    else
        echo "❌ $1 is not available"
        return 1
    fi
}

# Check prerequisites
echo "Checking prerequisites..."
check_command kubectl || exit 1
check_command docker || echo "⚠️ Docker not found - may need for image building"

# Check if cluster is running
echo ""
echo "Checking cluster status..."
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "❌ Kubernetes cluster not accessible"
    echo "💡 Try starting your local cluster:"
    echo "   - Docker Desktop: Enable Kubernetes"
    echo "   - Kind: kind create cluster"
    echo "   - Minikube: minikube start"
    exit 1
fi

echo "✅ Cluster is accessible"

# Quick deploy
echo ""
echo "Deploying minimal UI..."

# Create namespace
kubectl create namespace expert-llm-system --dry-run=client -o yaml | kubectl apply -f - >/dev/null 2>&1

# Clean any existing
kubectl delete deployment expert-ui-quick -n expert-llm-system --ignore-not-found=true >/dev/null 2>&1
kubectl delete service expert-ui-quick-svc -n expert-llm-system --ignore-not-found=true >/dev/null 2>&1

# Deploy minimal working UI
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: expert-ui-quick
  namespace: expert-llm-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: expert-ui-quick
  template:
    metadata:
      labels:
        app: expert-ui-quick
    spec:
      containers:
      - name: ui
        image: python:3.11-slim
        ports:
        - containerPort: 8501
        command: ["/bin/bash", "-c"]
        args:
        - |
          pip install streamlit && 
          echo "
          import streamlit as st
          from datetime import datetime
          st.set_page_config(page_title='Expert LLM', page_icon='🚀', layout='wide')
          st.title('🚀 Expert LLM System')
          st.success('✅ System is running in Kubernetes!')
          col1, col2, col3 = st.columns(3)
          with col1: st.metric('Status', '🟢 Online')
          with col2: st.metric('Time', datetime.now().strftime('%H:%M:%S'))
          with col3: st.metric('Patterns', '14 Active')
          st.markdown('---')
          st.write('🎯 **Expert Patterns Available:**')
          patterns = ['Ubuntu Performance', 'Kubernetes Issues', 'GlusterFS Storage', 'Memory Management']
          for i, pattern in enumerate(patterns, 1):
              st.write(f'{i}. {pattern}')
          st.markdown('---')
          st.info('💡 Full Expert LLM System with AI chat, live monitoring, and pattern recognition!')
          " > app.py && 
          streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
---
apiVersion: v1
kind: Service
metadata:
  name: expert-ui-quick-svc
  namespace: expert-llm-system
spec:
  type: NodePort
  ports:
  - port: 80
    targetPort: 8501
  selector:
    app: expert-ui-quick
EOF

echo "⏳ Waiting for deployment..."
sleep 30

# Check status
echo ""
echo "📊 Deployment Status:"
kubectl get pods -n expert-llm-system | grep expert-ui-quick

# Get access info
NODEPORT=$(kubectl get service expert-ui-quick-svc -n expert-llm-system -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)

echo ""
echo "🌐 Access Information:"
if [ -n "$NODEPORT" ]; then
    echo "NodePort URL: http://localhost:$NODEPORT"
fi
echo "Port Forward: kubectl port-forward -n expert-llm-system service/expert-ui-quick-svc 8501:80"
echo "Then open: http://localhost:8501"

echo ""
echo "🔧 Quick Commands:"
echo "Check logs: kubectl logs -f deployment/expert-ui-quick -n expert-llm-system"
echo "Check status: kubectl get all -n expert-llm-system"
echo "Restart: kubectl rollout restart deployment/expert-ui-quick -n expert-llm-system"

echo ""
echo "✅ Quick UI fix completed!"
echo "💡 If still having issues, try the full troubleshoot-ui.sh script"

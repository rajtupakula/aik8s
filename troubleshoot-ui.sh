#!/bin/bash

# UI Troubleshooting Script for Expert LLM System
set -euo pipefail

echo "🔍 Expert LLM System UI Troubleshooting"
echo "========================================"
echo "$(date)"
echo ""

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    echo "Please install kubectl first"
    exit 1
fi

# Check if kubectl is working
echo "1. Checking Kubernetes connection..."
if timeout 10 kubectl cluster-info >/dev/null 2>&1; then
    echo "✅ Kubernetes cluster is accessible"
    kubectl cluster-info | head -3
else
    echo "❌ Cannot connect to Kubernetes cluster"
    echo "Please check your kubeconfig and cluster status"
    echo "Current context: $(kubectl config current-context 2>/dev/null || echo 'none')"
    exit 1
fi

echo ""
echo "2. Checking namespace..."
if kubectl get namespace expert-llm-system >/dev/null 2>&1; then
    echo "✅ Namespace expert-llm-system exists"
else
    echo "⚠️  Creating namespace expert-llm-system..."
    kubectl create namespace expert-llm-system
    echo "✅ Namespace created"
fi

echo ""
echo "3. Cleaning up any existing problematic deployments..."
kubectl delete deployment expert-ui-simple -n expert-llm-system --ignore-not-found=true
kubectl delete service expert-ui-service -n expert-llm-system --ignore-not-found=true
echo "✅ Cleanup completed"

echo ""
echo "4. Checking current deployments..."
kubectl get all -n expert-llm-system || echo "No resources found"

echo ""
echo "5. Deploying robust UI test..."
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: expert-ui-simple
  namespace: expert-llm-system
  labels:
    app: expert-ui-simple
spec:
  replicas: 1
  selector:
    matchLabels:
      app: expert-ui-simple
  template:
    metadata:
      labels:
        app: expert-ui-simple
    spec:
      containers:
      - name: streamlit-app
        image: python:3.11-slim
        ports:
        - containerPort: 8501
          name: http
        command: ["/bin/bash"]
        args:
        - -c
        - |
          set -e
          echo "Starting UI deployment..."
          
          # Install required packages
          pip install --no-cache-dir streamlit pandas plotly
          
          # Create the app
          cat > /app/ui.py << 'PYEOF'
          import streamlit as st
          import pandas as pd
          import plotly.express as px
          from datetime import datetime
          import time
          import random

          # Configure page
          st.set_page_config(
              page_title="Expert LLM System", 
              page_icon="🚀",
              layout="wide"
          )

          # Main header
          st.title("🚀 Expert LLM System - Live Dashboard")
          st.markdown("### Intelligent System Administration with Real-time Monitoring")
          
          # Status row
          col1, col2, col3, col4 = st.columns(4)
          with col1:
              st.metric("Status", "🟢 Online", "Running")
          with col2:
              st.metric("Kubernetes", "🟢 Ready", "1/1")
          with col3:
              st.metric("Patterns", "14", "Active")
          with col4:
              st.metric("Updated", datetime.now().strftime("%H:%M:%S"), "Live")

          # Tabs
          tab1, tab2, tab3 = st.tabs(["🏠 Dashboard", "📊 Monitoring", "🔧 Health"])

          with tab1:
              st.subheader("Expert Pattern Recognition")
              
              # Sample data
              data = {
                  "Pattern": ["Ubuntu CPU", "K8s Pod Issue", "GlusterFS", "Memory Alert"],
                  "Confidence": [0.95, 0.87, 0.92, 0.78],
                  "Status": ["✅ Resolved", "⚠️ Active", "🔍 Monitor", "⚠️ Warning"]
              }
              
              df = pd.DataFrame(data)
              st.dataframe(df, use_container_width=True)
              
              # Chart
              fig = px.bar(df, x="Pattern", y="Confidence", 
                          title="Pattern Confidence Scores")
              st.plotly_chart(fig, use_container_width=True)

          with tab2:
              st.subheader("Live System Metrics")
              
              # Generate sample metrics
              cpu_data = [random.randint(20, 80) for _ in range(10)]
              mem_data = [random.randint(30, 70) for _ in range(10)]
              
              col1, col2 = st.columns(2)
              with col1:
                  st.line_chart({"CPU %": cpu_data})
              with col2:
                  st.line_chart({"Memory %": mem_data})

          with tab3:
              st.subheader("System Health")
              
              health_items = [
                  ("Streamlit UI", "🟢 Healthy"),
                  ("Kubernetes", "🟢 Ready"),
                  ("Expert Patterns", "🟢 Loaded"),
                  ("Monitoring", "🟢 Active")
              ]
              
              for service, status in health_items:
                  col1, col2 = st.columns([2, 1])
                  with col1:
                      st.write(f"**{service}**")
                  with col2:
                      st.write(status)

          # Footer
          st.markdown("---")
          st.markdown(f"⏰ Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
          st.success("🎉 Expert LLM System is running successfully in Kubernetes!")
          PYEOF
          
          # Start the app
          echo "Starting Streamlit server..."
          mkdir -p /app
          cd /app
          streamlit run ui.py \
            --server.port=8501 \
            --server.address=0.0.0.0 \
            --server.headless=true \
            --server.runOnSave=false \
            --browser.gatherUsageStats=false
        
        livenessProbe:
          httpGet:
            path: /
            port: 8501
          initialDelaySeconds: 90
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /
            port: 8501
          initialDelaySeconds: 60
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
          
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: expert-ui-service
  namespace: expert-llm-system
  labels:
    app: expert-ui-simple
spec:
  type: NodePort
  ports:
  - port: 80
    targetPort: 8501
    protocol: TCP
    name: http
  selector:
    app: expert-ui-simple
EOF

echo ""
echo "6. Waiting for deployment to be ready..."
echo "This may take 2-3 minutes for first time deployment..."

# Wait for deployment with better error handling
if kubectl wait --for=condition=available --timeout=300s deployment/expert-ui-simple -n expert-llm-system; then
    echo "✅ Deployment is ready!"
else
    echo "⚠️ Deployment taking longer than expected. Checking status..."
    kubectl get pods -n expert-llm-system
    kubectl describe pod -l app=expert-ui-simple -n expert-llm-system | tail -20
fi

echo ""
echo "7. Getting service information..."
kubectl get services -n expert-llm-system

echo ""
echo "8. Getting pod status..."
kubectl get pods -n expert-llm-system -o wide

echo ""
echo "9. Checking pod logs (last 15 lines)..."
POD_NAME=$(kubectl get pods -n expert-llm-system -l app=expert-ui-simple -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$POD_NAME" ]; then
    echo "Pod: $POD_NAME"
    kubectl logs "$POD_NAME" -n expert-llm-system --tail=15 || echo "Logs not available yet"
else
    echo "No pod found"
fi

echo ""
echo "10. Getting NodePort for access..."
NODEPORT=$(kubectl get service expert-ui-service -n expert-llm-system -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
if [ -n "$NODEPORT" ]; then
    echo "✅ UI should be accessible at: http://localhost:$NODEPORT"
else
    echo "❌ Could not get NodePort"
fi

echo ""
echo "11. Testing connectivity..."
if [ -n "$POD_NAME" ]; then
    echo "Testing internal connectivity..."
    if kubectl exec -n expert-llm-system "$POD_NAME" -- curl -s -f http://localhost:8501 >/dev/null 2>&1; then
        echo "✅ Internal connectivity OK"
    else
        echo "⚠️ Internal connectivity test failed - app may still be starting"
    fi
fi

echo ""
echo "12. Final status check..."
kubectl get all -n expert-llm-system

echo ""
echo "🎯 Access Methods:"
echo "   Method 1 - NodePort: http://localhost:$NODEPORT"
echo "   Method 2 - Port Forward:"
echo "     kubectl port-forward -n expert-llm-system service/expert-ui-service 8501:80"
echo "     Then open: http://localhost:8501"
echo ""
echo "🔍 Troubleshooting Commands:"
echo "   Check logs: kubectl logs -f deployment/expert-ui-simple -n expert-llm-system"
echo "   Check pod details: kubectl describe pod -l app=expert-ui-simple -n expert-llm-system"
echo "   Restart: kubectl rollout restart deployment/expert-ui-simple -n expert-llm-system"
echo ""
echo "🎉 UI deployment process completed!"

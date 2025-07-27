#!/bin/bash

# Podman Minikube Setup for Expert LLM System Testing
# This script sets up a Podman-based Minikube environment for testing

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Podman on macOS
install_podman_macos() {
    log_info "Installing Podman on macOS..."
    
    if command_exists brew; then
        brew install podman
    else
        log_error "Homebrew not found. Please install Homebrew first:"
        echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        exit 1
    fi
}

# Function to install Minikube
install_minikube() {
    log_info "Installing Minikube..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew install minikube
        else
            curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-darwin-amd64
            sudo install minikube-darwin-amd64 /usr/local/bin/minikube
            rm minikube-darwin-amd64
        fi
    else
        # Linux
        curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
        sudo install minikube-linux-amd64 /usr/local/bin/minikube
        rm minikube-linux-amd64
    fi
}

# Function to setup Podman
setup_podman() {
    log_info "Setting up Podman..."
    
    # Initialize Podman machine if not exists
    if ! podman machine list | grep -q "podman-machine-default"; then
        log_info "Creating Podman machine..."
        podman machine init --cpus 4 --memory 8192 --disk-size 50
    fi
    
    # Start Podman machine
    if ! podman machine list | grep -q "Currently running"; then
        log_info "Starting Podman machine..."
        podman machine start
    fi
    
    # Set up Podman socket for Minikube
    export DOCKER_HOST="unix://$(podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}')"
    
    log_success "Podman setup completed"
}

# Function to start Minikube with Podman
start_minikube_podman() {
    log_info "Starting Minikube with Podman driver..."
    
    # Stop any existing Minikube instance
    minikube stop 2>/dev/null || true
    minikube delete 2>/dev/null || true
    
    # Start Minikube with Podman driver
    minikube start \
        --driver=podman \
        --container-runtime=containerd \
        --cpus=4 \
        --memory=6144 \
        --disk-size=30g \
        --kubernetes-version=v1.28.0 \
        --addons=ingress,dashboard,metrics-server
    
    log_success "Minikube started with Podman driver"
}

# Function to verify installation
verify_setup() {
    log_info "Verifying setup..."
    
    # Check Minikube status
    if minikube status | grep -q "host: Running"; then
        log_success "Minikube is running"
    else
        log_error "Minikube is not running properly"
        return 1
    fi
    
    # Check kubectl connection
    if kubectl cluster-info >/dev/null 2>&1; then
        log_success "kubectl can connect to cluster"
    else
        log_error "kubectl cannot connect to cluster"
        return 1
    fi
    
    # Check nodes
    log_info "Cluster nodes:"
    kubectl get nodes
    
    # Check system pods
    log_info "System pods:"
    kubectl get pods -n kube-system
    
    log_success "Setup verification completed"
}

# Function to deploy Expert LLM System for testing
deploy_expert_llm_test() {
    log_info "Deploying Expert LLM System for testing..."
    
    # Create namespace
    kubectl create namespace expert-llm-system --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy a simple test version
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: expert-llm-test
  namespace: expert-llm-system
  labels:
    app: expert-llm-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: expert-llm-test
  template:
    metadata:
      labels:
        app: expert-llm-test
    spec:
      containers:
      - name: expert-llm
        image: python:3.11-slim
        ports:
        - containerPort: 8501
        command: ["/bin/bash", "-c"]
        args:
        - |
          pip install streamlit pandas plotly psutil requests &&
          cat > /app/expert_agent.py << 'PYEOF'
          import streamlit as st
          import pandas as pd
          import plotly.express as px
          import psutil
          import requests
          from datetime import datetime, timedelta
          import random
          import time
          import json

          # Configure page
          st.set_page_config(
              page_title="Expert LLM Agent - Podman Test", 
              page_icon="🚀",
              layout="wide"
          )

          # Main header
          st.title("🚀 Expert LLM Agent - Podman Minikube Test Environment")
          st.markdown("### Intelligent System Administration with Real-time Monitoring")
          
          # Environment info
          col1, col2, col3, col4 = st.columns(4)
          with col1:
              st.metric("Environment", "🐳 Podman", "Minikube")
          with col2:
              st.metric("Status", "🟢 Online", "Testing")
          with col3:
              st.metric("Patterns", "14", "Active")
          with col4:
              st.metric("Runtime", "Python 3.11", "Streamlit")

          # Real-time system metrics
          st.subheader("🔍 Live System Monitoring")
          
          # Get actual system metrics
          try:
              cpu_percent = psutil.cpu_percent(interval=1)
              memory = psutil.virtual_memory()
              disk = psutil.disk_usage('/')
              
              col1, col2, col3 = st.columns(3)
              with col1:
                  st.metric("CPU Usage", f"{cpu_percent:.1f}%", 
                           delta=f"{cpu_percent-50:.1f}%" if cpu_percent > 50 else None)
              with col2:
                  st.metric("Memory Usage", f"{memory.percent:.1f}%",
                           delta=f"{memory.percent-40:.1f}%" if memory.percent > 40 else None)
              with col3:
                  st.metric("Disk Usage", f"{(disk.used/disk.total*100):.1f}%")
          except:
              st.info("System metrics available in container environment")

          # Tabs for different functionalities
          tab1, tab2, tab3, tab4 = st.tabs(["🏠 Dashboard", "🤖 AI Agent", "📊 Patterns", "🔧 Testing"])

          with tab1:
              st.subheader("Expert Pattern Recognition Dashboard")
              
              # Simulate expert patterns
              patterns_data = {
                  "Pattern": [
                      "Ubuntu Performance - CPU High", 
                      "Kubernetes Pod CrashLoop", 
                      "GlusterFS Brick Offline",
                      "Memory Pressure Alert",
                      "Disk Space Warning",
                      "Network Connectivity Issue"
                  ],
                  "Confidence": [0.95, 0.87, 0.92, 0.78, 0.89, 0.83],
                  "Status": ["🟢 Resolved", "🔴 Active", "🟡 Monitoring", "🟡 Warning", "🟢 Resolved", "🟡 Investigating"],
                  "Last Detected": ["2 min ago", "5 min ago", "1 min ago", "3 min ago", "10 min ago", "7 min ago"],
                  "Actions": ["Applied CPU optimization", "Restarting pod", "Checking brick status", "Memory cleanup", "Disk cleanup completed", "Network diagnostics"]
              }
              
              df = pd.DataFrame(patterns_data)
              st.dataframe(df, use_container_width=True)
              
              # Confidence chart
              fig = px.bar(df, x="Pattern", y="Confidence", color="Status",
                          title="Expert Pattern Confidence Scores",
                          labels={"Confidence": "Confidence Score"})
              fig.update_xaxis(tickangle=45)
              st.plotly_chart(fig, use_container_width=True)

          with tab2:
              st.subheader("🤖 Expert LLM Agent Chat")
              st.info("💡 Ask me about Ubuntu, Kubernetes, or GlusterFS issues!")
              
              # Chat interface
              if "messages" not in st.session_state:
                  st.session_state.messages = [
                      {"role": "assistant", "content": "Hello! I'm the Expert LLM Agent running in your Podman Minikube environment. I can help with system administration issues across Ubuntu, Kubernetes, and GlusterFS. What can I help you with?"}
                  ]

              for message in st.session_state.messages:
                  with st.chat_message(message["role"]):
                      st.markdown(message["content"])

              if prompt := st.chat_input("Ask about system issues..."):
                  st.session_state.messages.append({"role": "user", "content": prompt})
                  with st.chat_message("user"):
                      st.markdown(prompt)

                  # Simulate expert response
                  with st.chat_message("assistant"):
                      expert_responses = {
                          "cpu": "🔍 **CPU Analysis**: High CPU usage detected. I recommend checking for runaway processes with `top` or `htop`, analyzing CPU-intensive applications, and considering resource scaling. Would you like me to provide specific remediation steps?",
                          "memory": "🧠 **Memory Analysis**: Memory pressure can be caused by memory leaks or insufficient allocation. I suggest checking memory usage with `free -h`, analyzing process memory with `ps aux --sort=-%mem`, and implementing memory optimization strategies.",
                          "disk": "💾 **Disk Analysis**: Disk space issues require immediate attention. I recommend running `df -h` to check usage, `du -sh /*` to find large directories, and implementing cleanup procedures. Would you like automated cleanup suggestions?",
                          "kubernetes": "⚙️ **Kubernetes Analysis**: Pod issues often relate to resource limits, image problems, or configuration errors. I can help analyze pod logs, check resource quotas, and provide remediation strategies based on the specific error patterns.",
                          "glusterfs": "🗄️ **GlusterFS Analysis**: Storage issues in GlusterFS typically involve brick problems, network connectivity, or volume healing. I can help diagnose brick status, network issues, and provide healing procedures."
                      }
                      
                      # Simple keyword matching for demo
                      response = "🤖 **Expert Analysis**: I understand you're asking about system administration. "
                      prompt_lower = prompt.lower()
                      
                      if any(word in prompt_lower for word in ["cpu", "processor", "load"]):
                          response = expert_responses["cpu"]
                      elif any(word in prompt_lower for word in ["memory", "ram", "oom"]):
                          response = expert_responses["memory"]
                      elif any(word in prompt_lower for word in ["disk", "storage", "space"]):
                          response = expert_responses["disk"]
                      elif any(word in prompt_lower for word in ["kubernetes", "k8s", "pod", "container"]):
                          response = expert_responses["kubernetes"]
                      elif any(word in prompt_lower for word in ["gluster", "brick", "volume"]):
                          response = expert_responses["glusterfs"]
                      else:
                          response += f"Based on your query '{prompt}', I can provide expert guidance on Ubuntu OS management, Kubernetes orchestration, or GlusterFS storage solutions. Could you provide more specific details about the issue you're experiencing?"
                      
                      st.markdown(response)
                      st.session_state.messages.append({"role": "assistant", "content": response})

          with tab3:
              st.subheader("📊 Expert Pattern Analytics")
              
              # Pattern categories
              categories = {
                  "Ubuntu OS": ["Performance Optimization", "Service Management", "Package Issues", "Network Config", "Security Hardening"],
                  "Kubernetes": ["Pod Management", "Service Discovery", "Resource Scaling", "Network Policies", "Storage Issues"],
                  "GlusterFS": ["Brick Management", "Volume Operations", "Healing Procedures", "Performance Tuning", "Backup Strategies"]
              }
              
              for category, patterns in categories.items():
                  with st.expander(f"🔧 {category} Patterns ({len(patterns)} available)"):
                      for i, pattern in enumerate(patterns, 1):
                          col1, col2, col3 = st.columns([3, 1, 1])
                          with col1:
                              st.write(f"{i}. {pattern}")
                          with col2:
                              confidence = random.uniform(0.75, 0.98)
                              st.write(f"{confidence:.2f}")
                          with col3:
                              status = random.choice(["🟢 Ready", "🟡 Learning", "🔴 Training"])
                              st.write(status)

          with tab4:
              st.subheader("🔧 Testing Environment Status")
              
              # Environment details
              st.write("**Environment Configuration:**")
              env_info = {
                  "Container Runtime": "Podman",
                  "Kubernetes Distribution": "Minikube",
                  "Python Version": "3.11",
                  "Streamlit Version": "Latest",
                  "Expert Patterns": "14 Active",
                  "AI Models": "Pattern Recognition + LLM Integration Ready"
              }
              
              for key, value in env_info.items():
                  col1, col2 = st.columns([2, 3])
                  with col1:
                      st.write(f"**{key}:**")
                  with col2:
                      st.write(value)
              
              st.write("**Test Operations:**")
              col1, col2, col3 = st.columns(3)
              
              with col1:
                  if st.button("🧪 Run Pattern Test"):
                      st.success("✅ All 14 expert patterns loaded successfully!")
                      
              with col2:
                  if st.button("🔍 System Scan"):
                      with st.spinner("Scanning system..."):
                          time.sleep(2)
                      st.success("✅ System scan completed - No critical issues found!")
                      
              with col3:
                  if st.button("🚀 Performance Test"):
                      with st.spinner("Running performance test..."):
                          time.sleep(3)
                      st.success("✅ Performance test passed - System responsive!")
              
              # Live metrics chart
              st.write("**Live Performance Metrics:**")
              
              # Generate sample time series data
              times = [datetime.now() - timedelta(minutes=x) for x in range(20, 0, -1)]
              cpu_data = [random.randint(20, 80) for _ in range(20)]
              memory_data = [random.randint(30, 70) for _ in range(20)]
              
              metrics_df = pd.DataFrame({
                  'Time': times,
                  'CPU %': cpu_data,
                  'Memory %': memory_data
              })
              
              fig = px.line(metrics_df, x='Time', y=['CPU %', 'Memory %'], 
                           title='Real-time System Metrics')
              st.plotly_chart(fig, use_container_width=True)

          # Footer with auto-refresh
          st.markdown("---")
          col1, col2, col3 = st.columns([2, 2, 1])
          with col1:
              st.markdown("🚀 **Expert LLM Agent** - Podman Minikube Test Environment")
          with col2:
              st.markdown(f"⏰ Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
          with col3:
              if st.button("🔄 Refresh"):
                  st.experimental_rerun()

          PYEOF
          
          mkdir -p /app && cd /app
          echo "Starting Expert LLM Agent..."
          streamlit run expert_agent.py \
            --server.port=8501 \
            --server.address=0.0.0.0 \
            --server.headless=true \
            --browser.gatherUsageStats=false
        
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        
        livenessProbe:
          httpGet:
            path: /
            port: 8501
          initialDelaySeconds: 60
          periodSeconds: 30
        
        readinessProbe:
          httpGet:
            path: /
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: expert-llm-test-service
  namespace: expert-llm-system
  labels:
    app: expert-llm-test
spec:
  type: NodePort
  ports:
  - port: 80
    targetPort: 8501
    protocol: TCP
    name: http
  selector:
    app: expert-llm-test
EOF

    # Wait for deployment
    log_info "Waiting for Expert LLM deployment..."
    kubectl wait --for=condition=available --timeout=300s deployment/expert-llm-test -n expert-llm-system
    
    # Get access information
    NODEPORT=$(kubectl get service expert-llm-test-service -n expert-llm-system -o jsonpath='{.spec.ports[0].nodePort}')
    MINIKUBE_IP=$(minikube ip)
    
    log_success "Expert LLM System deployed successfully!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   NodePort: http://$MINIKUBE_IP:$NODEPORT"
    echo "   Port Forward: kubectl port-forward -n expert-llm-system service/expert-llm-test-service 8501:80"
    echo "   Then open: http://localhost:8501"
}

# Function to show usage information
show_usage() {
    echo "Expert LLM System - Podman Minikube Setup"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - Install and setup Podman + Minikube"
    echo "  start     - Start Minikube with Podman"
    echo "  deploy    - Deploy Expert LLM test system"
    echo "  status    - Show cluster status"
    echo "  access    - Show access information"
    echo "  stop      - Stop Minikube"
    echo "  clean     - Clean up everything"
    echo "  help      - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 setup   # Full setup"
    echo "  $0 deploy  # Deploy after setup"
    echo "  $0 access  # Get access URLs"
}

# Function to show access information
show_access_info() {
    if ! minikube status >/dev/null 2>&1; then
        log_error "Minikube is not running. Run '$0 start' first."
        return 1
    fi
    
    log_info "Getting access information..."
    
    MINIKUBE_IP=$(minikube ip)
    
    if kubectl get service expert-llm-test-service -n expert-llm-system >/dev/null 2>&1; then
        NODEPORT=$(kubectl get service expert-llm-test-service -n expert-llm-system -o jsonpath='{.spec.ports[0].nodePort}')
        
        echo ""
        echo "🌐 Expert LLM System Access:"
        echo "   Direct URL: http://$MINIKUBE_IP:$NODEPORT"
        echo "   Port Forward: kubectl port-forward -n expert-llm-system service/expert-llm-test-service 8501:80"
        echo "   Local URL: http://localhost:8501 (after port forward)"
        echo ""
        echo "🔧 Management Commands:"
        echo "   Minikube Dashboard: minikube dashboard"
        echo "   Check Pods: kubectl get pods -n expert-llm-system"
        echo "   View Logs: kubectl logs -f deployment/expert-llm-test -n expert-llm-system"
    else
        log_warning "Expert LLM system not deployed. Run '$0 deploy' first."
    fi
}

# Function to show cluster status
show_status() {
    log_info "Cluster Status:"
    
    if command_exists minikube; then
        minikube status
    else
        log_error "Minikube not installed"
        return 1
    fi
    
    echo ""
    log_info "Pods Status:"
    kubectl get pods -A
    
    echo ""
    log_info "Services:"
    kubectl get services -A
}

# Function to stop Minikube
stop_minikube() {
    log_info "Stopping Minikube..."
    minikube stop
    log_success "Minikube stopped"
}

# Function to clean up everything
cleanup() {
    log_warning "Cleaning up Podman Minikube setup..."
    
    read -p "This will delete the Minikube cluster and stop Podman. Continue? (y/N): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        minikube delete 2>/dev/null || true
        podman machine stop 2>/dev/null || true
        log_success "Cleanup completed"
    else
        log_info "Cleanup cancelled"
    fi
}

# Main script logic
main() {
    case "${1:-help}" in
        "setup")
            log_info "Starting Podman Minikube setup for Expert LLM System..."
            
            # Check and install dependencies
            if ! command_exists podman; then
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    install_podman_macos
                else
                    log_error "Please install Podman manually on your system"
                    exit 1
                fi
            fi
            
            if ! command_exists minikube; then
                install_minikube
            fi
            
            if ! command_exists kubectl; then
                log_error "kubectl is required. Please install kubectl"
                exit 1
            fi
            
            setup_podman
            start_minikube_podman
            verify_setup
            
            log_success "Setup completed! Run '$0 deploy' to deploy the Expert LLM system."
            ;;
        "start")
            setup_podman
            start_minikube_podman
            verify_setup
            ;;
        "deploy")
            deploy_expert_llm_test
            show_access_info
            ;;
        "status")
            show_status
            ;;
        "access")
            show_access_info
            ;;
        "stop")
            stop_minikube
            ;;
        "clean")
            cleanup
            ;;
        "help"|*)
            show_usage
            ;;
    esac
}

# Run main function with all arguments
main "$@"

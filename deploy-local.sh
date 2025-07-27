#!/bin/bash

# Local Kubernetes Deployment Script for Expert LLM System
# Optimized for Kind/Minikube/Docker Desktop Kubernetes

set -euo pipefail

# Configuration
NAMESPACE="expert-llm-system"
IMAGE_NAME="expert-llm-system"
IMAGE_TAG="local"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$CURRENT_DIR")"

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

# Function to check if running in Kind
check_cluster_type() {
    local context=$(kubectl config current-context)
    if [[ "$context" == *"kind"* ]]; then
        log_info "Detected Kind cluster: $context"
        CLUSTER_TYPE="kind"
    elif [[ "$context" == *"minikube"* ]]; then
        log_info "Detected Minikube cluster: $context"
        CLUSTER_TYPE="minikube"
    elif [[ "$context" == *"docker-desktop"* ]]; then
        log_info "Detected Docker Desktop cluster: $context"
        CLUSTER_TYPE="docker-desktop"
    else
        log_info "Unknown cluster type: $context"
        CLUSTER_TYPE="unknown"
    fi
}

# Function to build Docker image
build_image() {
    log_info "Building Docker image for local deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Build the image
    docker build -t "$IMAGE_NAME:$IMAGE_TAG" .
    
    # Load image into Kind cluster if using Kind
    if [ "$CLUSTER_TYPE" = "kind" ]; then
        log_info "Loading image into Kind cluster..."
        kind load docker-image "$IMAGE_NAME:$IMAGE_TAG"
    elif [ "$CLUSTER_TYPE" = "minikube" ]; then
        log_info "Loading image into Minikube..."
        minikube image load "$IMAGE_NAME:$IMAGE_TAG"
    fi
    
    log_success "Docker image built and loaded"
}

# Function to create namespace
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    kubectl label namespace "$NAMESPACE" monitoring=enabled --overwrite
    
    log_success "Namespace ready"
}

# Function to deploy core system
deploy_core() {
    log_info "Deploying Expert LLM System..."
    
    # Update image reference for local deployment
    local temp_file=$(mktemp)
    sed "s|image: expert-llm-system:latest|image: $IMAGE_NAME:$IMAGE_TAG|g" \
        "$CURRENT_DIR/expert-llm-system.yaml" > "$temp_file"
    
    # Apply the deployment
    kubectl apply -f "$temp_file"
    rm "$temp_file"
    
    # Wait for deployment
    log_info "Waiting for Expert LLM System to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/expert-llm-system -n "$NAMESPACE"
    
    log_success "Expert LLM System deployed"
}

# Function to deploy Ollama
deploy_ollama() {
    log_info "Deploying Ollama LLM service..."
    
    kubectl apply -f "$CURRENT_DIR/ollama-deployment.yaml"
    
    # Wait for deployment
    log_info "Waiting for Ollama to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/ollama -n "$NAMESPACE"
    
    log_success "Ollama deployed"
}

# Function to pull LLM model
pull_model() {
    log_info "Pulling Llama 3.2 model..."
    
    # Wait a bit for Ollama to fully start
    sleep 30
    
    # Pull model using kubectl exec
    kubectl exec -n "$NAMESPACE" deployment/ollama -- ollama pull llama3.2 || {
        log_warning "Model pull failed, this might take time. Continuing..."
        # Start a background job to pull the model
        kubectl exec -n "$NAMESPACE" deployment/ollama -- sh -c "ollama pull llama3.2 &" || true
    }
    
    log_success "Model pull initiated"
}

# Function to deploy monitoring (optional)
deploy_monitoring() {
    log_info "Deploying monitoring stack..."
    
    kubectl apply -f "$CURRENT_DIR/monitoring.yaml"
    
    # Wait for monitoring components
    log_info "Waiting for monitoring components..."
    kubectl wait --for=condition=available --timeout=180s deployment/prometheus -n "$NAMESPACE" || log_warning "Prometheus deployment timeout"
    kubectl wait --for=condition=available --timeout=180s deployment/grafana -n "$NAMESPACE" || log_warning "Grafana deployment timeout"
    
    log_success "Monitoring stack deployed"
}

# Function to show access information
show_access_info() {
    log_info "Getting access information..."
    
    echo ""
    echo "=== 🌐 Access URLs ==="
    
    # Get NodePort for main service
    local nodeport=$(kubectl get service expert-llm-service -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "")
    
    if [ -n "$nodeport" ]; then
        case $CLUSTER_TYPE in
            "kind")
                echo "Expert LLM Dashboard: http://localhost:$nodeport"
                ;;
            "minikube")
                local minikube_ip=$(minikube ip 2>/dev/null || echo "localhost")
                echo "Expert LLM Dashboard: http://$minikube_ip:$nodeport"
                ;;
            "docker-desktop")
                echo "Expert LLM Dashboard: http://localhost:$nodeport"
                ;;
            *)
                echo "Expert LLM Dashboard: http://localhost:$nodeport (or use cluster IP)"
                ;;
        esac
    fi
    
    # Port forwarding option
    echo ""
    echo "=== 🔗 Port Forwarding Commands ==="
    echo "Expert LLM System:  kubectl port-forward -n $NAMESPACE service/expert-llm-service 8501:80"
    echo "Ollama API:        kubectl port-forward -n $NAMESPACE service/ollama-service 11434:11434"
    echo "Grafana:           kubectl port-forward -n $NAMESPACE service/grafana-service 3000:3000"
    echo "Prometheus:        kubectl port-forward -n $NAMESPACE service/prometheus-service 9090:9090"
    
    echo ""
    echo "=== 📊 Quick Access ==="
    echo "Main Dashboard:    http://localhost:8501 (after port-forward)"
    echo "Grafana Login:     admin / expert-llm-admin"
    
    echo ""
    echo "=== 🔍 Monitoring Commands ==="
    echo "Pod Status:        kubectl get pods -n $NAMESPACE"
    echo "Service Status:    kubectl get services -n $NAMESPACE"
    echo "View Logs:         kubectl logs -f deployment/expert-llm-system -n $NAMESPACE"
    echo "Health Check:      kubectl exec -n $NAMESPACE deployment/expert-llm-system -- ./health_check.sh"
}

# Function to start port forwarding
start_port_forwarding() {
    log_info "Starting port forwarding for easy access..."
    
    # Kill any existing port forwards
    pkill -f "kubectl port-forward" 2>/dev/null || true
    sleep 2
    
    # Start port forwards in background
    kubectl port-forward -n "$NAMESPACE" service/expert-llm-service 8501:80 > /dev/null 2>&1 &
    local pf1_pid=$!
    
    kubectl port-forward -n "$NAMESPACE" service/ollama-service 11434:11434 > /dev/null 2>&1 &
    local pf2_pid=$!
    
    # Check if monitoring is deployed
    if kubectl get service grafana-service -n "$NAMESPACE" &>/dev/null; then
        kubectl port-forward -n "$NAMESPACE" service/grafana-service 3000:3000 > /dev/null 2>&1 &
        local pf3_pid=$!
        
        kubectl port-forward -n "$NAMESPACE" service/prometheus-service 9090:9090 > /dev/null 2>&1 &
        local pf4_pid=$!
    fi
    
    sleep 3
    
    echo ""
    echo "=== 🚀 Port Forwarding Active ==="
    echo "Expert LLM Dashboard: http://localhost:8501"
    echo "Ollama API:          http://localhost:11434"
    if [ -n "${pf3_pid:-}" ]; then
        echo "Grafana:             http://localhost:3000"
        echo "Prometheus:          http://localhost:9090"
    fi
    
    echo ""
    log_success "Port forwarding started! Press Ctrl+C to stop all port forwards."
    
    # Wait for user interrupt
    trap 'kill $pf1_pid $pf2_pid ${pf3_pid:-} ${pf4_pid:-} 2>/dev/null || true; log_info "Port forwarding stopped"; exit 0' INT
    wait
}

# Function to show system status
show_status() {
    echo "=== 📊 Expert LLM System Status ==="
    echo ""
    
    echo "Namespace:"
    kubectl get namespace "$NAMESPACE" 2>/dev/null || echo "Namespace not found"
    
    echo ""
    echo "Pods:"
    kubectl get pods -n "$NAMESPACE" -o wide 2>/dev/null || echo "No pods found"
    
    echo ""
    echo "Services:"
    kubectl get services -n "$NAMESPACE" 2>/dev/null || echo "No services found"
    
    echo ""
    echo "Deployments:"
    kubectl get deployments -n "$NAMESPACE" 2>/dev/null || echo "No deployments found"
    
    echo ""
    echo "PVCs:"
    kubectl get pvc -n "$NAMESPACE" 2>/dev/null || echo "No PVCs found"
    
    # Health check if system is running
    if kubectl get deployment expert-llm-system -n "$NAMESPACE" &>/dev/null; then
        echo ""
        echo "Health Check:"
        kubectl exec -n "$NAMESPACE" deployment/expert-llm-system -- ./health_check.sh quick 2>/dev/null || echo "Health check failed or not available"
    fi
}

# Function to create live data simulation
create_live_data() {
    log_info "Setting up live data simulation..."
    
    # Create a job that generates live system data
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: live-data-generator
  namespace: $NAMESPACE
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: data-generator
        image: alpine:latest
        command:
        - /bin/sh
        - -c
        - |
          # Install required tools
          apk add --no-cache curl jq
          
          # Wait for Expert LLM System to be ready
          while ! curl -f http://expert-llm-service:80/_stcore/health 2>/dev/null; do
            echo "Waiting for Expert LLM System..."
            sleep 10
          done
          
          echo "Expert LLM System is ready! Generating live data..."
          
          # Generate sample system issues for the system to learn from
          for i in \$(seq 1 20); do
            # Simulate various system issues
            case \$((i % 4)) in
              0) issue="High CPU usage detected on node worker-1" ;;
              1) issue="Disk space running low on /var partition" ;;
              2) issue="GlusterFS brick offline on node storage-2" ;;
              3) issue="Kubernetes pod in CrashLoopBackOff state" ;;
            esac
            
            echo "Generated issue \$i: \$issue"
            sleep 5
          done
          
          echo "Live data generation completed!"
      backoffLimit: 3
EOF
    
    log_success "Live data simulation job created"
}

# Function to cleanup deployment
cleanup() {
    log_warning "Cleaning up Expert LLM System deployment..."
    
    read -p "Are you sure you want to delete the deployment? (y/N): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        # Stop port forwarding
        pkill -f "kubectl port-forward" 2>/dev/null || true
        
        # Delete namespace (this removes everything)
        kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
        
        log_success "Deployment cleaned up"
    else
        log_info "Cleanup cancelled"
    fi
}

# Function to show help
show_help() {
    cat << EOF
Expert LLM System - Local Kubernetes Deployment

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    deploy          Deploy complete system (default)
    deploy-core     Deploy only Expert LLM System
    deploy-ollama   Deploy only Ollama service  
    deploy-monitoring Deploy monitoring stack
    build           Build Docker image only
    status          Show deployment status
    access          Show access information
    port-forward    Start port forwarding for easy access
    live-data       Generate live data for testing
    cleanup         Remove deployment
    help            Show this help

Examples:
    # Full deployment with monitoring
    $0 deploy

    # Deploy with monitoring
    $0 deploy --monitoring

    # Just build the image
    $0 build

    # Start port forwarding for access
    $0 port-forward

    # Check system status
    $0 status

    # Generate live test data
    $0 live-data

EOF
}

# Parse command line arguments
MONITORING=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --monitoring)
            MONITORING=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

# Main command handling
COMMAND="${1:-deploy}"

# Check cluster connection first
if ! kubectl cluster-info &>/dev/null; then
    log_error "Cannot connect to Kubernetes cluster. Please ensure kubectl is configured."
    exit 1
fi

check_cluster_type

case $COMMAND in
    "deploy")
        build_image
        create_namespace
        deploy_core
        deploy_ollama
        if [ "$MONITORING" = "true" ]; then
            deploy_monitoring
        fi
        pull_model
        create_live_data
        show_access_info
        echo ""
        echo "🎉 Deployment completed! Run '$0 port-forward' for easy access."
        ;;
    "deploy-core")
        build_image
        create_namespace
        deploy_core
        ;;
    "deploy-ollama")
        create_namespace
        deploy_ollama
        pull_model
        ;;
    "deploy-monitoring")
        create_namespace
        deploy_monitoring
        ;;
    "build")
        build_image
        ;;
    "status")
        show_status
        ;;
    "access")
        show_access_info
        ;;
    "port-forward")
        start_port_forwarding
        ;;
    "live-data")
        create_live_data
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|*)
        show_help
        ;;
esac

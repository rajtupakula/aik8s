#!/bin/bash

# Kubernetes Deployment Script for Expert LLM System
# This script provides comprehensive deployment and management capabilities

set -euo pipefail

# Configuration
NAMESPACE="expert-llm-system"
DEPLOYMENT_NAME="expert-llm-system"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-expert-llm-system}"
MONITORING="${MONITORING:-false}"
GPU_SUPPORT="${GPU_SUPPORT:-false}"
STORAGE_CLASS="${STORAGE_CLASS:-standard}"

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

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_warning "Docker is not available - cannot build images locally"
    fi
    
    log_success "Prerequisites check completed"
}

# Function to create namespace
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace "$NAMESPACE"
        log_success "Namespace $NAMESPACE created"
    fi
    
    # Label namespace for monitoring
    kubectl label namespace "$NAMESPACE" monitoring=enabled --overwrite
}

# Function to build and push Docker image
build_and_push_image() {
    local should_build="${1:-false}"
    
    if [ "$should_build" = "true" ]; then
        log_info "Building Docker image..."
        
        cd "$(dirname "$0")/.."
        
        # Build image
        docker build -t "$REGISTRY:$IMAGE_TAG" .
        
        # Tag for latest
        docker tag "$REGISTRY:$IMAGE_TAG" "$REGISTRY:latest"
        
        # Push if registry is remote
        if [[ "$REGISTRY" == *"."* ]]; then
            log_info "Pushing image to registry..."
            docker push "$REGISTRY:$IMAGE_TAG"
            docker push "$REGISTRY:latest"
        fi
        
        log_success "Docker image built and pushed"
    fi
}

# Function to update deployment configurations
update_configs() {
    log_info "Updating deployment configurations..."
    
    # Update storage class in all PVC definitions
    if [ "$STORAGE_CLASS" != "standard" ]; then
        log_info "Updating storage class to: $STORAGE_CLASS"
        sed -i.bak "s/storageClassName: standard/storageClassName: $STORAGE_CLASS/g" k8s/*.yaml
        sed -i.bak "s/storageClassName: fast-ssd/storageClassName: $STORAGE_CLASS/g" k8s/*.yaml
    fi
    
    # Update image tag
    sed -i.bak "s|image: expert-llm-system:latest|image: $REGISTRY:$IMAGE_TAG|g" k8s/expert-llm-system.yaml
    
    # Configure GPU support
    if [ "$GPU_SUPPORT" = "true" ]; then
        log_info "Enabling GPU support..."
        # Add GPU resource requests/limits
        cat >> k8s/expert-llm-system.yaml << EOF

        # GPU Configuration
        - name: CUDA_VISIBLE_DEVICES
          value: "0"
        resources:
          limits:
            nvidia.com/gpu: 1
EOF
    fi
    
    log_success "Configurations updated"
}

# Function to deploy core system
deploy_core() {
    log_info "Deploying Expert LLM System..."
    
    # Apply core deployment
    kubectl apply -f k8s/expert-llm-system.yaml
    
    # Wait for deployment to be ready
    log_info "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=600s deployment/$DEPLOYMENT_NAME -n $NAMESPACE
    
    log_success "Expert LLM System deployed successfully"
}

# Function to deploy Ollama
deploy_ollama() {
    log_info "Deploying Ollama LLM service..."
    
    kubectl apply -f k8s/ollama-deployment.yaml
    
    # Wait for Ollama to be ready
    log_info "Waiting for Ollama to be ready..."
    kubectl wait --for=condition=available --timeout=600s deployment/ollama -n $NAMESPACE
    
    # Run model pull job
    log_info "Pulling LLM models..."
    kubectl wait --for=condition=complete --timeout=1200s job/ollama-model-pull -n $NAMESPACE
    
    log_success "Ollama LLM service deployed successfully"
}

# Function to deploy monitoring
deploy_monitoring() {
    if [ "$MONITORING" = "true" ]; then
        log_info "Deploying monitoring stack..."
        
        kubectl apply -f k8s/monitoring.yaml
        
        # Wait for monitoring components
        log_info "Waiting for monitoring components..."
        kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n $NAMESPACE
        kubectl wait --for=condition=available --timeout=300s deployment/grafana -n $NAMESPACE
        
        log_success "Monitoring stack deployed successfully"
    fi
}

# Function to setup ingress
setup_ingress() {
    local domain="${1:-expert-llm.local}"
    
    log_info "Setting up ingress for domain: $domain"
    
    # Update ingress with actual domain
    sed -i.bak "s/expert-llm.yourdomain.com/$domain/g" k8s/expert-llm-system.yaml
    
    # Apply ingress
    kubectl apply -f k8s/expert-llm-system.yaml
    
    log_success "Ingress configured for $domain"
}

# Function to check deployment status
check_status() {
    log_info "Checking deployment status..."
    
    echo ""
    echo "=== Namespace Status ==="
    kubectl get namespace $NAMESPACE
    
    echo ""
    echo "=== Pods Status ==="
    kubectl get pods -n $NAMESPACE
    
    echo ""
    echo "=== Services Status ==="
    kubectl get services -n $NAMESPACE
    
    echo ""
    echo "=== Ingress Status ==="
    kubectl get ingress -n $NAMESPACE
    
    echo ""
    echo "=== PVC Status ==="
    kubectl get pvc -n $NAMESPACE
    
    echo ""
    echo "=== Deployment Status ==="
    kubectl get deployments -n $NAMESPACE
    
    # Check health endpoints
    echo ""
    echo "=== Health Checks ==="
    
    # Port forward for health check
    kubectl port-forward -n $NAMESPACE service/expert-llm-service 8501:80 &
    PF_PID=$!
    sleep 5
    
    if curl -f http://localhost:8501/_stcore/health &> /dev/null; then
        log_success "Expert LLM System is healthy"
    else
        log_warning "Expert LLM System health check failed"
    fi
    
    kill $PF_PID 2>/dev/null || true
}

# Function to get access information
get_access_info() {
    log_info "Getting access information..."
    
    echo ""
    echo "=== Access Information ==="
    
    # Get LoadBalancer IP
    LB_IP=$(kubectl get service expert-llm-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$LB_IP" ]; then
        echo "LoadBalancer URL: http://$LB_IP"
    fi
    
    # Get NodePort
    NODE_PORT=$(kubectl get service expert-llm-service -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "")
    if [ -n "$NODE_PORT" ]; then
        NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}' || \
                  kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
        echo "NodePort URL: http://$NODE_IP:$NODE_PORT"
    fi
    
    # Get Ingress URL
    INGRESS_HOST=$(kubectl get ingress expert-llm-ingress -n $NAMESPACE -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "")
    if [ -n "$INGRESS_HOST" ]; then
        echo "Ingress URL: https://$INGRESS_HOST"
    fi
    
    # Port forwarding option
    echo "Port Forward: kubectl port-forward -n $NAMESPACE service/expert-llm-service 8501:80"
    
    if [ "$MONITORING" = "true" ]; then
        echo ""
        echo "=== Monitoring Access ==="
        echo "Grafana: kubectl port-forward -n $NAMESPACE service/grafana-service 3000:3000"
        echo "Prometheus: kubectl port-forward -n $NAMESPACE service/prometheus-service 9090:9090"
        echo "Grafana Login: admin / expert-llm-admin"
    fi
}

# Function to clean up deployment
cleanup() {
    log_warning "Cleaning up deployment..."
    
    read -p "Are you sure you want to delete the entire deployment? (y/N): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        kubectl delete namespace $NAMESPACE
        log_success "Deployment cleaned up"
    else
        log_info "Cleanup cancelled"
    fi
}

# Function to show logs
show_logs() {
    local component="${1:-expert-llm-system}"
    
    log_info "Showing logs for: $component"
    
    case $component in
        "expert-llm"|"app")
            kubectl logs -f deployment/expert-llm-system -n $NAMESPACE
            ;;
        "ollama")
            kubectl logs -f deployment/ollama -n $NAMESPACE
            ;;
        "prometheus")
            kubectl logs -f deployment/prometheus -n $NAMESPACE
            ;;
        "grafana")
            kubectl logs -f deployment/grafana -n $NAMESPACE
            ;;
        *)
            kubectl logs -f deployment/$component -n $NAMESPACE
            ;;
    esac
}

# Function to scale deployment
scale_deployment() {
    local replicas="${1:-2}"
    
    log_info "Scaling Expert LLM System to $replicas replicas..."
    
    kubectl scale deployment $DEPLOYMENT_NAME --replicas=$replicas -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/$DEPLOYMENT_NAME -n $NAMESPACE
    
    log_success "Deployment scaled to $replicas replicas"
}

# Function to update deployment
update_deployment() {
    local new_image="${1:-$REGISTRY:latest}"
    
    log_info "Updating deployment with image: $new_image"
    
    kubectl set image deployment/$DEPLOYMENT_NAME expert-llm-system=$new_image -n $NAMESPACE
    kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE
    
    log_success "Deployment updated successfully"
}

# Function to show help
show_help() {
    cat << EOF
Expert LLM System - Kubernetes Deployment Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    deploy          Deploy the complete system
    deploy-core     Deploy only the core Expert LLM System
    deploy-ollama   Deploy only the Ollama LLM service
    deploy-monitoring Deploy monitoring stack
    status          Check deployment status
    logs [component] Show logs for component (expert-llm|ollama|prometheus|grafana)
    scale [replicas] Scale the deployment
    update [image]  Update deployment with new image
    ingress [domain] Setup ingress with domain
    access          Show access information
    cleanup         Clean up the deployment
    help            Show this help message

Options:
    --namespace     Kubernetes namespace (default: expert-llm-system)
    --image-tag     Docker image tag (default: latest)
    --registry      Docker registry (default: expert-llm-system)
    --monitoring    Enable monitoring stack (default: false)
    --gpu           Enable GPU support (default: false)
    --storage-class Storage class for PVCs (default: standard)
    --build         Build and push Docker image before deploy

Environment Variables:
    NAMESPACE       Same as --namespace
    IMAGE_TAG       Same as --image-tag
    REGISTRY        Same as --registry
    MONITORING      Same as --monitoring
    GPU_SUPPORT     Same as --gpu
    STORAGE_CLASS   Same as --storage-class

Examples:
    # Deploy complete system with monitoring
    $0 deploy --monitoring --build

    # Deploy with custom storage class
    $0 deploy --storage-class fast-ssd

    # Scale to 5 replicas
    $0 scale 5

    # Update with new image
    $0 update myregistry/expert-llm:v2.0.0

    # Setup ingress
    $0 ingress expert-llm.mycompany.com

    # Check status
    $0 status

    # View logs
    $0 logs expert-llm

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --image-tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --monitoring)
            MONITORING="true"
            shift
            ;;
        --gpu)
            GPU_SUPPORT="true"
            shift
            ;;
        --storage-class)
            STORAGE_CLASS="$2"
            shift 2
            ;;
        --build)
            BUILD_IMAGE="true"
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

# Main command handling
COMMAND="${1:-help}"

case $COMMAND in
    "deploy")
        check_prerequisites
        create_namespace
        update_configs
        build_and_push_image "${BUILD_IMAGE:-false}"
        deploy_core
        deploy_ollama
        deploy_monitoring
        log_success "Deployment completed successfully!"
        get_access_info
        ;;
    "deploy-core")
        check_prerequisites
        create_namespace
        update_configs
        build_and_push_image "${BUILD_IMAGE:-false}"
        deploy_core
        ;;
    "deploy-ollama")
        check_prerequisites
        deploy_ollama
        ;;
    "deploy-monitoring")
        check_prerequisites
        MONITORING="true"
        deploy_monitoring
        ;;
    "status")
        check_status
        ;;
    "logs")
        show_logs "${2:-expert-llm-system}"
        ;;
    "scale")
        scale_deployment "${2:-2}"
        ;;
    "update")
        update_deployment "${2:-$REGISTRY:latest}"
        ;;
    "ingress")
        setup_ingress "${2:-expert-llm.local}"
        ;;
    "access")
        get_access_info
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|*)
        show_help
        ;;
esac

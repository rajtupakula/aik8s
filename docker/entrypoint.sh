#!/bin/bash

# Expert LLM System - Docker Entrypoint Script
# Handles initialization and service startup

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[DOCKER]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to wait for a service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local timeout=${4:-30}
    
    print_status "Waiting for $service_name to be ready at $host:$port..."
    
    for i in $(seq 1 $timeout); do
        if nc -z "$host" "$port" 2>/dev/null; then
            print_success "$service_name is ready!"
            return 0
        fi
        print_status "Waiting for $service_name... ($i/$timeout)"
        sleep 2
    done
    
    print_warning "$service_name is not ready after ${timeout} attempts"
    return 1
}

# Function to initialize application data
initialize_app() {
    print_status "Initializing Expert LLM System..."
    
    # Create necessary directories
    mkdir -p /app/data/backups
    mkdir -p /app/logs
    mkdir -p /app/temp
    
    # Initialize Ollama in background
    print_status "Setting up Ollama with expert knowledge..."
    if [ -f /app/setup-ollama.sh ]; then
        # Create log file with proper error handling
        touch /app/logs/ollama-setup.log 2>/dev/null || {
            print_warning "Cannot create log file in mounted volume, using temp location"
            mkdir -p /tmp/logs
            nohup bash /app/setup-ollama.sh > /tmp/logs/ollama-setup.log 2>&1 &
        } && {
            nohup bash /app/setup-ollama.sh > /app/logs/ollama-setup.log 2>&1 &
        }
        echo $! > /app/temp/ollama-setup.pid 2>/dev/null || echo $! > /tmp/ollama-setup.pid
        print_status "Ollama setup initiated in background"
    else
        print_warning "Ollama setup script not found"
    fi
    
    # Initialize historical issues file if it doesn't exist
    if [ ! -f /app/data/historical_issues.json ]; then
        print_status "Creating initial historical issues file..."
        cat > /app/data/historical_issues.json << 'EOF'
{
  "issue_history": {},
  "learning_analytics": {
    "total_issues_tracked": 0,
    "overall_success_rate": 0.0,
    "avg_resolution_time": 0,
    "most_common_categories": [],
    "trend_analysis": {
      "improving_areas": [],
      "stable_areas": [],
      "concerning_areas": []
    }
  },
  "system_baselines": {
    "ubuntu_os": {
      "disk_usage_normal": 75,
      "memory_usage_normal": 60,
      "cpu_usage_normal": 40
    },
    "kubernetes": {
      "pod_restart_rate_normal": 0.1,
      "node_ready_percentage": 100
    },
    "glusterfs": {
      "heal_queue_normal": 0,
      "peer_connectivity": 100
    }
  }
}
EOF
    fi
    
    # Set proper permissions (ignore errors for mounted volumes)
    chmod 644 /app/data/historical_issues.json 2>/dev/null || print_warning "Cannot set permissions on historical_issues.json (mounted volume)"
    chmod 755 /app/data/backups 2>/dev/null || print_warning "Cannot set permissions on backups directory (mounted volume)"
    chmod 755 /app/logs 2>/dev/null || print_warning "Cannot set permissions on logs directory (mounted volume)"
    chmod 755 /app/temp 2>/dev/null || print_warning "Cannot set permissions on temp directory"
    
    print_success "Application initialization complete"
}

# Function to check Ollama availability
check_ollama() {
    # Skip Ollama check if explicitly disabled
    if [ "$OLLAMA_ENABLED" = "false" ]; then
        print_warning "Ollama is disabled. LLM features will not be available."
        return 0
    fi
    
    if [ -n "$OLLAMA_HOST" ]; then
        local ollama_host=$(echo $OLLAMA_HOST | cut -d: -f1)
        local ollama_port=$(echo $OLLAMA_HOST | cut -d: -f2)
        
        if wait_for_service "$ollama_host" "$ollama_port" "Ollama" 60; then
            print_status "Checking if Llama model is available..."
            if curl -sf "http://$OLLAMA_HOST/api/tags" | grep -q "llama3.2"; then
                print_success "Llama 3.2 model is available"
            else
                print_warning "Llama 3.2 model not found. Pulling model..."
                curl -X POST "http://$OLLAMA_HOST/api/pull" \
                     -H "Content-Type: application/json" \
                     -d '{"name": "llama3.2"}' || print_warning "Failed to pull model"
            fi
        else
            print_warning "Ollama service not available. LLM features may not work."
        fi
    else
        print_warning "OLLAMA_HOST not set. LLM features will be disabled."
    fi
}

# Function to run health check
run_health_check() {
    print_status "Running application health check..."
    
    # Check Python imports
    python3 -c "
import sys
import os
sys.path.append('/app/src')

try:
    from agent.enhanced_rag_agent import EnhancedRAGAgent
    from agent.expert_remediation_engine import ExpertRemediationEngine
    from agent.issue_history_manager import IssueHistoryManager
    print('✅ Core modules imported successfully')
except ImportError as e:
    print(f'❌ Module import failed: {e}')
    sys.exit(1)

try:
    import streamlit
    import yaml
    import pandas
    import plotly
    print('✅ UI dependencies available')
except ImportError as e:
    print(f'⚠️  UI dependency missing: {e}')

print('✅ Health check passed')
"
    
    if [ $? -eq 0 ]; then
        print_success "Health check passed"
    else
        print_error "Health check failed"
        exit 1
    fi
}

# Main execution
main() {
    print_status "Starting Expert LLM System Docker container..."
    
    # Initialize application
    initialize_app
    
    # Check external services
    check_ollama
    
    # Run health check
    run_health_check
    
    # Handle different startup modes
    case "${1:-streamlit}" in
        "streamlit")
            print_status "Starting Streamlit dashboard..."
            cd /app/src
            exec streamlit run ui/dashboard.py \
                --server.port=8501 \
                --server.address=0.0.0.0 \
                --server.headless=true \
                --browser.gatherUsageStats=false \
                --server.enableCORS=false \
                --server.enableXsrfProtection=true
            ;;
        "supervisor")
            print_status "Starting with supervisor..."
            exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
            ;;
        "bash")
            print_status "Starting bash shell..."
            exec /bin/bash
            ;;
        "health")
            print_status "Running health check only..."
            run_health_check
            exit 0
            ;;
        *)
            print_status "Starting custom command: $*"
            exec "$@"
            ;;
    esac
}

# Trap signals for graceful shutdown
trap 'print_status "Received shutdown signal, stopping..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@"

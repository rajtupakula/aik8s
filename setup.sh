#!/bin/bash

# Expert LLM System - Setup and Deployment Script
# This script sets up the complete expert system with all dependencies

set -e  # Exit on any error

echo "🔧 Expert LLM System - Setup and Deployment"
echo "============================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found. Please run this script from the expert-llm-agent directory."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    print_warning "Ollama is not installed. Please install Ollama to use LLM features:"
    echo "  macOS: brew install ollama"
    echo "  Linux: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  Or visit: https://ollama.ai"
else
    print_success "Ollama is installed"
    
    # Pull required model
    print_status "Pulling Llama 3.2 model..."
    ollama pull llama3.2 || print_warning "Failed to pull llama3.2 model. You may need to do this manually."
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p data/backups
mkdir -p temp

# Set permissions
print_status "Setting appropriate permissions..."
chmod +x setup.sh
chmod +x run.sh 2>/dev/null || true

# Create run script
print_status "Creating run script..."
cat > run.sh << 'EOF'
#!/bin/bash

# Expert LLM System - Run Script

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if all required dependencies are installed
python -c "import streamlit, yaml, ollama, psutil, kubernetes" 2>/dev/null || {
    echo "Dependencies missing. Please run setup.sh first."
    exit 1
}

print_status "Starting Expert LLM System Dashboard..."
print_success "Dashboard will be available at: http://localhost:8501"
print_status "Use Ctrl+C to stop the system"

# Run the dashboard
cd src && streamlit run ui/dashboard.py --server.port=8501 --server.address=0.0.0.0
EOF

chmod +x run.sh

# Create development script
print_status "Creating development script..."
cat > dev.sh << 'EOF'
#!/bin/bash

# Expert LLM System - Development Mode

set -e

# Activate virtual environment
source venv/bin/activate

# Run in development mode with hot reload
cd src && streamlit run ui/dashboard.py --server.port=8501 --server.address=localhost --server.runOnSave=true
EOF

chmod +x dev.sh

# Create Kubernetes deployment configuration
print_status "Creating Kubernetes deployment configuration..."
mkdir -p k8s

cat > k8s/expert-llm-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: expert-llm-system
  labels:
    app: expert-llm-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: expert-llm-system
  template:
    metadata:
      labels:
        app: expert-llm-system
    spec:
      containers:
      - name: expert-llm-system
        image: expert-llm-system:latest
        ports:
        - containerPort: 8501
        env:
        - name: STREAMLIT_SERVER_PORT
          value: "8501"
        - name: STREAMLIT_SERVER_ADDRESS
          value: "0.0.0.0"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        - name: logs-volume
          mountPath: /app/logs
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: expert-llm-data-pvc
      - name: logs-volume
        persistentVolumeClaim:
          claimName: expert-llm-logs-pvc
      serviceAccountName: expert-llm-service-account
---
apiVersion: v1
kind: Service
metadata:
  name: expert-llm-service
spec:
  selector:
    app: expert-llm-system
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8501
  type: LoadBalancer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: expert-llm-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: expert-llm-logs-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 2Gi
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: expert-llm-service-account
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: expert-llm-cluster-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "nodes", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["storage.k8s.io"]
  resources: ["storageclasses", "persistentvolumes", "persistentvolumeclaims"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: expert-llm-cluster-role-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: expert-llm-cluster-role
subjects:
- kind: ServiceAccount
  name: expert-llm-service-account
  namespace: default
EOF

# Create Dockerfile
print_status "Creating Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    vim \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY data/ ./data/

# Create necessary directories
RUN mkdir -p logs temp data/backups

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "src/ui/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
EOF

# Create Docker Compose file
print_status "Creating Docker Compose configuration..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  expert-llm-system:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  # Optional: Add Ollama service if needed
  # ollama:
  #   image: ollama/ollama:latest
  #   ports:
  #     - "11434:11434"
  #   volumes:
  #     - ollama_data:/root/.ollama
  #   restart: unless-stopped

# volumes:
#   ollama_data:
EOF

# Create system health check script
print_status "Creating system health check script..."
cat > health_check.sh << 'EOF'
#!/bin/bash

# Expert LLM System - Health Check Script

echo "🔍 Expert LLM System Health Check"
echo "================================="

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment: OK"
else
    echo "❌ Virtual environment: MISSING"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check Python dependencies
echo "📦 Checking Python dependencies..."
python -c "
import sys
packages = ['streamlit', 'yaml', 'ollama', 'psutil', 'kubernetes', 'plotly', 'pandas']
missing = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg}: OK')
    except ImportError:
        print(f'❌ {pkg}: MISSING')
        missing.append(pkg)

if missing:
    print(f'Missing packages: {missing}')
    sys.exit(1)
"

# Check Ollama
if command -v ollama &> /dev/null; then
    echo "✅ Ollama: INSTALLED"
    if ollama list | grep -q "llama3.2"; then
        echo "✅ Llama 3.2 model: AVAILABLE"
    else
        echo "⚠️  Llama 3.2 model: NOT DOWNLOADED"
    fi
else
    echo "⚠️  Ollama: NOT INSTALLED"
fi

# Check data files
if [ -f "src/data/expert_patterns.yaml" ]; then
    echo "✅ Expert patterns: OK"
else
    echo "❌ Expert patterns: MISSING"
fi

if [ -f "src/data/historical_issues.json" ]; then
    echo "✅ Historical issues: OK"
else
    echo "⚠️  Historical issues: WILL BE CREATED"
fi

echo "✅ Health check completed!"
EOF

chmod +x health_check.sh

# Run initial health check
print_status "Running initial health check..."
./health_check.sh

# Create README for deployment
print_status "Creating deployment README..."
cat > DEPLOYMENT.md << 'EOF'
# Expert LLM System - Deployment Guide

## Quick Start

1. **Setup the system:**
   ```bash
   ./setup.sh
   ```

2. **Run the system:**
   ```bash
   ./run.sh
   ```

3. **Access the dashboard:**
   Open http://localhost:8501 in your browser

## Deployment Options

### Local Development
```bash
./dev.sh  # Runs with hot reload
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t expert-llm-system .
docker run -p 8501:8501 expert-llm-system
```

### Kubernetes Deployment
```bash
# Apply Kubernetes configuration
kubectl apply -f k8s/expert-llm-deployment.yaml

# Check deployment status
kubectl get pods -l app=expert-llm-system

# Access the service
kubectl port-forward service/expert-llm-service 8501:80
```

## System Requirements

- Python 3.11+
- 4GB RAM minimum (8GB recommended)
- 10GB disk space
- Ollama (for LLM features)
- Kubernetes cluster (for K8s monitoring)

## Features

- 🔧 **14 Expert Patterns** across Ubuntu OS, Kubernetes, and GlusterFS
- 💬 **Interactive Chat Assistant** with natural language processing
- 📊 **Real-time Monitoring** and system health tracking
- 🤖 **Historical Learning** with predictive analytics
- 🛡️ **Safety-first** command execution with validation
- 📈 **Forecasting** and trend analysis
- 🎯 **Manual Remediation** tools with guided procedures

## Troubleshooting

1. **Dependencies missing:**
   ```bash
   ./setup.sh  # Re-run setup
   ```

2. **Ollama issues:**
   ```bash
   ollama pull llama3.2  # Pull the model
   ```

3. **Permission errors:**
   ```bash
   chmod +x *.sh  # Fix script permissions
   ```

4. **Health check:**
   ```bash
   ./health_check.sh  # Check system status
   ```

## Configuration

- Expert patterns: `src/data/expert_patterns.yaml`
- Historical data: `src/data/historical_issues.json`
- Logs: `logs/` directory
- Configuration: Modify environment variables in deployment files

EOF

print_success "Setup completed successfully!"
echo ""
echo "🚀 Next Steps:"
echo "1. Run './health_check.sh' to verify installation"
echo "2. Run './run.sh' to start the Expert LLM System"
echo "3. Access the dashboard at http://localhost:8501"
echo "4. See DEPLOYMENT.md for advanced deployment options"
echo ""
print_warning "Note: Install Ollama and pull llama3.2 model for full LLM functionality"

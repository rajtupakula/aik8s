# Expert LLM System - Kubernetes Deployment

## 🚀 Production-Ready Kubernetes Deployment

This directory contains comprehensive Kubernetes manifests and deployment scripts for the Expert LLM System, designed for production environments with high availability, monitoring, and scalability.

## 📁 File Structure

```
k8s/
├── expert-llm-system.yaml     # Main application deployment
├── ollama-deployment.yaml     # LLM service deployment
├── monitoring.yaml            # Prometheus & Grafana monitoring
├── deploy.sh                  # Automated deployment script
└── README.md                  # This file
```

## 🔧 Prerequisites

### Cluster Requirements
- **Kubernetes Version**: 1.21+
- **Cluster Resources**: 8+ CPU cores, 16GB+ RAM
- **Storage**: Dynamic provisioning with at least 100GB available
- **Networking**: LoadBalancer or Ingress controller

### Required Tools
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Install Helm (optional, for advanced deployments)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Cluster Setup Verification
```bash
# Check cluster connection
kubectl cluster-info

# Verify node resources
kubectl top nodes

# Check storage classes
kubectl get storageclass
```

## 🚀 Quick Deployment

### 1. Simple Deployment
```bash
# Deploy everything with monitoring
cd k8s/
./deploy.sh deploy --monitoring --build

# Access dashboard
kubectl port-forward -n expert-llm-system service/expert-llm-service 8501:80
```

### 2. Production Deployment
```bash
# Production deployment with custom domain
./deploy.sh deploy \
  --monitoring \
  --storage-class fast-ssd \
  --registry your-registry.com/expert-llm-system \
  --image-tag v1.0.0

# Setup ingress with your domain
./deploy.sh ingress expert-llm.yourcompany.com
```

### 3. GPU-Enabled Deployment
```bash
# Deploy with GPU support for Ollama
./deploy.sh deploy \
  --gpu \
  --monitoring \
  --storage-class fast-ssd
```

## 📋 Deployment Options

### Environment Variables
```bash
export NAMESPACE="expert-llm-system"
export IMAGE_TAG="v1.0.0"
export REGISTRY="your-registry.com/expert-llm"
export MONITORING="true"
export GPU_SUPPORT="true"
export STORAGE_CLASS="fast-ssd"
```

### Storage Classes
| Storage Class | Use Case | Performance |
|---------------|----------|-------------|
| `standard` | General use | Standard |
| `fast-ssd` | High performance | High IOPS |
| `gp2` | AWS General Purpose | Balanced |
| `pd-ssd` | GCP Persistent Disk | High performance |

## 🏗️ Architecture Overview

### Components

1. **Expert LLM System** (2+ replicas)
   - Main application with Streamlit UI
   - Auto-scaling based on CPU/Memory
   - Health checks and rolling updates

2. **Ollama LLM Service** (1 replica)
   - Local LLM inference service
   - Model storage on persistent volumes
   - GPU support for acceleration

3. **Monitoring Stack** (optional)
   - Prometheus for metrics collection
   - Grafana for visualization
   - Custom alerts and dashboards

### Network Architecture
```
Internet → LoadBalancer → Ingress → Expert LLM Service → Pods
                                  → Ollama Service → Ollama Pod
                                  → Monitoring Services
```

## 🔒 Security Configuration

### RBAC (Role-Based Access Control)
```yaml
# Minimal permissions for service account
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
```

### Pod Security
- Non-root user execution
- Read-only root filesystem (where possible)
- Dropped capabilities
- Security contexts enforced

### Network Policies
```bash
# Apply network policies for isolation
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: expert-llm-network-policy
  namespace: expert-llm-system
spec:
  podSelector:
    matchLabels:
      app: expert-llm-system
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: expert-llm-system
  egress:
  - to: []
EOF
```

## 📊 Monitoring and Observability

### Metrics Available
- **Application Metrics**: Request rates, response times, error rates
- **System Metrics**: CPU, memory, disk usage
- **Custom Metrics**: Expert pattern matches, confidence scores
- **Ollama Metrics**: Model inference times, GPU utilization

### Grafana Dashboards
```bash
# Access Grafana
kubectl port-forward -n expert-llm-system service/grafana-service 3000:3000

# Login: admin / expert-llm-admin
# Import dashboard: expert-llm-dashboard.json
```

### Prometheus Alerts
- Expert LLM System down
- High memory/CPU usage
- Ollama service unavailable
- Persistent volume space issues

## 🔧 Operations Guide

### Scaling Operations
```bash
# Scale expert system
./deploy.sh scale 5

# Manual scaling
kubectl scale deployment expert-llm-system --replicas=5 -n expert-llm-system

# Auto-scaling configuration
kubectl get hpa -n expert-llm-system
```

### Updates and Rollbacks
```bash
# Rolling update
./deploy.sh update your-registry.com/expert-llm:v2.0.0

# Check rollout status
kubectl rollout status deployment/expert-llm-system -n expert-llm-system

# Rollback if needed
kubectl rollout undo deployment/expert-llm-system -n expert-llm-system
```

### Backup and Restore
```bash
# Backup persistent data
kubectl exec -n expert-llm-system deployment/expert-llm-system -- \
  tar -czf /app/backup-$(date +%Y%m%d).tar.gz /app/data

# Copy backup to local
kubectl cp expert-llm-system/pod-name:/app/backup-$(date +%Y%m%d).tar.gz ./backup.tar.gz
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Pods Stuck in Pending
```bash
# Check events
kubectl describe pod -n expert-llm-system

# Common causes:
# - Insufficient resources
# - Storage class issues
# - Node selector problems
```

#### 2. Expert LLM Service Unhealthy
```bash
# Check logs
./deploy.sh logs expert-llm

# Check health endpoint
kubectl exec -n expert-llm-system deployment/expert-llm-system -- \
  curl -f http://localhost:8501/_stcore/health
```

#### 3. Ollama Connection Issues
```bash
# Check Ollama service
kubectl get svc ollama-service -n expert-llm-system

# Test connectivity
kubectl exec -n expert-llm-system deployment/expert-llm-system -- \
  curl http://ollama-service:11434/api/tags
```

#### 4. Storage Issues
```bash
# Check PVC status
kubectl get pvc -n expert-llm-system

# Check storage class
kubectl describe storageclass

# Check node disk space
kubectl top nodes
```

### Debug Commands
```bash
# Pod shell access
kubectl exec -it deployment/expert-llm-system -n expert-llm-system -- bash

# View all events
kubectl get events -n expert-llm-system --sort-by='.lastTimestamp'

# Resource usage
kubectl top pods -n expert-llm-system

# Network debugging
kubectl exec -it deployment/expert-llm-system -n expert-llm-system -- \
  nslookup ollama-service
```

## 🌐 Multi-Environment Setup

### Development Environment
```bash
# Minimal deployment for dev
kubectl apply -f expert-llm-system.yaml
```

### Staging Environment
```bash
# Staging with monitoring
./deploy.sh deploy --monitoring --namespace expert-llm-staging
```

### Production Environment
```bash
# Full production setup
./deploy.sh deploy \
  --monitoring \
  --storage-class fast-ssd \
  --namespace expert-llm-prod \
  --registry prod-registry.company.com/expert-llm \
  --image-tag v1.0.0
```

## 🔄 CI/CD Integration

### GitLab CI Example
```yaml
# .gitlab-ci.yml
deploy_k8s:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - cd k8s/
    - ./deploy.sh deploy --registry $CI_REGISTRY_IMAGE --image-tag $CI_COMMIT_TAG
  rules:
    - if: $CI_COMMIT_TAG
```

### GitHub Actions Example
```yaml
# .github/workflows/k8s-deploy.yml
- name: Deploy to Kubernetes
  run: |
    cd k8s/
    ./deploy.sh deploy \
      --registry ghcr.io/${{ github.repository }} \
      --image-tag ${{ github.ref_name }}
```

## 📈 Performance Optimization

### Resource Allocation
```yaml
# Production resource requests/limits
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

### Storage Optimization
- Use SSD storage classes for better performance
- Consider using local storage for temporary data
- Implement proper data retention policies

### Network Optimization
- Use cluster-local DNS for service discovery
- Implement connection pooling
- Consider service mesh for advanced traffic management

## 🆘 Support and Maintenance

### Health Monitoring
```bash
# Automated health checks
kubectl get pods -n expert-llm-system -o wide

# Custom health script
curl -f http://expert-llm.yourcompany.com/_stcore/health
```

### Log Aggregation
```bash
# Centralized logging with fluentd/fluent-bit
kubectl logs -f deployment/expert-llm-system -n expert-llm-system | \
  grep -E "(ERROR|WARN|CRITICAL)"
```

### Maintenance Windows
```bash
# Drain node for maintenance
kubectl drain node-name --ignore-daemonsets --delete-emptydir-data

# Cordon node to prevent scheduling
kubectl cordon node-name
```

---

## 📞 Getting Help

### Quick Status Check
```bash
./deploy.sh status
```

### Access Information
```bash
./deploy.sh access
```

### Cleanup
```bash
./deploy.sh cleanup
```

For advanced configuration and troubleshooting, refer to the [main documentation](../README.md) or check the [Docker deployment guide](../DOCKER.md).

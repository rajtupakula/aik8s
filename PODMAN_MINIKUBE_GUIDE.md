# Podman Minikube Setup for Expert LLM System

This guide helps you set up a Podman-based Minikube environment to test the Expert LLM Agent system locally.

## 🚀 Quick Start

```bash
# Run the setup script
./setup-podman-minikube.sh setup

# Deploy the Expert LLM system
./setup-podman-minikube.sh deploy

# Get access information
./setup-podman-minikube.sh access
```

## 📋 Prerequisites

### macOS
- **Homebrew** (for installing Podman)
- **kubectl** (Kubernetes CLI)

### Linux
- **Podman** (will be installed if not present)
- **kubectl** (Kubernetes CLI)

## 🔧 Installation Steps

### 1. Full Setup (Recommended)
```bash
./setup-podman-minikube.sh setup
```

This command will:
- ✅ Install Podman (macOS via Homebrew)
- ✅ Install Minikube
- ✅ Initialize and start Podman machine
- ✅ Start Minikube with Podman driver
- ✅ Enable required addons (ingress, dashboard, metrics-server)
- ✅ Verify the setup

### 2. Deploy Expert LLM System
```bash
./setup-podman-minikube.sh deploy
```

This will deploy a comprehensive test version of the Expert LLM system with:
- 🤖 **Interactive AI Agent Chat**
- 📊 **Real-time System Monitoring**
- 🔍 **14 Expert Pattern Recognition**
- 🧪 **Testing Dashboard**
- 📈 **Live Performance Metrics**

## 🌐 Accessing the System

After deployment, you'll have multiple access options:

### Option 1: Direct NodePort Access
```bash
# Get the access URL
./setup-podman-minikube.sh access

# Output will show:
# Direct URL: http://192.168.49.2:30001
```

### Option 2: Port Forward (Recommended)
```bash
# Set up port forwarding
kubectl port-forward -n expert-llm-system service/expert-llm-test-service 8501:80

# Access at: http://localhost:8501
```

### Option 3: Minikube Service
```bash
# Open in default browser
minikube service expert-llm-test-service -n expert-llm-system
```

## 🎯 Features Available in Test Environment

### 1. 🏠 Dashboard Tab
- **Expert Pattern Recognition**: View active patterns and their confidence scores
- **Real-time Status**: Monitor system patterns (Ubuntu, Kubernetes, GlusterFS)
- **Interactive Charts**: Visualize pattern confidence and system metrics

### 2. 🤖 AI Agent Tab
- **Chat Interface**: Ask questions about system administration
- **Expert Responses**: Get intelligent answers about:
  - Ubuntu OS management
  - Kubernetes orchestration
  - GlusterFS storage solutions
- **Context-Aware**: Provides relevant troubleshooting steps

### 3. 📊 Patterns Tab
- **14 Expert Patterns** across three categories:
  - **Ubuntu OS**: Performance, Services, Packages, Network, Security
  - **Kubernetes**: Pods, Services, Scaling, Policies, Storage
  - **GlusterFS**: Bricks, Volumes, Healing, Performance, Backup

### 4. 🔧 Testing Tab
- **Environment Status**: View configuration details
- **Test Operations**: Run pattern tests, system scans, performance tests
- **Live Metrics**: Real-time CPU and memory monitoring charts

## 📝 Available Commands

| Command | Description |
|---------|-------------|
| `setup` | Install and setup Podman + Minikube |
| `start` | Start Minikube with Podman |
| `deploy` | Deploy Expert LLM test system |
| `status` | Show cluster status |
| `access` | Show access information |
| `stop` | Stop Minikube |
| `clean` | Clean up everything |
| `help` | Show help information |

## 🔍 Monitoring & Management

### Check System Status
```bash
# Cluster status
./setup-podman-minikube.sh status

# Pod status
kubectl get pods -n expert-llm-system

# Service status
kubectl get services -n expert-llm-system
```

### View Logs
```bash
# Application logs
kubectl logs -f deployment/expert-llm-test -n expert-llm-system

# All pods in namespace
kubectl logs -f -l app=expert-llm-test -n expert-llm-system
```

### Minikube Dashboard
```bash
# Open Kubernetes dashboard
minikube dashboard
```

## 🛠️ Troubleshooting

### Podman Issues
```bash
# Check Podman machine status
podman machine list

# Restart Podman machine
podman machine stop
podman machine start
```

### Minikube Issues
```bash
# Check Minikube status
minikube status

# Restart Minikube
minikube stop
minikube start --driver=podman
```

### Pod Not Starting
```bash
# Check pod events
kubectl describe pod -n expert-llm-system -l app=expert-llm-test

# Check resource usage
kubectl top pods -n expert-llm-system
```

### Connection Issues
```bash
# Test connectivity
kubectl port-forward -n expert-llm-system service/expert-llm-test-service 8501:80

# Check service endpoints
kubectl get endpoints -n expert-llm-system
```

## 🧹 Cleanup

### Stop Everything
```bash
./setup-podman-minikube.sh stop
```

### Complete Cleanup
```bash
./setup-podman-minikube.sh clean
```

This will:
- Delete the Minikube cluster
- Stop the Podman machine
- Remove all created resources

## 🔧 Configuration Details

### Minikube Configuration
- **Driver**: Podman
- **Container Runtime**: containerd
- **CPUs**: 4
- **Memory**: 6144 MB
- **Disk**: 30 GB
- **Kubernetes Version**: v1.28.0

### Enabled Addons
- **ingress**: For HTTP/HTTPS routing
- **dashboard**: Kubernetes web UI
- **metrics-server**: Resource usage metrics

### Pod Resources
- **Requests**: 1GB memory, 500m CPU
- **Limits**: 2GB memory, 1000m CPU

## 🎯 Testing Scenarios

### 1. Pattern Recognition Test
- Navigate to Dashboard tab
- Observe expert pattern detections
- Check confidence scores and statuses

### 2. AI Agent Interaction
- Go to AI Agent tab
- Ask questions about system issues:
  - "How do I fix high CPU usage?"
  - "Kubernetes pod is crash-looping"
  - "GlusterFS brick is offline"

### 3. Live Monitoring
- Visit Testing tab
- Run system scans and performance tests
- Monitor real-time metrics charts

### 4. System Administration
- Use kubectl commands to manage the cluster
- Scale deployments up and down
- Monitor resource usage

## 🚀 Next Steps

After testing with Podman Minikube:

1. **Production Deployment**: Use the full `expert-llm-system.yaml` for production
2. **Model Integration**: Connect to actual LLM models (Ollama, OpenAI, etc.)
3. **Real Data Sources**: Integrate with actual system monitoring tools
4. **Custom Patterns**: Add organization-specific expert patterns
5. **Advanced Features**: Enable authentication, logging, alerting

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section
2. Review logs with `kubectl logs`
3. Use `./setup-podman-minikube.sh status` for diagnostics
4. Run `./setup-podman-minikube.sh clean` and retry setup if needed

---

**Happy Testing! 🎉**

Your Expert LLM Agent is now running in a lightweight, isolated Podman Minikube environment, ready for comprehensive testing and development.

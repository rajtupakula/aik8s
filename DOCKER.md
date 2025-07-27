# Expert LLM System - Docker Deployment Guide

## 🐳 Docker Deployment Options

This guide provides comprehensive instructions for deploying the Expert LLM System using Docker containers.

## 📋 Prerequisites

- Docker Engine 20.10+ 
- Docker Compose 2.0+
- 4GB+ RAM available
- 10GB+ disk space

## 🚀 Quick Start

### 1. Simple Docker Run
```bash
# Build the image
./build-docker.sh

# Run the container
docker run -d \
  --name expert-llm-system \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  expert-llm-system:latest

# Access dashboard
open http://localhost:8501
```

### 2. Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f expert-llm-system

# Stop services
docker-compose down
```

### 3. With Ollama LLM Support
```bash
# Start with Ollama service
docker-compose up -d expert-llm-system ollama

# Pull Llama model
docker-compose exec ollama ollama pull llama3.2
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAMLIT_SERVER_PORT` | `8501` | Dashboard port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `SAFETY_MODE` | `enabled` | Safety validation |
| `OLLAMA_HOST` | `ollama:11434` | Ollama service URL |
| `OLLAMA_MODEL` | `llama3.2` | LLM model name |

### Volume Mounts

| Container Path | Purpose | Recommended Host Path |
|----------------|---------|----------------------|
| `/app/data` | Persistent data storage | `./data` |
| `/app/logs` | Application logs | `./logs` |
| `/app/temp` | Temporary files | Docker volume |

## 🏗️ Build Options

### Production Build
```bash
./build-docker.sh --build-type production --tag v1.0.0
```

### Development Build
```bash
./build-docker.sh --build-type development --tag dev
```

### Multi-architecture Build
```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag expert-llm-system:multi-arch \
  --push .
```

## 🌐 Production Deployment

### With Reverse Proxy (Nginx)
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  expert-llm-system:
    image: expert-llm-system:latest
    restart: always
    expose:
      - "8501"
    environment:
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
    networks:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - backend
    depends_on:
      - expert-llm-system

networks:
  backend:
    driver: bridge
```

### With SSL/TLS
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name expert-llm.yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location / {
        proxy_pass http://expert-llm-system:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 Monitoring Setup

### With Prometheus & Grafana
```bash
# Start monitoring stack
docker-compose --profile monitoring up -d

# Access services
# Grafana: http://localhost:3000 (admin/expert-llm-admin)
# Prometheus: http://localhost:9090
```

### Health Monitoring
```bash
# Check container health
docker inspect expert-llm-system --format='{{.State.Health.Status}}'

# View health check logs
docker logs expert-llm-system | grep health
```

## 🔒 Security Configuration

### Non-root User
The container runs as a non-root user (`appuser`) for security.

### Resource Limits
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

### Network Security
```yaml
networks:
  expert-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 🔧 Troubleshooting

### Common Issues

1. **Container won't start**
   ```bash
   # Check logs
   docker logs expert-llm-system
   
   # Run health check
   docker run --rm expert-llm-system health
   ```

2. **Port already in use**
   ```bash
   # Find process using port 8501
   lsof -i :8501
   
   # Use different port
   docker run -p 8502:8501 expert-llm-system
   ```

3. **Memory issues**
   ```bash
   # Increase Docker memory limit
   docker run --memory=4g expert-llm-system
   ```

4. **Ollama connection issues**
   ```bash
   # Check Ollama service
   docker-compose exec ollama ollama list
   
   # Test connectivity
   docker-compose exec expert-llm-system curl http://ollama:11434/api/tags
   ```

### Debug Mode
```bash
# Run with debug logging
docker run -e LOG_LEVEL=DEBUG expert-llm-system

# Interactive shell
docker run -it expert-llm-system bash
```

## 📦 Container Registry

### Push to Docker Hub
```bash
# Tag image
docker tag expert-llm-system:latest yourusername/expert-llm-system:latest

# Push image
docker push yourusername/expert-llm-system:latest
```

### Push to Private Registry
```bash
# Build and push
./build-docker.sh \
  --registry registry.yourcompany.com \
  --push \
  --tag v1.0.0
```

## 🔄 Updates and Rollbacks

### Update to New Version
```bash
# Pull new image
docker pull expert-llm-system:v1.1.0

# Stop current container
docker stop expert-llm-system

# Start with new image
docker run -d \
  --name expert-llm-system \
  -p 8501:8501 \
  -v expert-data:/app/data \
  expert-llm-system:v1.1.0
```

### Rollback
```bash
# Rollback to previous version
docker stop expert-llm-system
docker rm expert-llm-system
docker run -d \
  --name expert-llm-system \
  -p 8501:8501 \
  -v expert-data:/app/data \
  expert-llm-system:v1.0.0
```

## 📈 Performance Optimization

### Resource Allocation
```bash
# For high-load environments
docker run \
  --memory=8g \
  --cpus=4 \
  --memory-swappiness=10 \
  expert-llm-system
```

### Storage Optimization
```bash
# Use bind mounts for better performance
docker run \
  -v /fast-ssd/expert-data:/app/data \
  -v /fast-ssd/expert-logs:/app/logs \
  expert-llm-system
```

## 🧪 Testing

### Automated Testing
```bash
# Run container tests
docker run --rm expert-llm-system health

# Load testing
docker run --rm \
  -v $(pwd)/tests:/tests \
  expert-llm-system \
  python /tests/load_test.py
```

### Manual Testing
```bash
# Test dashboard accessibility
curl -f http://localhost:8501/_stcore/health

# Test expert patterns
curl -X POST http://localhost:8501/api/analyze \
  -d '{"query": "disk space issue"}'
```

## 🆘 Support

### Logs Collection
```bash
# Collect all logs
mkdir -p debug-logs
docker logs expert-llm-system > debug-logs/container.log 2>&1
docker cp expert-llm-system:/app/logs debug-logs/app-logs
tar -czf expert-llm-debug-$(date +%Y%m%d).tar.gz debug-logs/
```

### System Information
```bash
# Container information
docker inspect expert-llm-system

# Resource usage
docker stats expert-llm-system --no-stream

# Network information
docker network ls
docker network inspect expert-network
```

---

## 📊 Quick Reference

### Essential Commands
```bash
# Build
./build-docker.sh

# Run
docker-compose up -d

# Logs
docker-compose logs -f

# Health
docker exec expert-llm-system curl -f http://localhost:8501/_stcore/health

# Shell
docker exec -it expert-llm-system bash

# Stop
docker-compose down
```

### URLs
- **Dashboard**: http://localhost:8501
- **Ollama API**: http://localhost:11434
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

This Docker setup provides a complete, production-ready deployment of the Expert LLM System with monitoring, security, and scalability features.

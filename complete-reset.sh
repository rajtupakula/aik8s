#!/bin/bash

# Expert LLM System - Complete Reset and Start
# This script will clean everything and start fresh

echo "🧹 EXPERT LLM SYSTEM - COMPLETE RESET"
echo "======================================"

# Step 1: Clean Docker
echo "Step 1: Cleaning Docker..."
docker stop $(docker ps -aq) 2>/dev/null
docker rm $(docker ps -aq) 2>/dev/null
docker system prune -af
docker rmi expert-llm-system:latest 2>/dev/null
docker rmi localhost/expert-llm-system:latest 2>/dev/null

# Step 2: Clean Minikube images
echo "Step 2: Cleaning Minikube images..."
minikube image rm expert-llm-system:latest 2>/dev/null
minikube image rm localhost/expert-llm-system:latest 2>/dev/null

# Step 3: Delete Kubernetes deployment
echo "Step 3: Removing Kubernetes deployment..."
kubectl delete namespace expert-llm-system 2>/dev/null

# Step 4: Build new image
echo "Step 4: Building fresh image..."
minikube image build -t localhost/expert-llm-system:latest .

# Step 5: Deploy to Kubernetes
echo "Step 5: Deploying to Kubernetes..."
kubectl apply -f k8s/simple-deployment.yaml

# Step 6: Wait for deployment
echo "Step 6: Waiting for deployment..."
kubectl wait --for=condition=available --timeout=300s deployment/expert-llm-system -n expert-llm-system

# Step 7: Show status
echo "Step 7: Current status:"
kubectl get all -n expert-llm-system

echo ""
echo "🌐 READY TO ACCESS UI!"
echo "======================"
echo ""
echo "Run this command to access the UI:"
echo "kubectl port-forward -n expert-llm-system svc/expert-llm-service 8501:8501"
echo ""
echo "Then open: http://localhost:8501"

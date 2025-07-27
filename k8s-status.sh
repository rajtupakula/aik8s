#!/bin/bash

echo "🎉 Expert LLM System Kubernetes Deployment Status"
echo "=================================================="
echo ""

echo "📊 Cluster Info:"
kubectl cluster-info | head -1

echo ""
echo "🏃‍♂️ Pod Status:"
kubectl get pods -n expert-llm-system

echo ""
echo "🌐 Service Status:"
kubectl get svc -n expert-llm-system

echo ""
echo "🔗 Access URLs:"
MINIKUBE_IP=$(minikube ip)
echo "   • Minikube URL: http://${MINIKUBE_IP}:30501"
echo "   • Port Forward: kubectl port-forward -n expert-llm-system svc/expert-llm-service 8501:8501"
echo ""

echo "📋 Useful Commands:"
echo "   • View logs: kubectl logs -n expert-llm-system deployment/expert-llm-system -f"
echo "   • Scale deployment: kubectl scale -n expert-llm-system deployment/expert-llm-system --replicas=2"
echo "   • Delete deployment: kubectl delete -f k8s/simple-deployment.yaml"
echo ""

echo "🚀 Expert LLM System is running on Kubernetes!"

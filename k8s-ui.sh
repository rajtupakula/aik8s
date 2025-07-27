#!/bin/bash

# Simple port forward command for Kubernetes UI
echo "🌐 Expert LLM System - Kubernetes UI Access"
echo "Starting port forward on http://localhost:8501"
echo "Press Ctrl+C to stop"
echo ""

kubectl port-forward -n expert-llm-system svc/expert-llm-service 8501:8501

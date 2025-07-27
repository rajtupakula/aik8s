#!/usr/bin/env python3

import sys
import os

print("🔍 Testing Kubernetes connectivity...")

try:
    from kubernetes import client, config
    print("✅ Kubernetes library imported successfully")
    
    # Check if we're running in a pod
    if os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount'):
        print("✅ Running in Kubernetes pod")
        config.load_incluster_config()
        print("✅ In-cluster config loaded")
    else:
        print("❌ Not running in Kubernetes pod")
        config.load_kube_config()
        print("✅ Local kube config loaded")
    
    v1 = client.CoreV1Api()
    print("✅ Kubernetes API client created")
    
    # Test API access
    pods = v1.list_namespaced_pod(namespace='expert-llm-system')
    running_pods = sum(1 for pod in pods.items if pod.status.phase == 'Running')
    print(f"✅ Found {running_pods} running pods in expert-llm-system namespace")
    
    # Test permissions
    print("✅ Kubernetes API access successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

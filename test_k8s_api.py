#!/usr/bin/env python3
"""
Test script to verify Kubernetes API access from within the pod
"""

try:
    from kubernetes import client, config
    
    # Load in-cluster config
    config.load_incluster_config()
    
    # Create API client
    v1 = client.CoreV1Api()
    
    print("✅ Kubernetes API connection successful!")
    
    # Test listing pods
    pods = v1.list_pod_for_all_namespaces()
    print(f"✅ Found {len(pods.items)} pods across all namespaces")
    
    # Test listing some pod details
    for i, pod in enumerate(pods.items[:3]):  # Show first 3 pods
        ready_count = 0
        total_count = len(pod.status.container_statuses) if pod.status.container_statuses else 0
        
        if pod.status.container_statuses:
            for container in pod.status.container_statuses:
                if container.ready:
                    ready_count += 1
        
        ready_status = f"{ready_count}/{total_count}"
        print(f"  Pod {i+1}: {pod.metadata.namespace}/{pod.metadata.name} - {ready_status} {pod.status.phase}")
    
    print("✅ Kubernetes API test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
"""
Direct test of Kubernetes API to show what the chat should display
"""

try:
    from kubernetes import client, config
    
    # Load in-cluster config
    config.load_incluster_config()
    
    # Create API client
    v1 = client.CoreV1Api()
    
    print("🚀 KUBERNETES API TEST - This is what the chat should show:")
    print("=" * 60)
    
    # Get pods from all namespaces (what kubectl get pods --all-namespaces would show)
    pods = v1.list_pod_for_all_namespaces()
    
    output = "NAMESPACE        NAME                                 READY   STATUS    RESTARTS   AGE\n"
    from datetime import datetime, timezone
    
    for pod in pods.items:
        # Calculate ready containers
        ready_count = 0
        total_count = len(pod.status.container_statuses) if pod.status.container_statuses else 0
        
        if pod.status.container_statuses:
            for container in pod.status.container_statuses:
                if container.ready:
                    ready_count += 1
        
        ready_status = f"{ready_count}/{total_count}"
        
        # Calculate age
        if pod.status.start_time:
            age = (datetime.now(timezone.utc) - pod.status.start_time).days
            age_str = f"{age}d" if age > 0 else "<1d"
        else:
            age_str = "unknown"
        
        # Get restart count
        restart_count = 0
        if pod.status.container_statuses:
            for container in pod.status.container_statuses:
                restart_count += container.restart_count
        
        output += f"{pod.metadata.namespace:<16} {pod.metadata.name:<35} {ready_status:<7} {pod.status.phase:<9} {restart_count:<10} {age_str}\n"
    
    print(output)
    print("=" * 60)
    print(f"✅ Found {len(pods.items)} pods total")
    print("✅ This is the live data that should appear in the chat!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

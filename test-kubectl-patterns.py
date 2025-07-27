#!/usr/bin/env python3

# Quick test for kubectl pattern matching
import re

def test_kubectl_patterns():
    test_queries = [
        "check the errors in the logs of expert-llm-system-77b9567866-m8v6c",
        "show me logs for pod my-app-123",
        "get logs from container xyz-456",
        "describe pod expert-llm-system-77b9567866-m8v6c",
        "what's the status of pod abc-789",
        "list all pods",
        "show pods in cluster"
    ]
    
    kubectl_patterns = {
        'logs': [
            r'check.*logs?.*(?:of|for|in)\s+([a-z0-9-]+)',
            r'(?:show|get).*logs?.*(?:of|for|from)\s+(?:pod\s+)?([a-z0-9-]+)',
            r'errors?.*logs?.*(?:of|for|from)\s+([a-z0-9-]+)',
            r'(?:view|see).*logs?.*(?:of|for|from)\s+([a-z0-9-]+)'
        ],
        'describe': [
            r'describe.*pod\s+([a-z0-9-]+)',
            r'(?:status|details|info).*(?:of|for|about)\s+(?:pod\s+)?([a-z0-9-]+)',
            r'what.*(?:status|condition).*([a-z0-9-]+)'
        ],
        'get': [
            r'list.*pods?',
            r'show.*pods?',
            r'get.*pods?',
            r'all.*pods?'
        ]
    }
    
    print("Testing kubectl pattern matching:")
    print("="*50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        query_lower = query.lower()
        matched = False
        
        for cmd_type, patterns in kubectl_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query_lower)
                if match:
                    print(f"✅ Matched: {cmd_type}")
                    if match.groups():
                        print(f"   Pod name: {match.group(1)}")
                    matched = True
                    break
            if matched:
                break
        
        if not matched:
            print("❌ No match found")

if __name__ == "__main__":
    test_kubectl_patterns()

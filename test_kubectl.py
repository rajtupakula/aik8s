#!/usr/bin/env python3
"""
Test the updated _execute_safe_command with Kubernetes API integration
"""

import sys
import os
sys.path.append('/app/src')

try:
    # Test the updated enhanced_rag_agent
    from agent.enhanced_rag_agent import EnhancedRAGAgent
    
    print("✅ Creating Enhanced RAG Agent...")
    agent = EnhancedRAGAgent()
    
    print("✅ Testing kubectl command execution...")
    result = agent._execute_safe_command('kubectl get pods --all-namespaces')
    
    print("✅ Command execution result:")
    print("=" * 50)
    print(result)
    print("=" * 50)
    
    print("✅ Test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

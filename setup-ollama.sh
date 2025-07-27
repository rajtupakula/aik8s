#!/bin/bash
# Setup Ollama with llama3.2 model and expert knowledge

set -e

echo "🚀 Setting up Ollama with Expert Knowledge..."

# Wait for Ollama service to be ready
wait_for_ollama() {
    echo "⏳ Waiting for Ollama to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "✅ Ollama is ready!"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts: Ollama not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Ollama failed to start after $max_attempts attempts"
    return 1
}

# Download llama3.2 model
download_model() {
    echo "📥 Downloading llama3.2 model..."
    /usr/local/bin/ollama pull llama3.2:latest
    if [ $? -eq 0 ]; then
        echo "✅ llama3.2 model downloaded successfully"
    else
        echo "❌ Failed to download llama3.2 model"
        return 1
    fi
}

# Create a custom Modelfile with expert system knowledge
create_expert_modelfile() {
    echo "🧠 Creating expert system knowledge base..."
    
    cat > /tmp/expertfile << 'EOF'
FROM llama3.2

# System prompt for expert system administration
SYSTEM """You are an expert system administrator with deep knowledge of:

1. **Kubernetes (K8s)**:
   - Pod lifecycle management and troubleshooting
   - Service discovery and networking
   - ConfigMaps, Secrets, and Volume management
   - Deployment strategies and scaling
   - Resource management and monitoring
   - RBAC and security best practices
   - Cluster debugging and performance tuning

2. **GlusterFS**:
   - Distributed file system architecture
   - Volume creation, management, and optimization
   - Peer management and cluster operations
   - Healing processes and split-brain resolution
   - Performance tuning and monitoring
   - Backup and disaster recovery
   - Integration with Kubernetes storage classes

3. **Ubuntu Linux Administration**:
   - System monitoring and performance analysis
   - Package management and system updates
   - Network configuration and troubleshooting
   - Log analysis and debugging
   - Service management with systemd
   - Security hardening and compliance
   - Storage management and filesystem operations

**Response Format**: Always respond with valid JSON containing:
- "analysis": Brief analysis of the issue
- "diagnosis": Root cause identification  
- "recommendations": Actionable steps (array)
- "safety_considerations": Safety warnings (array)
- "commands": Safe commands to execute (array)
- "risk_level": "SAFE", "MEDIUM", or "HIGH"

**Safety First**: Never suggest destructive commands without explicit warnings.
Always prioritize system stability and data integrity.
"""

# Set parameters for consistent, focused responses
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
EOF

    /usr/local/bin/ollama create expert-llm -f /tmp/expertfile
    if [ $? -eq 0 ]; then
        echo "✅ Expert system model created successfully"
    else
        echo "❌ Failed to create expert system model"
        return 1
    fi
}

# Test the model
test_model() {
    echo "🧪 Testing expert model..."
    
    local test_response
    test_response=$(/usr/local/bin/ollama run expert-llm "List Kubernetes pods in a cluster safely" --format json 2>/dev/null || echo '{"error": "failed"}')
    
    if echo "$test_response" | grep -q "analysis"; then
        echo "✅ Expert model is working correctly"
        echo "Sample response: $test_response"
    else
        echo "⚠️  Expert model test failed, but model is available"
    fi
}

# Main execution
main() {
    echo "🔧 Expert LLM System - Ollama Setup"
    echo "=================================="
    
    # Set environment variables
    export OLLAMA_HOST=0.0.0.0:11434
    export OLLAMA_ORIGINS="*"
    
    wait_for_ollama || exit 1
    download_model || exit 1
    create_expert_modelfile || exit 1
    test_model
    
    echo ""
    echo "🎉 Ollama setup completed successfully!"
    echo "📊 Available models:"
    /usr/local/bin/ollama list
    echo ""
    echo "🚀 Expert LLM System is ready for Kubernetes and GlusterFS queries!"
}

main "$@"

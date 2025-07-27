#!/bin/bash

echo "🚀 Starting Expert LLM Agent - Working UI"
echo "========================================="
echo ""
echo "✅ This version bypasses all Kubernetes issues"
echo "✅ Direct Python execution for immediate access"
echo "✅ Full expert pattern functionality"
echo ""

cd "$(dirname "$0")"

# Install dependencies if needed
echo "📦 Installing required packages..."
pip3 install streamlit pandas plotly psutil pyyaml 2>/dev/null || {
    echo "⚠️  Note: Some packages may already be installed"
}

echo ""
echo "🌐 Starting Streamlit UI..."
echo "📍 Access URL: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the UI
streamlit run working_ui.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=false \
    --browser.gatherUsageStats=false

#!/bin/bash
# Keap Export UI Startup Script

echo "🚀 Starting Keap Export UI..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f "/opt/es-keap-database/.env" ]; then
    echo "❌ Error: .env file not found at /opt/es-keap-database/.env"
    echo "Please ensure the environment file exists with database configuration."
    exit 1
fi

# Check if Keap tokens exist
if [ ! -f "/opt/es-keap-database/.keap_tokens.json" ]; then
    echo "❌ Error: Keap tokens not found at /opt/es-keap-database/.keap_tokens.json"
    echo "Please ensure Keap API tokens are available."
    exit 1
fi

echo "✅ Environment checks passed"
echo "🌐 Starting Streamlit application..."
echo "📊 UI will be available at: http://localhost:8501"
echo "🔒 This is a read-only interface - no data will be modified"

# Start Streamlit
.venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0

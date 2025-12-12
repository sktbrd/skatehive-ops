#!/bin/bash
# Run SkatehiveOps Dashboard
# Automatically detects if packages are available or if virtual environment is needed

echo "🛠️  Starting SkatehiveOps Dashboard..."

# Prefer local virtualenv if present (ensures consistent speedtest binary)
if [ -x "venv/bin/python" ]; then
    echo "🔧 Using local virtualenv"
    venv/bin/python dashboard.py
else
    # Check if required packages are available in system Python
    if python3 -c "import requests, rich" 2>/dev/null; then
        echo "✅ Using system Python packages"
        python3 dashboard.py
    else
        # Check legacy virtual environment
        if [ -d "skatehive-venv" ]; then
            echo "🔧 Using legacy virtual environment"
            source skatehive-venv/bin/activate
            python3 dashboard.py
            deactivate
        else
            echo "❌ Required packages not found!"
            echo "Please run: ./setup-server-dependencies.sh first"
            exit 1
        fi
    fi
fi

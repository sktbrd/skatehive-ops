#!/bin/bash
# Server Setup Script for SkatehiveOps Dashboard
# Run this on your server (Raspberry Pi)

echo "🚀 Setting up SkatehiveOps Dashboard dependencies..."

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install Python3 and pip if not already installed
echo "🐍 Installing Python3 and pip..."
sudo apt install -y python3 python3-pip

# Install required Python packages
echo "📚 Installing Python packages..."
pip3 install --user rich requests

# Optional: Install speedtest-cli for internet speed monitoring
echo "🌐 Installing speedtest-cli..."
sudo apt install -y speedtest-cli

# Verify installations
echo "✅ Verifying installations..."
python3 -c "import rich; print('✓ Rich library installed')"
python3 -c "import requests; print('✓ Requests library installed')"

echo "🎉 Setup complete! You can now run the dashboard."
echo ""
echo "To run the dashboard:"
echo "  cd /path/to/skatehive-ops"
echo "  python3 dashboard.py"

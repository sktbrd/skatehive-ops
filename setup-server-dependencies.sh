#!/bin/bash
# Server Setup Script for SkatehiveOps Dashboard
# Run this on your server (Raspberry Pi)

echo "🚀 Setting up SkatehiveOps Dashboard dependencies..."

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install Python3 and required system packages
echo "🐍 Installing Python3 and system packages..."
sudo apt install -y python3 python3-pip python3-full python3-venv

# Try to install packages via apt first (system packages)
echo "� Installing Python packages via apt..."
sudo apt install -y python3-requests python3-rich

# Check if system packages worked
if python3 -c "import requests, rich" 2>/dev/null; then
    echo "✅ System packages installed successfully!"
else
    echo "⚠️  System packages not available, creating virtual environment..."
    
    # Create virtual environment
    echo "🔧 Creating virtual environment..."
    python3 -m venv skatehive-venv
    
    # Activate and install packages
    echo "� Installing packages in virtual environment..."
    source skatehive-venv/bin/activate
    pip install rich requests
    deactivate
    
    echo "ℹ️  Virtual environment created at: $(pwd)/skatehive-venv"
    echo "ℹ️  To run dashboard with venv:"
    echo "     source skatehive-venv/bin/activate"
    echo "     python3 dashboard.py"
    echo "     deactivate"
fi

# Optional: Install speedtest-cli for internet speed monitoring
echo "🌐 Installing speedtest-cli..."
sudo apt install -y speedtest-cli

# Verify installations
echo "✅ Verifying installations..."
if python3 -c "import rich; print('✓ Rich library available')" 2>/dev/null; then
    echo "✓ Rich library OK"
else
    echo "⚠️  Rich library not in system Python"
fi

if python3 -c "import requests; print('✓ Requests library available')" 2>/dev/null; then
    echo "✓ Requests library OK"
else
    echo "⚠️  Requests library not in system Python"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To run the dashboard:"
echo "Option 1 (if system packages work):"
echo "  python3 dashboard.py"
echo ""
echo "Option 2 (if using virtual environment):"
echo "  source skatehive-venv/bin/activate"
echo "  python3 dashboard.py"
echo "  deactivate"

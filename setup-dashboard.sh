#!/bin/bash

# SkatehiveOps Dashboard Setup Script
echo "🛠️  Setting up SkatehiveOps Dashboard..."

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt update
sudo apt install -y python3-pip speedtest-cli curl

# Install Python packages
echo "🐍 Installing Python packages..."
pip3 install rich requests

# Make dashboard executable
chmod +x dashboard.py

# Create systemd service for dashboard (optional)
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/skatehive-dashboard.service > /dev/null <<EOF
[Unit]
Description=SkatehiveOps Dashboard
After=docker.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/skatehive/skate-insta
ExecStart=/usr/bin/python3 /home/pi/skatehive/skate-insta/dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Setup complete!"
echo ""
echo "🚀 To run the dashboard:"
echo "   cd ~/skatehive/skate-insta && python3 dashboard.py"
echo ""
echo "🔧 To run as a service:"
echo "   sudo systemctl enable skatehive-dashboard"
echo "   sudo systemctl start skatehive-dashboard"
echo ""
echo "📊 Dashboard features:"
echo "   • Real-time internet speed monitoring"
echo "   • Service health checks (video-worker, ytipfs-worker)"
echo "   • Docker container stats (CPU, Memory)"
echo "   • Live service logs"
echo "   • Auto-refresh every 10 seconds"
echo "   • Speed test every 5 minutes"

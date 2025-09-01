# SkatehiveOps Dashboard 🛠️

A beautiful terminal dashboard for monitoring Skatehive infrastructure services.

## Features

🌐 **Real-time Internet Monitoring**
- Connection status and latency
- Automated speed tests every 5 minutes
- Download/Upload speeds and ping

🚀 **Service Health Monitoring**
- video-worker (port 8081)
- ytipfs-worker (port 6666)
- Response times and uptime tracking
- Docker container resource usage (CPU/Memory)

📋 **Live Service Logs**
- Real-time log streaming
- Color-coded log levels (errors, warnings, success)
- Smart log filtering and truncation

⚡ **Auto-refresh Dashboard**
- Updates every 10 seconds
- Responsive terminal UI with Rich library
- Grid layout with organized panels

## Quick Start

### On your Raspberry Pi server:

```bash
# Clone the repository
git clone https://github.com/sktbrd/skatehive-ops.git
cd skatehive-ops

# Run setup script
chmod +x setup-dashboard.sh
./setup-dashboard.sh

# Start the dashboard
python3 dashboard.py
```

## Usage

```bash
python3 dashboard.py
```

Built with ❤️ for the Skatehive community 🛹

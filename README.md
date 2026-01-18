# SkatehiveOps Dashboard 🛠️

A beautiful terminal dashboard for real-time monitoring of Skatehive infrastructure services across Mac Mini M4 and Raspberry Pi servers.

## Features

### 🌐 **Internet Monitoring**
- Connection status and latency tracking
- Automated speed tests every 5 minutes
- Download/Upload speeds and ping measurements
- Network stability monitoring

### 🚀 **Service Health Monitoring**

**Mac Mini M4 (Primary) - via Tailscale Funnel:**
- **Video Transcoder** - `https://minivlad.tail83ea3e.ts.net/video/healthz`
  - Port: 8081 (external), 8080 (internal)
  - Container: `video-worker`
  - Monitors: Response time, uptime, processing statistics

- **Instagram Downloader** - `https://minivlad.tail83ea3e.ts.net/instagram/health`
  - Port: 6666 (external), 8000 (internal)
  - Container: `ytipfs-worker`
  - Monitors: Response time, cookie status, expiration tracking

- **Account Manager** - `https://minivlad.tail83ea3e.ts.net/healthz`
  - Port: 3001
  - Container: `skatehive-account-manager`
  - Monitors: Response time, Hive node connectivity, RC status

**Raspberry Pi (Backup) - via Tailscale:**
- **Video Transcoder** - `https://vladsberry.tail83ea3e.ts.net/video/healthz`
- **Instagram Downloader** - `https://vladsberry.tail83ea3e.ts.net/instagram/health`

### 📊 **Resource Tracking**
- Docker container CPU usage monitoring
- Memory usage tracking per container
- Container status (running/stopped/restarting)
- Resource alerts and warnings

### 📋 **Live Service Logs**
- Real-time log streaming from services
- Color-coded log levels:
  - 🔴 Errors (red)
  - 🟡 Warnings (yellow)
  - 🟢 Success (green)
  - ℹ️  Info (blue)
- Smart log filtering and truncation
- Deduplication of repeated messages
- Timestamp tracking

### 🚨 **Error Detection & Alerting**
- Rate limit error detection (Instagram)
- Authentication failure tracking
- Service timeout monitoring
- Cookie expiration warnings
- RC insufficiency alerts (Account Manager)

### ⚡ **Dashboard UI**
- Auto-refresh every 10 seconds
- Responsive grid layout
- Terminal size detection (small/medium/large layouts)
- Real-time panel updates
- Rich formatting with emojis and colors

## Layout Panels

### Small Layout (height < 30)
- Internet Status
- Service Health (compact)

### Small Layout (height < 30)
- Internet Status
- Service Health (compact)
- Recent Errors

### Medium Layout (height < 50)
- Internet Status
- Service Health (detailed)
- Docker Resources
- Recent Logs

### Large Layout (height ≥ 50)
- Internet Status
- Service Health (Mac Mini M4)
- Service Health (Raspberry Pi)
- Docker Resources
- Instagram Logs (live)
- Video Transcoder Logs (live)
- Error Summary

## Quick Start

### On Mac Mini M4 or Raspberry Pi:

```bash
# Clone the repository
cd skatehive-monorepo/skatehive-dashboard

# Install dependencies (first time only)
pip3 install rich requests docker

# Start the dashboard
python3 dashboard.py
```

## Usage

```bash
# Run dashboard
python3 dashboard.py

# Exit dashboard
Press Ctrl+C
```

## Configuration

The dashboard automatically detects:
- Your terminal size and adjusts layout
- Available services via Tailscale Funnel
- Docker containers on localhost
- Network connectivity status

**Monitored Endpoints:**
- Mac Mini services: `https://minivlad.tail83ea3e.ts.net`
- Raspberry Pi services: `https://vladsberry.tail83ea3e.ts.net`
- Local Docker API: `unix:///var/run/docker.sock`

## Troubleshooting

### Dashboard shows "Service Unavailable"

**Cause:** Service is down or Tailscale connectivity issue

**Solution:**
1. Check service is running: `docker ps`
2. Test endpoint directly: `curl https://minivlad.tail83ea3e.ts.net/video/healthz`
3. Verify Tailscale: `tailscale status`
4. Check Funnel: `tailscale funnel status`

### "Connection Error" for Docker resources

**Cause:** Docker API not accessible or permission issue

**Solution:**
1. Check Docker is running: `docker ps`
2. Verify user in docker group: `groups $USER`
3. Add user to docker group: `sudo usermod -aG docker $USER`
4. Re-login or run: `newgrp docker`

### Terminal size too small warning

**Cause:** Terminal window is too small for dashboard layout

**Solution:**
1. Resize terminal window (minimum 80x30 recommended)
2. Dashboard will auto-adjust to small layout
3. For full experience, use 150x50 terminal size

### "Rate limit" errors showing

**Cause:** Instagram cookie expiration or authentication failure

**Solution:**
1. Check Instagram cookie status: `curl https://minivlad.tail83ea3e.ts.net/instagram/health`
2. Refresh cookies (see instagram-downloader README)
3. Dashboard will automatically detect and display resolution

### Dashboard not updating

**Cause:** Network connectivity issue or service crash

**Solution:**
1. Check internet connection
2. Test services manually with curl
3. Restart dashboard: `Ctrl+C` then `python3 dashboard.py`
4. Check terminal supports required features

## Technical Details

**Requirements:**
- Python 3.7+
- Rich library (terminal UI)
- Requests library (HTTP client)
- Docker SDK for Python (container monitoring)

**Update Interval:**
- Dashboard refresh: 10 seconds
- Speed test: 5 minutes (automatic)
- Log streaming: Real-time
- Resource monitoring: 10 seconds

**Supported Platforms:**
- macOS (Mac Mini M4)
- Linux (Raspberry Pi OS)
- Any Unix-like system with Python 3

Built with ❤️ for the Skatehive community 🛹

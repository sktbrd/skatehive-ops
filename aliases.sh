# SkatehiveOps Dashboard Aliases
# Add these to your ~/.bashrc or ~/.zshrc

# Dashboard shortcuts
alias dashboard='cd ~/skatehive/skate-insta && python3 dashboard.py'
alias dash='dashboard'
alias ops='dashboard'

# Service management
alias services='sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias logs-video='sudo docker logs -f video-worker'
alias logs-ytipfs='sudo docker logs -f ytipfs-worker'
alias restart-video='cd ~/skatehive/skate-insta/video-worker && sudo docker compose restart'
alias restart-ytipfs='cd ~/skatehive/skate-insta/ytipfs-worker && sudo docker compose restart'

# System monitoring
alias speed='speedtest'
alias ports='sudo netstat -tlnp | grep -E "(8000|8081|6666)"'
alias tailscale-status='tailscale status && tailscale funnel status'

# Quick health checks
alias health='curl -s http://localhost:6666/health && echo && curl -s http://localhost:8081/health'
alias health-public='curl -s https://raspberrypi.tail83ea3e.ts.net/health'

echo "🛠️  SkatehiveOps aliases loaded!"
echo "Commands: dashboard, services, logs-video, logs-ytipfs, speed, health"

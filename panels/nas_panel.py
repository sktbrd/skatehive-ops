#!/usr/bin/env python3
"""
NAS Panel
Displays OpenMediaVault/nginx status and metrics
"""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def create_nas_panel(monitor) -> Panel:
    """Create NAS status panel"""
    table = Table(show_header=False, padding=(0, 1), box=None)
    table.add_column("Metric", style="cyan", width=20)
    table.add_column("Value", style="green", width=30)
    
    # Get NAS service health
    nas_health = monitor.check_service_health("nas")
    
    # Status row
    status_text = Text()
    if "🟢" in nas_health["status"]:
        status_text.append("🟢 Online", style="green bold")
    else:
        status_text.append("🔴 Offline", style="red bold")
    
    table.add_row("Status", status_text)
    table.add_row("Response Time", nas_health["response_time"])
    table.add_row("Details", nas_health.get("details", "N/A"))
    table.add_row("Public URL", "raspberrypi.tail83ea3e.ts.net")
    
    # Container uptime if available
    uptime = nas_health.get("uptime", "N/A")
    table.add_row("Container Uptime", uptime)
    
    # Get Docker stats for nginx container
    docker_stats = monitor.get_docker_stats()
    nginx_stats = docker_stats.get("nginx", {"cpu": "N/A", "memory": "N/A"})
    
    table.add_row("CPU Usage", nginx_stats["cpu"])
    table.add_row("Memory Usage", nginx_stats["memory"])
    
    return Panel(table, title="🗄️ NAS (OpenMediaVault)", border_style="blue")

#!/usr/bin/env python3
"""
Services Status Panel
Displays status, uptime, and resource usage for monitored services
"""

from rich.panel import Panel
from rich.table import Table


def create_services_panel(monitor) -> Panel:
    """Create services status panel"""
    table = Table(show_header=True, header_style="bold cyan", padding=(0, 1), box=None)
    table.add_column("Service", style="cyan", width=12)
    table.add_column("Status", style="green", width=8)
    table.add_column("Response", style="yellow", width=8)
    table.add_column("CPU", style="red", width=6)
    table.add_column("Memory", style="blue", width=8)
    
    docker_stats = monitor.get_docker_stats()
    
    for service_name in monitor.services:
        health = monitor.check_service_health(service_name)
        container_name = monitor.services[service_name]["container"]
        stats = docker_stats.get(container_name, {"cpu": "N/A", "memory": "N/A"})
        
        # Simple status display
        status = health["status"]
        if "Healthy" in status:
            status = "✅ Healthy"
        elif "Unhealthy" in status:
            status = "❌ Unhealthy"
        else:
            status = "⚠️ Unknown"
        
        table.add_row(
            service_name,
            status,
            health["response_time"],
            stats["cpu"],
            stats["memory"]
        )
    
    return Panel(table, title="🚀 Services Status", border_style="green")

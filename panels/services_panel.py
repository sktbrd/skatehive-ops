#!/usr/bin/env python3
"""
Services Status Panel
Displays status, uptime, and resource usage for monitored services
"""

from rich.panel import Panel
from rich.table import Table


def create_services_panel(monitor) -> Panel:
    """Create services status panel"""
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Response", style="yellow")
    table.add_column("Uptime", style="magenta")
    table.add_column("CPU", style="red")
    table.add_column("Memory", style="blue")
    
    docker_stats = monitor.get_docker_stats()
    
    for service_name in monitor.services:
        health = monitor.check_service_health(service_name)
        stats = docker_stats.get(service_name, {"cpu": "N/A", "memory": "N/A"})
        
        table.add_row(
            service_name,
            health["status"],
            health["response_time"],
            health["uptime"],
            stats["cpu"],
            stats["memory"]
        )
    
    return Panel(table, title="🚀 Services Status", border_style="green")

#!/usr/bin/env python3
"""
Services Status Panel
Displays status, uptime, and resource usage for monitored services
"""

from rich.panel import Panel
from rich.table import Table


def create_services_panel(monitor) -> Panel:
    """Create services status panel with enhanced visuals"""
    table = Table(show_header=True, header_style="bold cyan", padding=(0, 1))
    table.add_column("Service", style="cyan", width=12, no_wrap=True)
    table.add_column("Status", style="white", width=8, no_wrap=True)
    table.add_column("Response", style="yellow", width=8, no_wrap=True)
    table.add_column("CPU", style="red", width=6, no_wrap=True)
    table.add_column("Memory", style="blue", width=8, no_wrap=True)
    
    docker_stats = monitor.get_docker_stats()
    
    for service_name in monitor.services:
        health = monitor.check_service_health(service_name)
        stats = docker_stats.get(service_name, {"cpu": "N/A", "memory": "N/A"})
        
        # Enhanced status with colors and icons
        if "Healthy" in health["status"]:
            status_display = "[bright_green]✅ Healthy[/bright_green]"
        elif "Unhealthy" in health["status"]:
            status_display = "[bright_red]❌ Unhealthy[/bright_red]"
        else:
            status_display = "[yellow]⚠️ Unknown[/yellow]"
        
        # Color-code response times
        response = health["response_time"]
        if "ms" in response:
            try:
                ms = float(response.replace("ms", "").strip())
                if ms < 100:
                    response = f"[green]{response}[/green]"
                elif ms < 500:
                    response = f"[yellow]{response}[/yellow]"
                else:
                    response = f"[red]{response}[/red]"
            except:
                pass
        
        # Color-code CPU usage
        cpu = stats["cpu"]
        if cpu != "N/A" and "%" in cpu:
            try:
                cpu_val = float(cpu.replace("%", ""))
                if cpu_val < 50:
                    cpu = f"[green]{cpu}[/green]"
                elif cpu_val < 80:
                    cpu = f"[yellow]{cpu}[/yellow]"
                else:
                    cpu = f"[red]{cpu}[/red]"
            except:
                pass
        
        table.add_row(
            service_name,
            status_display,
            response,
            cpu,
            stats["memory"]
        )
    
    return Panel(table, title="🚀 Services Status", border_style="green")

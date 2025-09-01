#!/usr/bin/env python3
"""
Internet Status Panel
Displays internet connectivity and speed test information
"""

from datetime import datetime
from rich.panel import Panel
from rich.table import Table


def create_internet_panel(monitor) -> Panel:
    """Create internet status panel"""
    table = Table(show_header=True, header_style="bold cyan", padding=(0, 1))
    table.add_column("Metric", style="cyan", width=10, no_wrap=True)
    table.add_column("Value", style="green", width=15, no_wrap=True)
    
    # Basic connectivity
    conn_status = monitor.check_internet_connection()
    table.add_row("Connection", conn_status["status"])
    table.add_row("Latency", conn_status["latency"])
    
    # Speed test status and results
    status = monitor.speedtest_status
    if status == "Complete" and monitor.last_speed_test:
        # Show all metrics in a more compact way
        download = monitor.internet_speed.get('download', 0)
        upload = monitor.internet_speed.get('upload', 0)
        ping = monitor.internet_speed.get('ping', 0)
        
        table.add_row("Download", f"[bright_green]{download:.1f}[/bright_green] Mbps")
        table.add_row("Upload", f"[bright_yellow]{upload:.1f}[/bright_yellow] Mbps")
        table.add_row("Ping", f"[bright_magenta]{ping:.1f}[/bright_magenta] ms")
        
        age = datetime.now() - monitor.last_speed_test
        age_min = int(age.total_seconds()//60)
        age_color = "green" if age_min < 10 else "yellow" if age_min < 30 else "red"
        table.add_row("Last Test", f"[{age_color}]{age_min}m ago[/{age_color}]")
        
    elif status == "Running test...":
        table.add_row("Speed Test", "[yellow]🔄 Running...[/yellow]")
    elif status == "Failed":
        table.add_row("Speed Test", "[red]❌ Failed[/red]")
        if monitor.speedtest_error:
            error_msg = monitor.speedtest_error[:25] + "..." if len(monitor.speedtest_error) > 25 else monitor.speedtest_error
            table.add_row("Error", f"[red]{error_msg}[/red]")
    else:
        table.add_row("Speed Test", "[dim]🔄 Initializing...[/dim]")
    
    return Panel(table, title="🌐 Internet Status", border_style="blue")

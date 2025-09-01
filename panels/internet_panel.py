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
    table = Table(show_header=True, header_style="bold cyan", padding=(0, 0), box=None)
    table.add_column("Metric", style="cyan", width=10)
    table.add_column("Value", style="green", width=12)
    
    # Basic connectivity
    conn_status = monitor.check_internet_connection()
    table.add_row("Connection", conn_status["status"])
    table.add_row("Latency", conn_status["latency"])
    
    # Speed test status and results
    status = monitor.speedtest_status
    if status == "Complete" and monitor.last_speed_test:
        # Always show all three metrics
        download = monitor.internet_speed.get('download', 0)
        upload = monitor.internet_speed.get('upload', 0)
        ping = monitor.internet_speed.get('ping', 0)
        
        table.add_row("Download", f"{download:.1f} Mbps")
        table.add_row("Upload", f"{upload:.1f} Mbps")
        table.add_row("Ping", f"{ping:.1f} ms")
        age = datetime.now() - monitor.last_speed_test
        table.add_row("Last Test", f"{int(age.total_seconds()//60)}m ago")
    elif status == "Running test...":
        table.add_row("Speed Test", "🔄 Running...")
    elif status == "Failed":
        table.add_row("Speed Test", f"[red]Failed[/red]")
        if monitor.speedtest_error:
            # Truncate long error messages
            error_msg = monitor.speedtest_error[:30] + "..." if len(monitor.speedtest_error) > 30 else monitor.speedtest_error
            table.add_row("Error", f"[red]{error_msg}[/red]")
    else:
        table.add_row("Speed Test", "🔄 Init...")
    
    return Panel(table, title="🌐 Internet Status", border_style="blue")

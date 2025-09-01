#!/usr/bin/env python3
"""
SkatehiveOps Dashboard
A terminal dashboard for monitoring video-worker and ytipfs-worker services

Refactored into modular components for better maintainability.
"""

import asyncio
import subprocess
from rich.console import Console
from rich.live import Live

# Import our modules
from monitors.service_monitor import ServiceMonitor
from panels.internet_panel import create_internet_panel
from panels.services_panel import create_services_panel
from panels.hive_stats_panel import create_hive_stats_panel
from panels.logs_panel import create_logs_panel
from utils.layout import create_dashboard_layout, create_header_panel, create_footer_panel

console = Console()


async def run_periodic_speed_test(monitor: ServiceMonitor):
    """Run speed test every 5 minutes asynchronously"""
    while True:
        await monitor.run_speed_test_async()
        await asyncio.sleep(300)  # 5 minutes


async def main():
    """Main dashboard loop"""
    monitor = ServiceMonitor()
    layout = create_dashboard_layout()
    
    # Start initial speed test in background
    initial_speedtest_task = asyncio.create_task(monitor.run_speed_test_async())
    # Start periodic speed test
    speed_test_task = asyncio.create_task(run_periodic_speed_test(monitor))
    
    try:
        with Live(layout, refresh_per_second=1, screen=True):
            while True:
                # Update all panels
                layout["header"].update(create_header_panel())
                layout["internet"].update(create_internet_panel(monitor))
                layout["services"].update(create_services_panel(monitor))
                layout["hive_stats"].update(create_hive_stats_panel(monitor))
                layout["video_worker_logs"].update(
                    create_logs_panel(monitor, "video-worker", "📹 Video Worker Logs")
                )
                layout["ytipfs_logs"].update(
                    create_logs_panel(monitor, "ytipfs-worker", "📦 YTIPFS Worker Logs")
                )
                layout["footer"].update(create_footer_panel())
                
                await asyncio.sleep(10)  # Refresh every 10 seconds
                
    except KeyboardInterrupt:
        speed_test_task.cancel()
        initial_speedtest_task.cancel()
        console.print("\n[yellow]Dashboard stopped.[/yellow]")


if __name__ == "__main__":
    # Check for dependencies
    speedtest_available = False
    for cmd in ["speedtest", "speedtest-cli"]:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            speedtest_available = True
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    if not speedtest_available:
        console.print("[yellow]Warning: No speedtest command found. Speed tests will fail.[/yellow]")
        console.print("[yellow]Install with: sudo apt install speedtest-cli[/yellow]")
    
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[yellow]Warning: Docker not found. Container stats will be N/A.[/yellow]")
    
    # Install rich if not available
    try:
        import rich
    except ImportError:
        console.print("[yellow]Installing rich library...[/yellow]")
        subprocess.run(["pip3", "install", "rich"], check=True)
    
    # Run the dashboard
    asyncio.run(main())

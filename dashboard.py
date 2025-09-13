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
from panels.nas_panel import create_nas_panel
from panels.services_panel import create_services_panel
from panels.error_monitor_panel import create_error_monitor_panel
from panels.hive_stats_panel import create_hive_stats_panel
from panels.logs_panel import create_logs_panel
from panels.video_transcoder_panel import create_video_transcoder_panel
from panels.instagram_panel import create_instagram_panel, create_instagram_logs_panel
# Utils
from utils.layout import (
    create_dashboard_layout,
    create_header_panel,
    create_footer_panel,
    create_responsive_layout,
    create_responsive_header_panel,
    create_responsive_footer_panel,
    get_terminal_size
)

console = Console()


async def run_periodic_speed_test(monitor: ServiceMonitor):
    """Run speed test every 15 minutes asynchronously"""
    while True:
        await monitor.run_speed_test_async()
        await asyncio.sleep(900)  # 15 minutes


async def main():
    """Main dashboard loop with responsive design"""
    monitor = ServiceMonitor()
    
    # Print initial terminal size info
    width, height = get_terminal_size()
    console.print(f"[dim]Terminal size: {width}x{height} - Creating layout...[/dim]")
    
    try:
        layout = create_responsive_layout()
        console.print("[dim]Layout created successfully, starting dashboard...[/dim]")
    except Exception as e:
        console.print(f"[red]Error creating layout: {e}[/red]")
        # Fallback to simple layout
        layout = create_dashboard_layout()
    
    # Start initial speed test in background
    initial_speedtest_task = asyncio.create_task(monitor.run_speed_test_async())
    # Start periodic speed test
    speed_test_task = asyncio.create_task(run_periodic_speed_test(monitor))
    
    try:
        with Live(layout, refresh_per_second=1, screen=True, auto_refresh=True):
            console.print("[dim]Dashboard started, entering update loop...[/dim]")
            while True:
                try:
                    # Check if terminal size changed and recreate layout if needed
                    current_width, current_height = get_terminal_size()
                    if abs(current_width - width) > 10 or abs(current_height - height) > 5:
                        width, height = current_width, current_height
                        layout = create_responsive_layout()
                    
                    # Update panels that exist in current layout
                    try:
                        layout["header"].update(create_responsive_header_panel())
                    except KeyError:
                        pass
                    
                    try:
                        layout["internet"].update(create_internet_panel(monitor))
                    except KeyError:
                        pass
                    
                    try:
                        layout["nas"].update(create_nas_panel(monitor))
                    except KeyError:
                        pass
                    
                    try:
                        layout["services"].update(create_services_panel(monitor))
                    except KeyError:
                        pass
                    
                    try:
                        layout["error_monitor"].update(create_error_monitor_panel(monitor))
                    except KeyError:
                        pass
                    
                    try:
                        layout["instagram"].update(create_instagram_panel(monitor))
                    except KeyError:
                        pass
                    
                    try:
                        layout["hive_stats"].update(create_hive_stats_panel(monitor))
                    except KeyError:
                        pass
                    
                    try:
                        layout["video_transcoder"].update(create_video_transcoder_panel(monitor))
                    except KeyError:
                        pass
                    
                    try:
                        layout["video_logs"].update(
                            create_logs_panel(monitor, "video-worker", "📹 Video Worker Container Logs")
                        )
                    except KeyError:
                        try:
                            # For compact layout, combine both logs
                            layout["logs"].update(create_instagram_logs_panel(monitor))
                        except KeyError:
                            pass
                    
                    try:
                        layout["instagram_logs"].update(create_instagram_logs_panel(monitor))
                    except KeyError:
                        pass
                    
                    try:
                        layout["footer"].update(create_responsive_footer_panel())
                    except KeyError:
                        pass
                    
                    await asyncio.sleep(10)  # Refresh every 10 seconds
                except Exception as e:
                    console.print(f"[red]Error in update loop: {e}[/red]")
                    await asyncio.sleep(5)  # Wait before retrying
                
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

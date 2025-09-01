#!/usr/bin/env python3
"""
SkatehiveOps Dashboard
A terminal dashboard for monitoring video-worker and ytipfs-worker services
"""

import asyncio
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align

console = Console()

class ServiceMonitor:
    def __init__(self):
        self.services = {
            "video-worker": {
                "url": "http://localhost:8081/health",
                "port": 8081,
                "container": "video-worker"
            },
            "ytipfs-worker": {
                "url": "http://localhost:6666/health",
                "port": 6666,
                "container": "ytipfs-worker"
            }
        }
        self.internet_speed = {"download": 0, "upload": 0, "ping": 0}
        self.last_speed_test = None
        self.speedtest_status = "Initializing..."  # Initial status
        self.speedtest_error = None
        
    def check_internet_connection(self) -> Dict:
        """Check basic internet connectivity"""
        try:
            response = requests.get("https://8.8.8.8", timeout=5)
            return {"status": "🟢 Online", "latency": f"{response.elapsed.total_seconds()*1000:.0f}ms"}
        except:
            return {"status": "🔴 Offline", "latency": "N/A"}
    
    async def run_speed_test_async(self):
        """Run internet speed test asynchronously using speedtest"""
        self.speedtest_status = "Running test..."
        self.speedtest_error = None
        
        # Try different speedtest commands
        commands_to_try = [
            ["speedtest", "--format=json"],
            ["speedtest", "--json"],  # fallback for older versions
            ["speedtest-cli", "--json"],
            ["/usr/bin/speedtest", "--format=json"],
            ["/usr/local/bin/speedtest", "--format=json"]
        ]
        
        for cmd in commands_to_try:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    self.speedtest_error = "Test timeout (>2min)"
                    continue  # Try next command
                    
                if proc.returncode == 0:
                    try:
                        data = json.loads(stdout.decode())
                        # Handle different JSON formats from different speedtest tools
                        download_speed = 0
                        upload_speed = 0
                        ping_time = 0
                        
                        # Ookla speedtest format
                        if "download" in data and "bandwidth" in data["download"]:
                            download_speed = data["download"]["bandwidth"] * 8 / 1_000_000  # Convert bytes to Mbps
                            upload_speed = data["upload"]["bandwidth"] * 8 / 1_000_000
                            ping_time = data["ping"]["latency"]
                        # speedtest-cli format
                        elif "download" in data and isinstance(data["download"], (int, float)):
                            download_speed = data["download"] / 1_000_000
                            upload_speed = data["upload"] / 1_000_000
                            ping_time = data["ping"]
                        # Alternative format
                        elif "Download" in data and "Upload" in data:
                            download_speed = float(str(data["Download"]).split()[0])
                            upload_speed = float(str(data["Upload"]).split()[0])
                            ping_time = float(str(data.get("Ping", "0")).split()[0])
                        
                        self.internet_speed = {
                            "download": download_speed,
                            "upload": upload_speed,
                            "ping": ping_time
                        }
                        
                        self.last_speed_test = datetime.now()
                        self.speedtest_status = "Complete"
                        return  # Success, exit function
                    except Exception as e:
                        self.speedtest_error = f"JSON parse error: {e}"
                        continue  # Try next command
                else:
                    error_msg = stderr.decode().strip()
                    if "not found" in error_msg or "command not found" in error_msg:
                        continue  # Try next command
                    elif "Timeout occurred" in error_msg:
                        self.speedtest_error = "Connection timeout"
                        continue  # Try next command
                    elif "Error:" in error_msg:
                        # Extract just the error part, not the full output
                        error_lines = [line for line in error_msg.split('\n') if 'Error:' in line]
                        if error_lines:
                            self.speedtest_error = error_lines[0].replace('[error] Error: ', '').strip()
                        else:
                            self.speedtest_error = "Network error"
                        continue  # Try next command
                    else:
                        self.speedtest_error = error_msg or "Command failed"
                        
            except FileNotFoundError:
                continue  # Try next command
            except Exception as e:
                self.speedtest_error = str(e)
                continue  # Try next command
        
        # If we get here, all commands failed
        self.speedtest_status = "Failed"
        if not self.speedtest_error:
            self.speedtest_error = "Speedtest command not found or not working"
    
    def check_service_health(self, service_name: str) -> Dict:
        """Check individual service health"""
        service = self.services[service_name]
        try:
            response = requests.get(service["url"], timeout=5)
            if response.status_code == 200:
                return {
                    "status": "🟢 Healthy",
                    "response_time": f"{response.elapsed.total_seconds()*1000:.0f}ms",
                    "uptime": self.get_container_uptime(service["container"])
                }
        except requests.exceptions.RequestException:
            pass
        
        return {
            "status": "🔴 Down", 
            "response_time": "N/A",
            "uptime": "N/A"
        }
    
    def get_container_uptime(self, container_name: str) -> str:
        """Get Docker container uptime"""
        try:
            result = subprocess.run(
                ["docker", "inspect", container_name, "--format", "{{.State.StartedAt}}"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                start_time = datetime.fromisoformat(result.stdout.strip().replace('Z', '+00:00'))
                uptime = datetime.now().astimezone() - start_time.astimezone()
                
                days = uptime.days
                hours, remainder = divmod(uptime.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                if days > 0:
                    return f"{days}d {hours}h {minutes}m"
                elif hours > 0:
                    return f"{hours}h {minutes}m"
                else:
                    return f"{minutes}m"
        except:
            pass
        return "Unknown"
    
    def get_recent_logs(self, container_name: str, lines: int = 5) -> List[str]:
        """Get recent container logs"""
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(lines), container_name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logs = result.stdout.strip().split('\n')
                return [log for log in logs if log.strip()]
        except:
            pass
        return ["No logs available"]
    
    def get_docker_stats(self) -> Dict:
        """Get Docker container resource usage"""
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", 
                 "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                stats = {}
                for line in lines:
                    parts = line.split('\t')
                    if len(parts) >= 4:
                        container = parts[0]
                        if container in ["video-worker", "ytipfs-worker"]:
                            stats[container] = {
                                "cpu": parts[1],
                                "memory": parts[2].split(' / ')[0],
                                "network": parts[3]
                            }
                return stats
        except:
            pass
        return {}

def create_dashboard_layout() -> Layout:
    """Create the dashboard layout"""
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    
    layout["left"].split_column(
        Layout(name="internet", size=8),
        Layout(name="services", size=12)
    )
    
    layout["right"].split_column(
        Layout(name="video_worker_logs", size=10),
        Layout(name="ytipfs_logs", size=10)
    )
    
    return layout

def create_header_panel() -> Panel:
    """Create header panel"""
    title = Text("🛠️  SkatehiveOps Dashboard", style="bold magenta")
    subtitle = Text(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
    
    header_text = Align.center(title + "\n" + subtitle)
    return Panel(header_text, style="bright_blue")

def create_internet_panel(monitor: ServiceMonitor) -> Panel:
    """Create internet status panel"""
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    # Basic connectivity
    conn_status = monitor.check_internet_connection()
    table.add_row("Connection", conn_status["status"])
    table.add_row("Latency", conn_status["latency"])
    
    # Speed test status and results
    status = monitor.speedtest_status
    if status == "Complete" and monitor.last_speed_test:
        table.add_row("Download", f"{monitor.internet_speed['download']:.1f} Mbps")
        table.add_row("Upload", f"{monitor.internet_speed['upload']:.1f} Mbps")
        table.add_row("Ping", f"{monitor.internet_speed['ping']:.1f} ms")
        age = datetime.now() - monitor.last_speed_test
        table.add_row("Last Test", f"{int(age.total_seconds()//60)} min ago")
    elif status == "Running test...":
        table.add_row("Speed Test", "🔄 Running test...")
    elif status == "Failed":
        table.add_row("Speed Test", f"[red]Failed[/red]")
        if monitor.speedtest_error:
            # Truncate long error messages
            error_msg = monitor.speedtest_error[:50] + "..." if len(monitor.speedtest_error) > 50 else monitor.speedtest_error
            table.add_row("Error", f"[red]{error_msg}[/red]")
    else:
        table.add_row("Speed Test", "🔄 Initializing...")
    
    return Panel(table, title="🌐 Internet Status", border_style="blue")

def create_services_panel(monitor: ServiceMonitor) -> Panel:
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

def create_logs_panel(monitor: ServiceMonitor, container: str, title: str) -> Panel:
    """Create logs panel for a service"""
    logs = monitor.get_recent_logs(container, 8)
    
    log_text = Text()
    for i, log in enumerate(logs[-8:]):  # Show last 8 lines
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color code based on log content
        if "error" in log.lower() or "fail" in log.lower():
            style = "red"
        elif "warning" in log.lower() or "warn" in log.lower():
            style = "yellow"
        elif "success" in log.lower() or "complete" in log.lower():
            style = "green"
        else:
            style = "white"
        
        # Truncate long lines
        display_log = log[:80] + "..." if len(log) > 80 else log
        log_text.append(f"{timestamp} {display_log}\n", style=style)
    
    return Panel(log_text, title=title, border_style="yellow")

def create_footer_panel() -> Panel:
    """Create footer panel"""
    footer_text = Text("Press Ctrl+C to exit | Auto-refresh every 10s | Speed test every 10min", 
                      style="dim", justify="center")
    return Panel(footer_text, style="bright_black")

async def run_periodic_speed_test(monitor: ServiceMonitor):
    """Run speed test every 10 minutes asynchronously"""
    while True:
        await monitor.run_speed_test_async()
        await asyncio.sleep(600)  # 10 minutes

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
                layout["header"].update(create_header_panel())
                layout["internet"].update(create_internet_panel(monitor))
                layout["services"].update(create_services_panel(monitor))
                layout["video_worker_logs"].update(
                    create_logs_panel(monitor, "video-worker", "📹 Video Worker Logs")
                )
                layout["ytipfs_logs"].update(
                    create_logs_panel(monitor, "ytipfs-worker", "📦 YTIPFS Worker Logs")
                )
                layout["footer"].update(create_footer_panel())
                await asyncio.sleep(10)
    except KeyboardInterrupt:
        speed_test_task.cancel()
        initial_speedtest_task.cancel()
        console.print("\n[yellow]Dashboard stopped.[/yellow]")

if __name__ == "__main__":
    # Check for speedtest availability (but don't exit if not found, let runtime handle it)
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
        import rich
    
    asyncio.run(main())

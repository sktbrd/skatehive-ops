#!/usr/bin/env python3
"""
Service Monitor Module
Handles monitoring of services, internet connectivity, and Hive community stats
"""

import asyncio
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests


class ServiceMonitor:
    def __init__(self):
        self.services = {
            "video-worker": {
                "url": "http://localhost:8081/healthz",
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
        self.hive_stats = {}
        self.last_hive_stats_fetch = None
        self.hive_stats_error = None
        
    def check_internet_connection(self) -> Dict:
        """Check basic internet connectivity"""
        try:
            response = requests.get("https://8.8.8.8", timeout=5)
            return {"status": "🟢 Online", "latency": f"{response.elapsed.total_seconds()*1000:.0f}ms"}
        except:
            return {"status": "🔴 Offline", "latency": "N/A"}
    
    def fetch_hive_stats(self) -> Dict:
        """Fetch Hive community stats from API"""
        # Use urllib (built into Python) instead of requests
        try:
            import urllib.request
            import json
            
            with urllib.request.urlopen("https://stats.hivehub.dev/communities?c=hive-173115", timeout=10) as response:
                raw_data = response.read().decode()
                data = json.loads(raw_data)
                
                # Debug: Let's see what we actually get
                if isinstance(data, dict):
                    # Check if it's the expected format or if it's nested
                    if 'total_subscribers' in data:
                        self.hive_stats = data
                        self.last_hive_stats_fetch = datetime.now()
                        self.hive_stats_error = None
                        return data
                    elif isinstance(data, dict) and len(data) > 0:
                        # Maybe the data is nested? Let's try to find the actual stats
                        for key, value in data.items():
                            if isinstance(value, dict) and 'total_subscribers' in value:
                                self.hive_stats = value
                                self.last_hive_stats_fetch = datetime.now()
                                self.hive_stats_error = None
                                return value
                        # If we get here, log what keys we found
                        keys = list(data.keys())[:3]  # First 3 keys
                        self.hive_stats_error = f"No total_subscribers. Keys: {keys}"
                    else:
                        self.hive_stats_error = f"Empty dict response"
                elif isinstance(data, list) and len(data) > 0:
                    # Maybe it's a list with the stats inside?
                    first_item = data[0]
                    if isinstance(first_item, dict) and 'total_subscribers' in first_item:
                        self.hive_stats = first_item
                        self.last_hive_stats_fetch = datetime.now()
                        self.hive_stats_error = None
                        return first_item
                    else:
                        self.hive_stats_error = f"List but no stats in first item"
                else:
                    self.hive_stats_error = f"Response type: {type(data)}"
                    
        except json.JSONDecodeError as e:
            self.hive_stats_error = f"JSON error: {str(e)[:20]}"
        except Exception as e:
            self.hive_stats_error = f"urllib: {str(e)[:25]}"
        return {}
    
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
        commands_to_try = [
            ["docker", "inspect", container_name, "--format", "{{.State.StartedAt}}"],
            ["sudo", "docker", "inspect", container_name, "--format", "{{.State.StartedAt}}"]
        ]
        
        for cmd in commands_to_try:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
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
                elif "permission denied" in result.stderr.lower() and cmd[0] != "sudo":
                    continue  # Try with sudo
            except Exception:
                continue  # Try next command
        return "Unknown"
    
    def get_recent_logs(self, container_name: str, lines: int = 5) -> List[str]:
        """Get recent container logs"""
        # Try without sudo first, then with sudo if permission denied
        commands_to_try = [
            ["docker", "logs", "--tail", str(lines), container_name],
            ["sudo", "docker", "logs", "--tail", str(lines), container_name]
        ]
        
        for cmd in commands_to_try:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    logs = result.stdout.strip().split('\n')
                    # Also check stderr for logs
                    if result.stderr.strip():
                        stderr_logs = result.stderr.strip().split('\n')
                        logs.extend(stderr_logs)
                    
                    valid_logs = [log for log in logs if log.strip()]
                    if valid_logs:
                        return valid_logs
                    else:
                        return [f"Container '{container_name}' has no recent logs"]
                elif "permission denied" in result.stderr.lower() and cmd[0] != "sudo":
                    continue  # Try with sudo
                else:
                    return [f"Error getting logs (code {result.returncode}): {result.stderr.strip()}"]
            except subprocess.TimeoutExpired:
                return [f"Timeout getting logs for {container_name}"]
            except Exception as e:
                if "permission denied" in str(e).lower() and cmd[0] != "sudo":
                    continue  # Try with sudo
                return [f"Error: {str(e)}"]
        
        return ["No logs available"]
    
    def get_docker_stats(self) -> Dict:
        """Get Docker container resource usage"""
        commands_to_try = [
            ["docker", "stats", "--no-stream", "--format", 
             "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"],
            ["sudo", "docker", "stats", "--no-stream", "--format", 
             "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"]
        ]
        
        for cmd in commands_to_try:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # Skip header
                    stats = {}
                    for line in lines:
                        parts = line.split('\t')
                        if len(parts) >= 4:
                            container = parts[0]
                            if container in ["video-worker", "ytipfs-worker"]:
                                # Parse memory usage, handle cases where limit might be 0B
                                mem_usage = parts[2]
                                if " / " in mem_usage:
                                    actual_mem = mem_usage.split(' / ')[0]
                                    if actual_mem == "0B":
                                        # Try to get memory from a different method
                                        actual_mem = self._get_container_memory_usage(container)
                                else:
                                    actual_mem = mem_usage
                                
                                stats[container] = {
                                    "cpu": parts[1],
                                    "memory": actual_mem,
                                    "network": parts[3]
                                }
                    return stats
                elif "permission denied" in result.stderr.lower() and cmd[0] != "sudo":
                    continue  # Try with sudo
            except subprocess.TimeoutExpired:
                continue  # Try next command
            except Exception:
                continue  # Try next command
        return {}

    def _get_container_memory_usage(self, container_name: str) -> str:
        """Get memory usage directly from container inspect when stats shows 0B"""
        try:
            cmd = ["docker", "exec", container_name, "cat", "/proc/meminfo"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('MemAvailable:'):
                        # This is a rough estimate - in a real scenario you'd want more precise calculation
                        mem_kb = int(line.split()[1])
                        if mem_kb > 1024 * 1024:  # > 1GB
                            return f"{mem_kb // (1024 * 1024)}GB"
                        elif mem_kb > 1024:  # > 1MB
                            return f"{mem_kb // 1024}MB"
                        else:
                            return f"{mem_kb}KB"
        except:
            pass
        
        # Fallback: try docker inspect for memory usage
        try:
            cmd = ["docker", "inspect", container_name, "--format", "{{.HostConfig.Memory}}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip() != "0":
                memory_bytes = int(result.stdout.strip())
                if memory_bytes > 1024 * 1024 * 1024:  # > 1GB
                    return f"{memory_bytes // (1024 * 1024 * 1024)}GB"
                elif memory_bytes > 1024 * 1024:  # > 1MB
                    return f"{memory_bytes // (1024 * 1024)}MB"
                else:
                    return f"{memory_bytes // 1024}KB"
        except:
            pass
            
        return "N/A"

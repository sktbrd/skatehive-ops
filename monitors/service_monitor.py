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

# Import configuration
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    TAILSCALE_HOSTNAME,
    VIDEO_TRANSCODER_PORT,
    INSTAGRAM_DOWNLOADER_PORT,
    VIDEO_FUNNEL_PATH,
    INSTAGRAM_FUNNEL_PATH,
    SKATEHIVE_NODES,
    get_external_url,
)


class ServiceMonitor:
    def __init__(self):
        # Build URLs from configuration
        self.base_url = f"https://{TAILSCALE_HOSTNAME}" if TAILSCALE_HOSTNAME else ""
        
        # Build services dict dynamically from config
        self.services = {}
        
        # Local services
        if TAILSCALE_HOSTNAME:
            self.services["ytipfs-worker"] = {
                "url": f"{self.base_url}{INSTAGRAM_FUNNEL_PATH}/health",
                "port": INSTAGRAM_DOWNLOADER_PORT,
                "container": "ytipfs-worker",
                "check_type": "json_key",
                "expected_key": "status",
                "expected_value": "ok"
            }
            self.services["video-worker"] = {
                "url": f"{self.base_url}{VIDEO_FUNNEL_PATH}/healthz",
                "port": VIDEO_TRANSCODER_PORT,
                "container": "video-worker",
                "check_type": "json_key",
                "expected_key": "ok",
                "expected_value": True
            }
        
        # Add other known nodes
        for node_id, node_info in SKATEHIVE_NODES.items():
            hostname = node_info['hostname']
            if hostname and hostname != TAILSCALE_HOSTNAME:
                self.services[f"{node_id}-video"] = {
                    "url": f"https://{hostname}{VIDEO_FUNNEL_PATH}/healthz",
                    "port": 443,
                    "container": f"{node_id}-video-worker",
                    "check_type": "json_key",
                    "expected_key": "ok",
                    "expected_value": True,
                    "remote": True,  # Mark as remote node
                    "node_name": node_info.get('name', node_id),
                }
                self.services[f"{node_id}-instagram"] = {
                    "url": f"https://{hostname}{INSTAGRAM_FUNNEL_PATH}/health",
                    "port": 443,
                    "container": f"{node_id}-ytipfs-worker",
                    "check_type": "json_key",
                    "expected_key": "status",
                    "expected_value": "ok",
                    "remote": True,  # Mark as remote node
                    "node_name": node_info.get('name', node_id),
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
        """Check individual service health with different validation methods"""
        service = self.services[service_name]
        try:
            response = requests.get(service["url"], timeout=10)
            response_time = f"{response.elapsed.total_seconds()*1000:.0f}ms"
            
            # Handle different check types
            check_type = service.get("check_type", "http_status")
            
            if check_type == "http_status":
                # Just check HTTP status code
                expected_status = service.get("expected_status", 200)
                if response.status_code == expected_status:
                    return {
                        "status": "🟢 Healthy",
                        "response_time": response_time,
                        "uptime": self.get_container_uptime(service["container"]),
                        "details": f"HTTP {response.status_code}"
                    }
                else:
                    return {
                        "status": "🔴 Down",
                        "response_time": response_time,
                        "uptime": "N/A",
                        "details": f"HTTP {response.status_code} (expected {expected_status})"
                    }
                    
            elif check_type == "json_key":
                # Check for specific key-value in JSON response
                if response.status_code == 200:
                    try:
                        data = response.json()
                        expected_key = service.get("expected_key")
                        expected_value = service.get("expected_value")
                        
                        if expected_key in data and data[expected_key] == expected_value:
                            return {
                                "status": "🟢 Healthy",
                                "response_time": response_time,
                                "uptime": self.get_container_uptime(service["container"]),
                                "details": f"JSON OK: {expected_key}={data[expected_key]}"
                            }
                        else:
                            actual_value = data.get(expected_key, "missing")
                            return {
                                "status": "🔴 Down",
                                "response_time": response_time,
                                "uptime": "N/A",
                                "details": f"JSON fail: {expected_key}={actual_value} (expected {expected_value})"
                            }
                    except ValueError:
                        return {
                            "status": "🔴 Down",
                            "response_time": response_time,
                            "uptime": "N/A",
                            "details": "Invalid JSON response"
                        }
                else:
                    return {
                        "status": "🔴 Down",
                        "response_time": response_time,
                        "uptime": "N/A",
                        "details": f"HTTP {response.status_code}"
                    }
                    
            elif check_type == "tailscale_device":
                # Check Tailscale device status first, then service health
                tailscale_name = service.get("tailscale_name")
                device_status = self.check_tailscale_device(tailscale_name)
                
                if not device_status["online"]:
                    return {
                        "status": "🔴 Offline",
                        "response_time": "N/A",
                        "uptime": "N/A", 
                        "details": f"Tailscale device offline: {device_status['status']}"
                    }
                
                # Device is online, now check service health
                if response.status_code == 200:
                    try:
                        # Try to parse as JSON for health check
                        data = response.json()
                        return {
                            "status": "🟢 Online + Service Healthy",
                            "response_time": response_time,
                            "uptime": device_status.get("uptime", "Unknown"),
                            "details": f"Device online, service responding"
                        }
                    except ValueError:
                        # Not JSON, but HTTP 200 is still good
                        return {
                            "status": "🟡 Online + Service Limited", 
                            "response_time": response_time,
                            "uptime": device_status.get("uptime", "Unknown"),
                            "details": f"Device online, HTTP {response.status_code}"
                        }
                else:
                    return {
                        "status": "🟡 Online + Service Down",
                        "response_time": response_time,
                        "uptime": device_status.get("uptime", "Unknown"), 
                        "details": f"Device online, HTTP {response.status_code}"
                    }
                    
        except requests.exceptions.RequestException as e:
            # For Tailscale devices, check device status even if service is unreachable
            if service.get("check_type") == "tailscale_device":
                tailscale_name = service.get("tailscale_name")
                device_status = self.check_tailscale_device(tailscale_name)
                
                if device_status["online"]:
                    error_msg = str(e)
                    if "timeout" in error_msg.lower():
                        details = "Device online, service timeout"
                    elif "connection" in error_msg.lower():
                        details = "Device online, service unreachable"
                    else:
                        details = f"Device online, service error: {error_msg[:30]}"
                    
                    return {
                        "status": "🟡 Online + Service Down",
                        "response_time": "N/A",
                        "uptime": device_status.get("uptime", "Unknown"),
                        "details": details
                    }
                else:
                    return {
                        "status": "🔴 Offline",
                        "response_time": "N/A",
                        "uptime": "N/A",
                        "details": f"Tailscale device offline: {device_status['status']}"
                    }
            
            # Standard error handling for other services
            error_msg = str(e)
            is_remote = service.get("remote", False)
            node_name = service.get("node_name", "Unknown")
            
            if "SSL" in error_msg or "ssl" in error_msg:
                details = f"Funnel down ({node_name})" if is_remote else "SSL error"
            elif "timeout" in error_msg.lower():
                details = f"Funnel timeout ({node_name})" if is_remote else "Connection timeout"
            elif "connection" in error_msg.lower():
                details = f"Funnel offline ({node_name})" if is_remote else "Connection refused"
            else:
                details = f"Unreachable ({node_name})" if is_remote else f"Network error: {error_msg[:30]}"
                
            return {
                "status": "🔴 Down", 
                "response_time": "N/A",
                "uptime": "N/A",
                "details": details
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
    
    def check_tailscale_device(self, device_name: str) -> Dict:
        """Check if a Tailscale device is online and get its status"""
        try:
            result = subprocess.run(
                ["tailscale", "status", "--json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    "online": False,
                    "status": "tailscale command failed",
                    "uptime": "N/A"
                }
            
            # Parse Tailscale JSON status
            import json
            tailscale_data = json.loads(result.stdout)
            
            # Look for the device in the peer list
            for peer_id, peer_info in tailscale_data.get("Peer", {}).items():
                if peer_info.get("HostName") == device_name:
                    online = peer_info.get("Online", False)
                    last_seen = peer_info.get("LastSeen")
                    
                    if online:
                        return {
                            "online": True,
                            "status": "active",
                            "uptime": "Active",
                            "last_seen": last_seen
                        }
                    else:
                        return {
                            "online": False,
                            "status": "offline",
                            "uptime": "N/A",
                            "last_seen": last_seen
                        }
            
            # Device not found in peer list
            return {
                "online": False,
                "status": "device not found in tailscale network",
                "uptime": "N/A"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "online": False,
                "status": "tailscale status timeout",
                "uptime": "N/A"
            }
        except Exception as e:
            return {
                "online": False,
                "status": f"error checking tailscale: {str(e)[:50]}",
                "uptime": "N/A"
            }
    
    def get_docker_stats(self) -> Dict:
        """Get Docker container resource usage"""
        stats = {}
        
        # Get CPU stats from docker stats
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
                    for line in lines:
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            container = parts[0]
                            if container in ["video-worker", "ytipfs-worker"]:
                                # Get CPU percentage
                                cpu_percent = parts[1]
                                
                                # Get memory usage - if it's 0B / 0B, get actual usage
                                mem_usage = parts[2]
                                if mem_usage == "0B / 0B" or "0B" in mem_usage:
                                    mem_usage = self._get_container_memory_usage(container)
                                else:
                                    mem_usage = mem_usage.split(' / ')[0]  # Just the used part
                                
                                stats[container] = {
                                    "cpu": cpu_percent,
                                    "memory": mem_usage,
                                    "network": parts[3] if len(parts) > 3 else "N/A"
                                }
                    break  # Success, don't try with sudo
                elif "permission denied" in result.stderr.lower() and cmd[0] != "sudo":
                    continue  # Try with sudo
            except subprocess.TimeoutExpired:
                continue  # Try next command
            except Exception:
                continue  # Try next command
        
        return stats

    def _get_container_memory_usage(self, container_name: str) -> str:
        """Get actual memory usage from container when Docker stats shows 0B"""
        try:
            # Get the main process ID of the container
            cmd = ["docker", "inspect", container_name, "--format", "{{.State.Pid}}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip().isdigit():
                pid = result.stdout.strip()
                
                # Get memory usage from /proc/PID/status
                try:
                    with open(f"/proc/{pid}/status", "r") as f:
                        for line in f:
                            if line.startswith("VmRSS:"):  # Resident Set Size (actual memory usage)
                                mem_kb = int(line.split()[1])
                                return self._format_bytes(mem_kb * 1024)  # Convert KB to bytes
                except:
                    pass
                
                # Alternative: use /proc/PID/statm
                try:
                    with open(f"/proc/{pid}/statm", "r") as f:
                        # statm format: size resident shared text lib data dt
                        statm = f.read().split()
                        if len(statm) >= 2:
                            resident_pages = int(statm[1])
                            page_size = 4096  # Standard page size
                            memory_bytes = resident_pages * page_size
                            return self._format_bytes(memory_bytes)
                except:
                    pass
        except:
            pass
            
        return "N/A"
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes into human readable format"""
        if bytes_value >= 1024 * 1024 * 1024:  # GB
            return f"{bytes_value / (1024 * 1024 * 1024):.1f}GB"
        elif bytes_value >= 1024 * 1024:  # MB
            return f"{bytes_value / (1024 * 1024):.1f}MB"
        elif bytes_value >= 1024:  # KB
            return f"{bytes_value / 1024:.1f}KB"
        else:
            return f"{bytes_value}B"

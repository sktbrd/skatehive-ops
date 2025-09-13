#!/usr/bin/env python3
"""
Unified Video Activity Monitor
Aggregates video transcoding logs from all services: Mac Mini, Raspberry Pi, and Render
"""

import requests
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import json


class UnifiedVideoActivityMonitor:
    def __init__(self):
        self.video_services = {
            "mac_mini": {
                "name": "Mac Mini M4",
                "endpoint": "https://minivlad.tail9656d3.ts.net/video/logs",
                "health_endpoint": "https://minivlad.tail9656d3.ts.net/video/healthz",
                "icon": "🖥️",
                "color": "blue"
            },
            "raspberry_pi": {
                "name": "Raspberry Pi",
                "endpoint": "https://raspberrypi.tail83ea3e.ts.net/video/logs",
                "health_endpoint": "https://raspberrypi.tail83ea3e.ts.net/video/healthz",
                "icon": "🥧",
                "color": "green"
            },
            "render_cloud": {
                "name": "Render Cloud",
                "endpoint": "https://skatehive-transcoder.onrender.com/logs",
                "health_endpoint": "https://skatehive-transcoder.onrender.com/health",
                "icon": "☁️",
                "color": "purple"
            }
        }
        self.unified_logs = []
        self.service_status = {}
        self.last_update = None
        
    async def fetch_service_logs(self, service_key: str, service_config: Dict) -> List[Dict]:
        """Fetch logs from a specific video service"""
        try:
            response = requests.get(
                service_config["endpoint"], 
                timeout=8,
                params={"limit": 10}  # Get last 10 operations
            )
            
            if response.status_code == 200:
                data = response.json()
                logs = data.get('logs', []) if isinstance(data, dict) else data
                
                # Add service metadata to each log entry
                enriched_logs = []
                for log in logs:
                    if isinstance(log, dict):
                        enriched_log = log.copy()
                        enriched_log['service'] = service_key
                        enriched_log['service_name'] = service_config['name']
                        enriched_log['service_icon'] = service_config['icon']
                        enriched_log['service_color'] = service_config['color']
                        enriched_logs.append(enriched_log)
                
                self.service_status[service_key] = {
                    "status": "online",
                    "last_seen": datetime.now().isoformat(),
                    "log_count": len(enriched_logs)
                }
                
                return enriched_logs
                
        except requests.exceptions.ConnectTimeout:
            self.service_status[service_key] = {
                "status": "timeout",
                "error": "Connection timeout",
                "last_seen": None
            }
        except requests.exceptions.ConnectionError:
            self.service_status[service_key] = {
                "status": "offline", 
                "error": "Connection refused",
                "last_seen": None
            }
        except Exception as e:
            self.service_status[service_key] = {
                "status": "error",
                "error": str(e)[:100],
                "last_seen": None
            }
            
        return []
    
    async def update_unified_logs(self) -> Dict:
        """Fetch and merge logs from all video services"""
        all_logs = []
        
        # Fetch logs from all services concurrently
        tasks = []
        for service_key, service_config in self.video_services.items():
            task = self.fetch_service_logs(service_key, service_config)
            tasks.append(task)
        
        # Wait for all services to respond (or timeout)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all logs
        for result in results:
            if isinstance(result, list):
                all_logs.extend(result)
        
        # Sort by timestamp (newest first) with detailed error handling
        def safe_timestamp_sort(log):
            timestamp = log.get('timestamp', '')
            if not timestamp:
                return '1970-01-01T00:00:00Z'  # Default very old timestamp
            if not isinstance(timestamp, str):
                # Convert non-string timestamps to string
                return str(timestamp)
            return timestamp
        
        try:
            all_logs.sort(key=safe_timestamp_sort, reverse=True)
        except Exception as e:
            # If sorting still fails, log the error and use unsorted logs
            print(f"Warning: Failed to sort logs: {e}")
            # Try to identify problematic log entries
            for i, log in enumerate(all_logs):
                ts = log.get('timestamp', 'MISSING')
                print(f"Log {i}: timestamp={ts}, type={type(ts)}")
            # Continue with unsorted logs
        
        # Keep last 20 operations across all services
        self.unified_logs = all_logs[:20]
        self.last_update = datetime.now()
        
        return {
            "logs": self.unified_logs,
            "service_status": self.service_status,
            "last_update": self.last_update.isoformat(),
            "total_services": len(self.video_services),
            "online_services": len([s for s in self.service_status.values() if s.get("status") == "online"])
        }
    
    def get_unified_activity(self) -> Dict:
        """Get the current unified activity data"""
        return {
            "logs": self.unified_logs,
            "service_status": self.service_status,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "summary": self.get_activity_summary()
        }
    
    def get_activity_summary(self) -> Dict:
        """Generate summary statistics from unified logs"""
        if not self.unified_logs:
            return {
                "total_operations": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0,
                "services_active": 0
            }
        
        # Count operations by status
        successful = len([log for log in self.unified_logs if log.get('status') == 'completed'])
        failed = len([log for log in self.unified_logs if log.get('status') == 'failed'])
        total = len(self.unified_logs)
        
        # Count active services (services that have recent logs)
        active_services = len(set(log.get('service') for log in self.unified_logs if log.get('service')))
        
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            "total_operations": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round(success_rate, 1),
            "services_active": active_services
        }


# Global instance for dashboard use
unified_video_monitor = UnifiedVideoActivityMonitor()


async def get_unified_video_activity():
    """Main function to get unified video activity - for use in dashboard"""
    return await unified_video_monitor.update_unified_logs()


def get_cached_video_activity():
    """Get cached video activity without refreshing - for quick dashboard updates"""
    return unified_video_monitor.get_unified_activity()
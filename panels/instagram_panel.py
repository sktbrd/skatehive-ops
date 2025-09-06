#!/usr/bin/env python3
"""
Instagram Download Monitor Panel
Displays Instagram service health, cookie status, and recent downloads
"""

import json
import requests
from datetime import datetime
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box


def create_instagram_panel(monitor):
    """Create Instagram monitoring panel"""
    
    # Create main table
    table = Table(box=box.ROUNDED, expand=True)
    table.add_column("Metric", style="cyan", width=20)
    table.add_column("Status", style="green", width=15)
    table.add_column("Details", style="white")
    
    try:
        # Check Instagram service health
        local_health = check_service_health("http://localhost:8000")
        tailscale_health = check_service_health("http://raspberrypi.tail83ea3e.ts.net:8000")
        render_health = check_service_health("https://skate-insta.onrender.com")
        
        # Service Status
        table.add_row(
            "🐳 Local Service",
            "🟢 UP" if local_health['status'] else "🔴 DOWN",
            f"localhost:8000 - {local_health.get('version', 'Unknown')}"
        )
        
        table.add_row(
            "🌐 Tailscale Service", 
            "🟢 UP" if tailscale_health['status'] else "🔴 DOWN",
            f"raspberrypi.tail83ea3e.ts.net:8000"
        )
        
        table.add_row(
            "☁️  Render Service",
            "🟢 UP" if render_health['status'] else "🔴 DOWN", 
            f"skate-insta.onrender.com"
        )
        
        table.add_row("", "", "")  # Separator
        
        # Cookie Health (from local service)
        if local_health['status'] and 'authentication' in local_health.get('data', {}):
            auth = local_health['data']['authentication']
            cookies_valid = auth.get('cookies_valid', False)
            cookies_exist = auth.get('cookies_exist', False)
            last_validation = auth.get('last_validation', 'Never')
            
            cookie_status = "🟢 VALID" if cookies_valid else "🟡 INVALID" if cookies_exist else "🔴 MISSING"
            
            table.add_row(
                "🍪 Cookie Status",
                cookie_status,
                f"Last validation: {format_timestamp(last_validation)}"
            )
            
            # Cookie expiry check
            cookie_health = check_cookie_expiry()
            if cookie_health:
                table.add_row(
                    "⏰ Cookie Expiry",
                    cookie_health['status'],
                    cookie_health['details']
                )
        else:
            table.add_row(
                "🍪 Cookie Status", 
                "🔴 UNKNOWN",
                "Cannot connect to service"
            )
            
        table.add_row("", "", "")  # Separator
        
        # Recent Downloads
        recent_downloads = get_recent_downloads()
        if recent_downloads:
            table.add_row(
                "📥 Latest Download",
                "🟢 SUCCESS", 
                f"{recent_downloads[0]['filename']} ({recent_downloads[0]['size']})"
            )
            table.add_row(
                "📅 Download Time",
                "",
                recent_downloads[0]['timestamp']
            )
            table.add_row(
                "🔗 IPFS Gateway", 
                "",
                recent_downloads[0]['gateway'][:60] + "..." if len(recent_downloads[0]['gateway']) > 60 else recent_downloads[0]['gateway']
            )
        else:
            table.add_row(
                "📥 Recent Downloads",
                "🔴 NONE",
                "No recent downloads found"
            )
            
    except Exception as e:
        table.add_row("❌ Error", "🔴 FAILED", f"Monitor error: {str(e)}")
    
    return Panel(
        table,
        title="📱 Instagram Download Service",
        border_style="blue",
        expand=True
    )


def check_service_health(url):
    """Check health of an Instagram service"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            return {
                'status': True,
                'data': response.json()
            }
        else:
            return {'status': False, 'error': f"HTTP {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {'status': False, 'error': str(e)}


def check_cookie_expiry():
    """Check Instagram cookie expiry status"""
    try:
        response = requests.get("http://localhost:8000/cookies/status", timeout=3)
        if response.status_code == 200:
            data = response.json()
            
            # Simple cookie health logic
            if data.get('cookies_valid'):
                return {
                    'status': '🟢 GOOD',
                    'details': 'Cookies are valid and working'
                }
            elif data.get('cookies_exist'):
                return {
                    'status': '🟡 EXPIRED',
                    'details': 'Cookies exist but need refresh'
                }
            else:
                return {
                    'status': '🔴 MISSING',
                    'details': 'No cookies found - add to .env'
                }
        else:
            return {
                'status': '🔴 ERROR',
                'details': f"Cannot check cookies (HTTP {response.status_code})"
            }
    except Exception as e:
        return {
            'status': '🔴 ERROR',
            'details': f"Cookie check failed: {str(e)}"
        }


def get_recent_downloads():
    """Get recent Instagram downloads from Docker logs"""
    try:
        # Get recent logs from ytipfs-worker container
        result = subprocess.run(
            ['docker', 'logs', '--tail', '50', 'ytipfs-worker'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        downloads = []
        lines = result.stdout.split('\n')
        
        for line in lines:
            if 'Final file for IPFS upload:' in line and '.mp4' in line:
                try:
                    # Extract filename from log line
                    filename = line.split('Final file for IPFS upload: /data/')[-1].strip()
                    
                    # Get timestamp from log line
                    timestamp_part = line.split(' INFO ')[0]
                    
                    # Mock data for demo - in real implementation, you'd parse more log data
                    downloads.append({
                        'filename': filename,
                        'timestamp': timestamp_part,
                        'size': 'Unknown',  # Would need to parse from other logs
                        'gateway': 'https://ipfs.skatehive.app/ipfs/...'  # Would need CID from logs
                    })
                except Exception:
                    continue
                    
        return downloads[:3]  # Return last 3 downloads
        
    except Exception:
        return []


def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    if not timestamp_str or timestamp_str == 'Never':
        return 'Never'
    
    try:
        # Parse ISO timestamp
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return str(timestamp_str)[:19]  # Truncate if parsing fails

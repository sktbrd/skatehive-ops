#!/usr/bin/env python3
"""
Instagram Download Monitor Panel
Displays Instagram service health, cookie status, and recent downloads
"""

import json
import requests
import subprocess
import asyncio
from datetime import datetime
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.align import Align


def get_instagram_logs():
    """Fetch Instagram download logs from the service"""
    try:
        response = requests.get("https://raspberrypi.tail83ea3e.ts.net/instagram/logs", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {"logs": [], "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"logs": [], "error": str(e)}


def create_instagram_panel(monitor):
    """Create Instagram monitoring panel"""
    
    # Create main table
    table = Table(box=box.ROUNDED, expand=True)
    table.add_column("Metric", style="cyan", width=20)
    table.add_column("Status", style="green", width=15)
    table.add_column("Details", style="white")
    
    try:
        # Check Instagram service health
        tailscale_health = check_service_health("https://raspberrypi.tail83ea3e.ts.net/instagram")
        render_health = check_service_health("https://skate-insta.onrender.com")
        
        # Service Status
        table.add_row(
            "🌐 Primary Service",
            "🟢 UP" if tailscale_health['status'] else "🔴 DOWN",
            f"raspberrypi.tail83ea3e.ts.net - {tailscale_health.get('version', 'Unknown')}"
        )
        
        table.add_row(
            "🌐 Tailscale Service", 
            "🟢 UP" if tailscale_health['status'] else "🔴 DOWN",
            f"Primary endpoint via Tailscale Funnel"
        )
        
        table.add_row(
            "☁️  Render Service",
            "🟢 UP" if render_health['status'] else "🔴 DOWN", 
            f"skate-insta.onrender.com"
        )
        
        table.add_row("", "", "")  # Separator
        
        # Cookie Health (from primary service)
        if tailscale_health['status'] and 'authentication' in tailscale_health.get('data', {}):
            auth = tailscale_health['data']['authentication']
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
        response = requests.get("https://raspberrypi.tail83ea3e.ts.net/instagram/cookies/status", timeout=10)
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


def create_instagram_logs_panel(monitor):
    """Create Instagram download logs panel (similar to video transcoder)"""
    try:
        # Get Instagram logs
        response = requests.get("https://raspberrypi.tail83ea3e.ts.net/instagram/logs", timeout=10)
        if response.status_code != 200:
            return Panel(
                Align.center("❌ Could not fetch Instagram logs"),
                title="📱 Instagram Download Logs",
                border_style="red"
            )
        
        logs_data = response.json()
        logs = logs_data.get("logs", [])
        
        # Filter out processing entries, only show completed/failed
        completed_logs = [log for log in logs if log.get('status') in ['completed', 'failed']]
        
        if not completed_logs:
            return Panel(
                Align.center("No Instagram downloads yet"),
                title="📱 Instagram Download Logs",
                border_style="blue"
            )
        
        # Create content similar to video transcoder logs
        content = []
        
        for log in completed_logs[:10]:  # Show last 10 downloads
            try:
                timestamp = log.get('timestamp', '')
                status = log.get('status', 'unknown')
                success = log.get('success', False)
                url = log.get('url', '')
                filename = log.get('filename', 'N/A')
                duration = log.get('duration', 0)
                
                # Format timestamp
                if timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                else:
                    time_str = "Unknown"
                
                # Format URL (extract Instagram post ID)
                if 'instagram.com/p/' in url:
                    post_id = url.split('/p/')[-1].split('/')[0]
                    url_display = f"instagram.com/p/{post_id}"
                else:
                    url_display = url[:40] + "..." if len(url) > 40 else url
                
                # Format filename
                if len(filename) > 30:
                    filename_display = filename[:27] + "..."
                else:
                    filename_display = filename
                
                # Format duration
                duration_str = f"{duration/1000:.1f}s" if duration else "N/A"
                
                # Status icon and error handling
                if status == "completed" and success:
                    status_icon = "✅"
                    log_line = f"{status_icon} {time_str} {url_display} - {filename_display} {duration_str}"
                elif status == "failed" or not success:
                    status_icon = "❌"
                    # Get error details and categorize them
                    error = log.get('error', log.get('message', 'Unknown error'))
                    
                    # Categorize common errors
                    if 'private' in error.lower():
                        error_short = "Private account"
                    elif 'not found' in error.lower() or '404' in error:
                        error_short = "Post not found"
                    elif 'timeout' in error.lower():
                        error_short = "Connection timeout"
                    elif 'rate limit' in error.lower() or 'too many' in error.lower():
                        error_short = "Rate limited"
                    elif 'cookie' in error.lower() or 'auth' in error.lower():
                        error_short = "Authentication issue"
                    elif 'network' in error.lower() or 'connection' in error.lower():
                        error_short = "Network error"
                    elif len(error) > 40:
                        error_short = error[:37] + "..."
                    else:
                        error_short = error
                    
                    log_line = f"{status_icon} {time_str} {url_display} - [red]ERROR:[/red] {error_short}"
                else:
                    status_icon = "⚠️"
                    log_line = f"{status_icon} {time_str} {url_display} - {filename_display} {duration_str}"
                
                content.append(log_line)
                
            except Exception as e:
                content.append(f"❌ Error parsing log entry: {str(e)}")
        
        # Add stats
        total = len(completed_logs)
        success_count = len([l for l in completed_logs if l.get('success', False)])
        failure_count = total - success_count
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        stats_line = f"\n📊 Total: {total} | Success: {success_count} | Failed: {failure_count} | Rate: {success_rate:.1f}%"
        content.append(stats_line)
        
        return Panel(
            "\n".join(content),
            title="📱 Instagram Download Logs",
            border_style="blue"
        )
        
    except Exception as e:
        return Panel(
            Align.center(f"❌ Error: {str(e)}"),
            title="📱 Instagram Download Logs",
            border_style="red"
        )

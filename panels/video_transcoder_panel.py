#!/usr/bin/env python3
"""
Video Transcoder Panel
Displays the latest transcoding operations from the video-worker service
"""

import requests
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from datetime import datetime
import json


def parse_device_display(platform, device_info):
    """Parse device info into a concise display format"""
    
    # Handle the current format from frontend: "web/MacIntel/desktop"
    if device_info and '/' in device_info:
        parts = device_info.split('/')
        
        if len(parts) >= 3:
            platform_part = parts[0]  # web
            os_part = parts[1]        # MacIntel, iPhone, etc.
            device_part = parts[2]    # desktop, mobile, etc.
            
            # Detect device type and OS
            if 'iphone' in os_part.lower() or 'ios' in device_info.lower():
                return "📱 iPhone"
            elif 'android' in device_info.lower():
                return "📱 Android"
            elif 'ipad' in os_part.lower():
                return "📟 iPad"
            elif 'mac' in os_part.lower():
                # Try to detect browser from additional info if available
                return "💻 Mac"
            elif 'win' in os_part.lower() or 'windows' in device_info.lower():
                return "💻 Win"
            elif 'linux' in device_info.lower():
                return "💻 Linux"
            else:
                # Fallback to platform detection
                if platform == 'mobile' or device_part == 'mobile':
                    return "📱 Mobile"
                elif platform == 'tablet' or device_part == 'tablet':
                    return "📟 Tablet"
                else:
                    return "💻 Desktop"
    
    # Fallback for older format or unknown
    if platform == 'mobile':
        return "📱 Mobile"
    elif platform == 'tablet':
        return "📟 Tablet"
    elif platform == 'web' or platform == 'desktop':
        return "💻 Web"
    else:
        return "❓ Unknown"


def create_video_transcoder_panel(monitor, title: str = "📹 Video Transcoder") -> Panel:
    """Create video transcoder panel showing latest transcode operations"""
    
    try:
        import requests
        
        # Fetch logs from video-worker service
        response = requests.get('http://localhost:8081/logs?limit=5', timeout=3)
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            stats = data.get('stats', {})
            
            # Filter to show only completed operations
            completed_logs = []
            for log in logs:
                if log.get('action') == 'transcode_complete' or log.get('status') == 'completed':
                    completed_logs.append(log)
                elif log.get('action') == 'transcode_start' and log.get('status') == 'error':
                    # Include failed operations
                    completed_logs.append(log)
            
            # Sort by timestamp descending and take last 5 completed operations
            completed_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            recent_logs = completed_logs[:5]
            
            if not recent_logs:
                content = "[dim]No transcoding operations completed yet[/dim]"
            else:
                lines = []
                for log in recent_logs:
                    # Get user info with HP
                    user = log.get('creator', 'unknown')
                    hp = log.get('userHP', 'unknown')
                    
                    # Parse device info
                    platform = log.get('platform', 'unknown')
                    device_info = log.get('deviceInfo', '')
                    device_display = parse_device_display(platform, device_info)
                    
                    # Get status and timing
                    status = log.get('status', 'unknown')
                    timestamp = log.get('timestamp', '')
                    time_str = ''
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = dt.strftime('%H:%M:%S')
                        except:
                            time_str = timestamp[-8:] if len(timestamp) >= 8 else timestamp
                    
                    # Get processing details
                    if status == 'completed':
                        duration = log.get('processingTime', 'unknown')
                        output_size = log.get('outputSize', 'unknown')
                        status_icon = "✅"
                        details = f"({duration:.1f}s, {output_size})" if isinstance(duration, (int, float)) else ""
                    elif status == 'error':
                        error = log.get('error', 'Unknown error')
                        status_icon = "❌"
                        details = f"({error})"
                    else:
                        status_icon = "⏳"
                        details = ""
                    
                    # Format HP indicator
                    if hp != 'unknown' and isinstance(hp, (int, float)):
                        hp_indicator = f"⚡{hp}"
                    else:
                        hp_indicator = ""
                    
                    # Build the line
                    line = f"{status_icon} {user} {hp_indicator} {device_display} {time_str} {details}"
                    lines.append(line)
                
                content = "\n".join(lines)
        else:
            content = f"[red]Error fetching logs: {response.status_code}[/red]"
            
    except Exception as e:
        content = f"[red]Error: {str(e)}[/red]"
    
    return Panel(content, title=title, border_style="green")


def create_transcoder_panel_with_data(logs, stats, title):
    """Create panel with actual transcoder data"""
    
    # Create stats summary
    total = stats.get('total', 0)
    successful = stats.get('successful', 0)
    failed = stats.get('failed', 0)
    success_rate = stats.get('successRate', 0)
    avg_duration = stats.get('avgDuration', 0)
    
    # Create table for recent operations
    table = Table(show_header=True, header_style="bold magenta", box=None, pad_edge=False)
    table.add_column("Time", style="cyan", width=8)
    table.add_column("User", style="green", width=12)
    table.add_column("Device", style="blue", width=8)
    table.add_column("File", style="yellow", width=16)
    table.add_column("Status", width=8)
    table.add_column("Duration", style="blue", width=6)
    
    if logs:
        # Filter to show only completed or failed operations (not started/in-progress)
        completed_logs = [log for log in logs if log.get('status') in ['completed', 'failed']]
        
        for log in completed_logs[:5]:  # Show last 5 completed operations
            # Format timestamp
            try:
                dt = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
            except:
                time_str = "Unknown"
            
            # Format user with HP
            user = log.get('user', 'anonymous')[:11]
            user_hp = log.get('userHP', 0)
            if user_hp > 0:
                hp_emoji = '🔥' if user_hp > 200 else '⚡' if user_hp > 100 else '💫'
                user = f"{user} {hp_emoji}"
            
            # Enhanced device info parsing
            platform = log.get('platform', 'unknown')
            device_info = log.get('deviceInfo', 'unknown')
            
            device_short = parse_device_display(platform, device_info)
            
            # Format filename (shorter due to device column)
            filename = log.get('filename', 'unknown')
            if len(filename) > 15:
                filename = filename[:12] + "..."
            
            # Format status with emoji and error details
            status = log.get('status', 'unknown')
            if status == 'failed':
                error_msg = log.get('error', 'Unknown error')
                # Show first few words of error
                error_short = ' '.join(error_msg.split()[:2]) if error_msg else 'Error'
                status_display = f"❌ {error_short}"
            else:
                status_display = "✅"
            
            # Format duration (shorter)
            duration = log.get('duration')
            if duration:
                if duration < 1000:
                    duration_str = f"{duration}ms"[:5]
                else:
                    duration_str = f"{duration/1000:.1f}s"[:4]
            else:
                duration_str = "-"
            
            table.add_row(time_str, user, device_short, filename, status_display, duration_str)
    else:
        table.add_row("", "", "", "No recent operations", "", "")
    
    # Create content with stats and table
    content_parts = []
    
    # Stats line
    if total > 0:
        stats_line = f"📊 Total: {total} | ✅ Success: {successful} | ❌ Failed: {failed} | 📈 Rate: {success_rate}%"
        if avg_duration > 0:
            if avg_duration < 1000:
                stats_line += f" | ⏱️ Avg: {avg_duration}ms"
            else:
                stats_line += f" | ⏱️ Avg: {avg_duration/1000:.1f}s"
    else:
        stats_line = "📊 No operations recorded yet"
    
    content_parts.append(stats_line)
    content_parts.append("")  # Empty line
    content_parts.append("Recent Operations:")
    
    # Convert table to string
    from rich.console import Console
    from io import StringIO
    
    console = Console(file=StringIO(), width=60)
    console.print(table)
    table_str = console.file.getvalue()
    content_parts.append(table_str)
    
    content = "\n".join(content_parts)
    
    # Determine border color based on recent activity
    recent_failures = sum(1 for log in logs if log.get('status') == 'failed')
    recent_successes = sum(1 for log in logs if log.get('status') == 'completed')
    
    if recent_failures > 0:
        border_color = "red"
    elif recent_successes > 0:
        border_color = "green"
    elif logs:
        border_color = "yellow"  # Operations in progress
    else:
        border_color = "blue"   # No activity
    
    return Panel(content, title=title, border_style=border_color)


def create_transcoder_panel_error(error_msg, title):
    """Create error panel when service is unavailable"""
    content = f"⚠️ Video Transcoder Service\n\nStatus: {error_msg}\n\n💡 Check if video-worker is running on port 8081"
    return Panel(content, title=title, border_style="red")

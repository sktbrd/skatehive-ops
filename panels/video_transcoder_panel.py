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


def create_video_transcoder_panel(monitor, title: str = "📹 Video Transcoder") -> Panel:
    """Create video transcoder panel showing latest transcode operations"""
    
    try:
        # Try to fetch logs from video-worker service
        response = requests.get('http://localhost:8081/logs?limit=5', timeout=3)
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            stats = data.get('stats', {})
            
            return create_transcoder_panel_with_data(logs, stats, title)
        else:
            return create_transcoder_panel_error(f"Service returned {response.status_code}", title)
            
    except requests.exceptions.ConnectionError:
        return create_transcoder_panel_error("Service not running", title)
    except requests.exceptions.Timeout:
        return create_transcoder_panel_error("Service timeout", title)
    except Exception as e:
        return create_transcoder_panel_error(f"Error: {str(e)}", title)


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
        for log in logs:
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
            
            # Format device info
            platform = log.get('platform', 'unknown')
            device_info = log.get('deviceInfo', 'unknown')
            if platform != 'unknown':
                device_emoji = '📱' if platform == 'mobile' else '📟' if platform == 'tablet' else '💻'
                device_short = f"{device_emoji}{platform[:3]}"
            else:
                device_short = "❓unk"
            
            # Format filename (shorter due to device column)
            filename = log.get('filename', 'unknown')
            if len(filename) > 15:
                filename = filename[:12] + "..."
            
            # Format status with emoji
            status = log.get('status', 'unknown')
            status_emoji = {
                'started': '🚀',
                'completed': '✅', 
                'failed': '❌',
                'processing': '⚙️',
                'uploading': '☁️'
            }.get(status, f"❓")
            
            # Format duration (shorter)
            duration = log.get('duration')
            if duration:
                if duration < 1000:
                    duration_str = f"{duration}ms"[:5]
                else:
                    duration_str = f"{duration/1000:.1f}s"[:4]
            else:
                duration_str = "-"
            
            table.add_row(time_str, user, device_short, filename, status_emoji, duration_str)
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

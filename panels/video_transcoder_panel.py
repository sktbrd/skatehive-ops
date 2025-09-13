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
    
    # Handle device info formats: "web/MacIntel/desktop" or "desktop/macOS/Chrome"
    if device_info and '/' in device_info:
        parts = device_info.split('/')
        
        if len(parts) >= 2:
            first_part = parts[0]   # web, desktop, mobile, tablet
            second_part = parts[1]  # MacIntel, macOS, iOS, Android, etc.
            
            # NEW enhanced format: "desktop/macOS/Chrome"
            if first_part in ['desktop', 'mobile', 'tablet']:
                if 'macOS' in second_part:
                    return "💻 Mac"
                elif 'Windows' in second_part:
                    return "💻 Win"
                elif 'Linux' in second_part:
                    return "� Linux"
                elif 'iOS' in second_part:
                    return "📱 iPhone" if first_part == 'mobile' else "📟 iPad"
                elif 'Android' in second_part:
                    return "� Android"
                else:
                    # Fallback based on device type
                    if first_part == 'mobile':
                        return "� Mobile"
                    elif first_part == 'tablet':
                        return "� Tablet"
                    else:
                        return "💻 Desktop"
            
            # OLD format: "web/MacIntel/desktop"
            elif first_part == 'web':
                if 'mac' in second_part.lower():
                    return "💻 Mac"
                elif 'win' in second_part.lower():
                    return "� Win"
                elif 'linux' in second_part.lower():
                    return "� Linux"
                else:
                    return "💻 Web"
    
    # Fallback for platform only
    if platform == 'mobile':
        return "📱 Mobile"
    elif platform == 'tablet':
        return "📟 Tablet"
    elif platform in ['web', 'desktop']:
        return "💻 Web"
    else:
        return "❓ Unknown"


def create_video_transcoder_panel(monitor, title: str = "📹 Video Transcoder") -> Panel:
    """Create video transcoder panel showing latest transcode operations"""
    
    try:
        import requests
        
        # Fetch logs from video-worker service via Tailscale Funnel
        response = requests.get('https://raspberrypi.tail83ea3e.ts.net/video/logs?limit=10', timeout=10)
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            stats = data.get('stats', {})
            
            # Show all operations (completed, failed, and started) for better visibility
            all_operations = []
            for log in logs:
                # Include all operations, not just completed ones
                if log.get('status') in ['completed', 'failed', 'started']:
                    all_operations.append(log)
            
            # Sort by timestamp descending and take last 5 operations
            all_operations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            recent_logs = all_operations[:5]
            
            if not recent_logs:
                content = "[dim]No operations detected yet[/dim]"
            else:
                lines = []
                for log in recent_logs:
                    # Get user info with HP - try both field names
                    user = log.get('user', log.get('creator', 'unknown'))
                    hp = log.get('userHP', 'N/A')
                    
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
                    filename = log.get('filename', 'unknown')
                    duration_ms = log.get('duration', 0)
                    duration_str = f"{duration_ms/1000:.1f}s" if duration_ms > 0 else "..."
                    
                    # Status indicators
                    if status == 'completed':
                        status_icon = "✅"
                        status_color = "green"
                    elif status == 'failed':
                        status_icon = "❌"
                        status_color = "red"
                        # Show detailed error if available
                        error = log.get('error', '')
                        error_message = log.get('message', '')
                        error_details = error or error_message or 'Unknown error'
                        
                        # Extract meaningful error info
                        if 'timeout' in error_details.lower():
                            error_short = "Timeout"
                        elif 'memory' in error_details.lower():
                            error_short = "Memory issue"
                        elif 'codec' in error_details.lower():
                            error_short = "Codec error"
                        elif 'permission' in error_details.lower():
                            error_short = "Permission denied"
                        elif 'space' in error_details.lower():
                            error_short = "No disk space"
                        elif len(error_details) > 40:
                            error_short = error_details[:37] + "..."
                        else:
                            error_short = error_details
                        
                        duration_str = f"[red]ERROR:[/red] {error_short}"
                    elif status == 'started':
                        status_icon = "🔄"
                        status_color = "yellow"
                        duration_str = "Processing..."
                    else:
                        status_icon = "❓"
                        status_color = "dim"
                    
                    # Format line with rich user info
                    user_display = f"{user}" if hp == 'N/A' else f"{user} ({hp} HP)"
                    line = f"{status_icon} [{status_color}]{time_str}[/{status_color}] {device_display} [bold]{user_display}[/bold] - {filename} [{status_color}]{duration_str}[/{status_color}]"
                    lines.append(line)
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
    
    # Detect specific error types
    if "Connection refused" in error_msg or "ConnectTimeout" in error_msg:
        status = "Service Offline"
        details = "video-worker container not running on port 8081"
        fix = "💡 Run: docker run -d --name video-worker -p 8081:8080 video-worker"
    elif "404" in error_msg:
        status = "API Endpoint Missing"  
        details = "/logs endpoint not found"
        fix = "💡 Check video-worker version and API endpoints"
    elif "timeout" in error_msg.lower():
        status = "Service Timeout"
        details = "video-worker not responding"
        fix = "💡 Check docker logs video-worker"
    else:
        status = "Service Error"
        details = error_msg[:50] + "..." if len(error_msg) > 50 else error_msg
        fix = "💡 Check service logs and configuration"
    
    content = f"⚠️ Video Transcoder Service\n\nStatus: [red]{status}[/red]\nDetails: {details}\n\n{fix}"
    return Panel(content, title=title, border_style="red")

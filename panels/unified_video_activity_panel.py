#!/usr/bin/env python3
"""
Unified Video Activity Panel
Displays video transcoding activity from all services (Mac Mini, Raspberry Pi, Render)
"""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from datetime import datetime
import asyncio
from monitors.unified_video_monitor import get_unified_video_activity, get_cached_video_activity


def parse_device_display(platform, device_info):
    """Parse device info into a concise display format"""
    
    if device_info and '/' in device_info:
        parts = device_info.split('/')
        
        if len(parts) >= 2:
            first_part = parts[0]   # web, desktop, mobile, tablet
            second_part = parts[1]  # MacIntel, macOS, iOS, Android, etc.
            
            if first_part in ['desktop', 'mobile', 'tablet']:
                if 'macOS' in second_part:
                    return "💻 Mac"
                elif 'Windows' in second_part:
                    return "💻 Win"
                elif 'Linux' in second_part:
                    return "🐧 Linux"
                elif 'iOS' in second_part:
                    return "📱 iPhone" if first_part == 'mobile' else "📟 iPad"
                elif 'Android' in second_part:
                    return "🤖 Android"
                else:
                    if first_part == 'mobile':
                        return "📱 Mobile"
                    elif first_part == 'tablet':
                        return "📟 Tablet"
                    else:
                        return "💻 Desktop"
            
            elif first_part == 'web':
                if 'mac' in second_part.lower():
                    return "💻 Mac"
                elif 'win' in second_part.lower():
                    return "💻 Win"
                else:
                    return "🌐 Web"
    
    # Fallback
    if platform == 'mobile':
        return "📱 Mobile"
    elif platform == 'tablet':
        return "📟 Tablet"
    else:
        return "💻 Desktop"


def create_unified_video_activity_panel():
    """Create panel showing unified video transcoding activity from all services"""
    
    try:
        # Get cached activity data (quick, non-blocking)
        activity_data = get_cached_video_activity()
        
        if not activity_data or not activity_data.get('logs'):
            return create_no_activity_panel()
        
        logs = activity_data['logs']
        service_status = activity_data.get('service_status', {})
        summary = activity_data.get('summary', {})
        last_update = activity_data.get('last_update')
        
        # Create services status line
        services_line = ""
        for service_key, status_info in service_status.items():
            status = status_info.get('status', 'unknown')
            if service_key == 'mac_mini':
                icon = "🖥️"
                name = "Mac"
            elif service_key == 'raspberry_pi':
                icon = "🥧"
                name = "Pi"
            elif service_key == 'render_cloud':
                icon = "☁️"
                name = "Cloud"
            else:
                icon = "🔧"
                name = service_key
            
            if status == 'online':
                services_line += f"[green]{icon} {name}[/green]  "
            elif status == 'offline':
                services_line += f"[red]{icon} {name}[/red]  "
            else:
                services_line += f"[yellow]{icon} {name}[/yellow]  "
        
        # Create summary stats
        total_ops = summary.get('total_operations', 0)
        successful = summary.get('successful', 0)
        failed = summary.get('failed', 0)
        success_rate = summary.get('success_rate', 0)
        
        # Create header with stats
        header = f"Services: {services_line}\n"
        header += f"Recent: {total_ops} ops • {successful}✅ {failed}❌ • {success_rate}% success\n"
        
        # Create table for recent operations
        table = Table(show_header=True, header_style="bold magenta", box=None, pad_edge=False)
        table.add_column("Time", style="cyan", width=8)
        table.add_column("Service", style="blue", width=8)
        table.add_column("User", style="green", width=12)
        table.add_column("Device", style="blue", width=8)
        table.add_column("File", style="yellow", width=14)
        table.add_column("Status", width=8)
        table.add_column("Duration", style="blue", width=6)
        
        # Add recent operations from all services
        for log in logs[:8]:  # Show last 8 operations
            # Format timestamp
            try:
                dt = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
            except:
                time_str = "Unknown"
            
            # Service info
            service_icon = log.get('service_icon', '🔧')
            service_name = log.get('service_name', 'Unknown')
            if len(service_name) > 6:
                service_short = service_name[:6]
            else:
                service_short = service_name
            service_display = f"{service_icon} {service_short}"
            
            # Format user with HP
            user = log.get('user', log.get('creator', 'anonymous'))[:11]
            user_hp = log.get('userHP', 0)
            if user_hp > 0:
                hp_emoji = '🔥' if user_hp > 200 else '⚡' if user_hp > 100 else '💫'
                user = f"{user} {hp_emoji}"
            
            # Parse device info
            platform = log.get('platform', 'unknown')
            device_info = log.get('deviceInfo', 'unknown')
            device_display = parse_device_display(platform, device_info)
            
            # Format filename
            filename = log.get('filename', log.get('file', 'unknown'))
            if len(filename) > 13:
                filename = filename[:10] + "..."
            
            # Format status with emoji
            status = log.get('status', 'unknown')
            if status == 'completed':
                status_display = "✅ Done"
            elif status == 'failed':
                error_msg = log.get('error', 'Error')
                if 'timeout' in error_msg.lower():
                    status_display = "⏰ Timeout"
                elif 'memory' in error_msg.lower():
                    status_display = "💾 Memory"
                elif 'space' in error_msg.lower():
                    status_display = "📁 Space"
                else:
                    status_display = "❌ Failed"
            elif status == 'started':
                status_display = "🟡 Started"
            else:
                status_display = f"❓ {status}"
            
            # Format duration
            duration_ms = log.get('duration', 0)
            if duration_ms > 0:
                duration_str = f"{duration_ms/1000:.1f}s"
            else:
                duration_str = "..."
            
            table.add_row(
                time_str,
                service_display,
                user,
                device_display,
                filename,
                status_display,
                duration_str
            )
        
        content = header + "\n" + str(table)
        
        # Update time info
        if last_update:
            try:
                dt = datetime.fromisoformat(last_update)
                update_str = dt.strftime('%H:%M:%S')
                title = f"🎬 Video Transcoding Activity (Updated: {update_str})"
            except:
                title = "🎬 Video Transcoding Activity"
        else:
            title = "🎬 Video Transcoding Activity"
        
        # Determine border color based on recent activity
        recent_failures = len([log for log in logs[:5] if log.get('status') == 'failed'])
        recent_successes = len([log for log in logs[:5] if log.get('status') == 'completed'])
        
        if recent_failures > 0:
            border_color = "red"
        elif recent_successes > 0:
            border_color = "green"
        else:
            border_color = "blue"
        
        return Panel(content, title=title, border_style=border_color)
        
    except Exception as e:
        return create_error_panel(str(e))


def create_no_activity_panel():
    """Create panel when no video activity is found"""
    content = (
        "🎬 Video Transcoding Services\n\n"
        "🖥️ Mac Mini M4: Checking...\n"
        "🥧 Raspberry Pi: Checking...\n"
        "☁️ Render Cloud: Checking...\n\n"
        "💡 No recent video transcoding activity\n"
        "   Upload a video to see activity here"
    )
    return Panel(content, title="🎬 Video Transcoding Activity", border_style="yellow")


def create_error_panel(error_msg):
    """Create error panel when there's an issue fetching activity"""
    content = (
        f"⚠️ Video Activity Monitor Error\n\n"
        f"Error: {error_msg[:100]}\n\n"
        f"💡 Checking video services...\n"
        f"   - Mac Mini transcoder\n"
        f"   - Raspberry Pi transcoder\n"
        f"   - Render cloud transcoder"
    )
    return Panel(content, title="🎬 Video Transcoding Activity", border_style="red")


async def create_unified_video_activity_panel_async():
    """Async version that fetches fresh data"""
    try:
        # Fetch fresh activity data from all services
        activity_data = await get_unified_video_activity()
        
        # Update the cached data and return panel
        return create_unified_video_activity_panel()
        
    except Exception as e:
        return create_error_panel(str(e))
#!/usr/bin/env python3
"""
Instagram Download Logs Panel
Displays recent Instagram download history and statistics
"""

import json
import requests
from datetime import datetime
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box
import sys
from pathlib import Path

# Import configuration
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import INSTAGRAM_LOCAL_URL, INSTAGRAM_EXTERNAL_URL


def get_instagram_logs():
    """Fetch Instagram download logs"""
    try:
        # Try external URL first, fall back to local
        url = INSTAGRAM_EXTERNAL_URL if INSTAGRAM_EXTERNAL_URL else INSTAGRAM_LOCAL_URL
        response = requests.get(f"{url}/logs", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"logs": [], "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"logs": [], "error": str(e)}


def create_instagram_logs_panel():
    """Create Instagram download logs panel"""
    logs_data = get_instagram_logs()
    logs = logs_data.get("logs", [])
    
    if not logs:
        return Panel(
            Align.center("No Instagram download logs available"),
            title="📱 Instagram Downloads",
            border_style="blue"
        )
    
    table = Table(show_header=True, header_style="bold blue", box=box.SIMPLE)
    table.add_column("Time", width=8)
    table.add_column("Status", width=10)
    table.add_column("URL", width=30)
    table.add_column("File", width=25)
    table.add_column("Size", width=8)
    table.add_column("Duration", width=8)
    
    for log in logs[:10]:  # Show last 10 downloads
        try:
            timestamp = datetime.fromisoformat(log.get('timestamp', '').replace('Z', '+00:00'))
            time_str = timestamp.strftime("%H:%M:%S")
        except:
            time_str = "Unknown"
        
        status = log.get('status', 'unknown')
        success = log.get('success', False)
        
        # Status formatting
        if status == "completed" and success:
            status_display = "✅ Complete"
        elif status == "failed":
            status_display = "❌ Failed"
        elif status == "started":
            status_display = "🔄 Processing"
        else:
            status_display = status
        
        # URL shortening
        url = log.get('url', '')
        if 'instagram.com/p/' in url:
            url_short = url.split('/p/')[-1][:15] + "..."
        else:
            url_short = url[:30] + "..." if len(url) > 30 else url
        
        # File info
        filename = log.get('filename', 'N/A')
        if len(filename) > 23:
            filename = filename[:20] + "..."
        
        # Size formatting
        bytes_size = log.get('bytes', 0)
        if bytes_size > 1024*1024:
            size_str = f"{bytes_size/(1024*1024):.1f}MB"
        elif bytes_size > 1024:
            size_str = f"{bytes_size/1024:.1f}KB"
        else:
            size_str = f"{bytes_size}B" if bytes_size else "N/A"
        
        # Duration
        duration = log.get('duration', 0)
        duration_str = f"{duration/1000:.1f}s" if duration else "N/A"
        
        table.add_row(
            time_str,
            status_display,
            url_short,
            filename,
            size_str,
            duration_str
        )
    
    # Summary stats
    total = logs_data.get("total", 0)
    success_count = logs_data.get("success_count", 0)
    failure_count = logs_data.get("failure_count", 0)
    success_rate = (success_count / total * 100) if total > 0 else 0
    
    title = f"📱 Instagram Downloads ({total} total, {success_rate:.1f}% success)"
    
    return Panel(
        table,
        title=title,
        border_style="blue"
    )

#!/usr/bin/env python3
"""
Webapp Client Logs Panel
Displays client-side errors from the SkateHive3.0 webapp including upload failures,
size restrictions, and other browser-side issues.
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box


# Import configuration
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TAILSCALE_HOSTNAME


class WebappErrorTracker:
    """Track and manage client-side errors from the webapp"""
    
    def __init__(self):
        # Try localhost first (for development), fallback to production URL
        external_url = f"https://{TAILSCALE_HOSTNAME}" if TAILSCALE_HOSTNAME else None
        self.base_urls = [
            "http://localhost:3000",  # Development server
        ]
        if external_url:
            self.base_urls.append(external_url)  # Production via Tailscale
        self.active_url = None
        self.error_cache = []
        self.last_error_check = None
    
    def get_webapp_errors(self, limit: int = 50) -> List[Dict]:
        """Get recent client errors from the webapp"""
        for base_url in self.base_urls:
            try:
                response = requests.get(
                    f"{base_url}/api/logs/client-errors?limit={limit}", 
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    self.error_cache = data.get('logs', [])
                    self.last_error_check = datetime.now()
                    self.active_url = base_url
                    return self.error_cache
                
            except Exception as e:
                # Try next URL
                continue
        
        # If all URLs failed, return cached data
        return self.error_cache
    
    def get_error_summary(self) -> Dict:
        """Get summary of error types and counts"""
        errors = self.get_webapp_errors()
        
        summary = {
            'total': len(errors),
            'by_level': {'error': 0, 'warning': 0, 'info': 0},
            'by_type': {},
            'recent_errors': 0,  # Last hour
            'upload_errors': 0,
            'size_restrictions': 0
        }
        
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        for error in errors:
            # Count by level
            level = error.get('level', 'error')
            summary['by_level'][level] = summary['by_level'].get(level, 0) + 1
            
            # Count by type
            error_type = error.get('type', 'unknown')
            summary['by_type'][error_type] = summary['by_type'].get(error_type, 0) + 1
            
            # Count recent errors (last hour)
            try:
                error_time = datetime.fromisoformat(error.get('timestamp', '').replace('Z', '+00:00'))
                if error_time.replace(tzinfo=None) >= one_hour_ago:
                    summary['recent_errors'] += 1
            except:
                pass
            
            # Count specific error types
            if 'upload' in error_type.lower():
                summary['upload_errors'] += 1
            if 'size_restriction' in error_type.lower():
                summary['size_restrictions'] += 1
        
        return summary


# Global instance
webapp_tracker = WebappErrorTracker()


def create_webapp_logs_panel() -> Panel:
    """Create webapp client logs panel"""
    try:
        errors = webapp_tracker.get_webapp_errors(limit=30)
        summary = webapp_tracker.get_error_summary()
        
        # Create the main table
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Time", style="cyan", width=8)
        table.add_column("Level", width=7)
        table.add_column("Type", style="yellow", width=16)
        table.add_column("Message", width=40)
        table.add_column("File", style="blue", width=15)
        
        # Add recent errors to table
        for error in errors[:15]:  # Show last 15 errors
            timestamp = error.get('timestamp', '')
            try:
                # Parse and format timestamp
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
            except:
                time_str = timestamp[:8] if timestamp else 'N/A'
            
            level = error.get('level', 'error')
            error_type = error.get('type', 'unknown')
            message = error.get('message', 'No message')
            
            # Get file info from details
            details = error.get('details', {})
            file_name = details.get('fileName', '')
            if not file_name and details.get('fileSize'):
                file_size_mb = round(details.get('fileSize', 0) / 1024 / 1024, 1)
                file_name = f"{file_size_mb}MB"
            
            # Truncate long messages
            if len(message) > 38:
                message = message[:35] + "..."
            
            # Color code by level
            level_style = "red" if level == "error" else "yellow" if level == "warning" else "green"
            
            table.add_row(
                time_str,
                f"[{level_style}]{level.upper()}[/{level_style}]",
                error_type[:15],
                message,
                file_name[:14] if file_name else ""
            )
        
        # Create summary info
        total_errors = summary['total']
        recent_errors = summary['recent_errors']
        upload_errors = summary['upload_errors']
        size_restrictions = summary['size_restrictions']
        
        # Build title with status indicators
        title_parts = ["🌐 Webapp Client Logs"]
        if recent_errors > 0:
            title_parts.append(f"🔴 {recent_errors} recent")
        if size_restrictions > 0:
            title_parts.append(f"📏 {size_restrictions} size")
        if upload_errors > 0:
            title_parts.append(f"📤 {upload_errors} upload")
            
        title = " ".join(title_parts)
        
        # Status line
        status_text = Text()
        status_text.append(f"Total: {total_errors} ", style="bold")
        status_text.append(f"Recent (1h): {recent_errors} ", style="red" if recent_errors > 0 else "green")
        status_text.append(f"Upload: {upload_errors} ", style="yellow" if upload_errors > 0 else "dim")
        status_text.append(f"Size: {size_restrictions}", style="orange1" if size_restrictions > 0 else "dim")
        
        # Combine table with status
        content = Text()
        content.append(status_text)
        content.append("\n\n")
        
        # Return panel with table
        return Panel(
            table,
            title=title,
            title_align="left",
            border_style="cyan",
            expand=True
        )
        
    except Exception as e:
        error_text = Text()
        error_text.append("❌ Failed to load webapp logs\n", style="red")
        error_text.append(f"Error: {str(e)}", style="dim")
        
        return Panel(
            error_text,
            title="🌐 Webapp Client Logs - ERROR",
            title_align="left",
            border_style="red",
            expand=True
        )


def create_webapp_error_summary_panel() -> Panel:
    """Create a compact summary panel for webapp errors"""
    try:
        summary = webapp_tracker.get_error_summary()
        
        content = Text()
        
        # Recent activity indicator
        recent = summary['recent_errors']
        if recent > 0:
            content.append(f"🔴 {recent} errors (1h)\n", style="red bold")
        else:
            content.append("✅ No recent errors\n", style="green")
        
        # Key metrics
        content.append(f"Total Logged: {summary['total']}\n", style="dim")
        content.append(f"Upload Issues: {summary['upload_errors']}\n", 
                      style="yellow" if summary['upload_errors'] > 0 else "dim")
        content.append(f"Size Limits: {summary['size_restrictions']}", 
                      style="orange1" if summary['size_restrictions'] > 0 else "dim")
        
        # Connection status
        if webapp_tracker.last_error_check:
            time_diff = datetime.now() - webapp_tracker.last_error_check
            if time_diff.seconds < 60:
                content.append(f"\n🟢 Connected", style="green")
            else:
                content.append(f"\n⚠️ Last check: {time_diff.seconds}s ago", style="yellow")
        else:
            content.append(f"\n🔴 Not connected", style="red")
        
        return Panel(
            content,
            title="🌐 Client Errors",
            title_align="left",
            border_style="cyan",
            width=25
        )
        
    except Exception as e:
        return Panel(
            Text(f"❌ Error loading\nwebapp summary", style="red"),
            title="🌐 Client Errors",
            border_style="red",
            width=25
        )
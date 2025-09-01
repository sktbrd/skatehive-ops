#!/usr/bin/env python3
"""
Logs Panel
Displays compact summary of container logs for download tracking and error detection
"""

import re
from rich.panel import Panel
from rich.text import Text


def create_logs_panel(monitor, container: str, title: str) -> Panel:
    """Create compact logs panel for a service"""
    logs = monitor.get_recent_logs(container, 15)  # Get fewer lines for compactness

    # Parse logs for essential info
    downloads = []
    last_error = None
    activity_count = 0

    for log in reversed(logs):
        # Count any activity
        if any(keyword in log.lower() for keyword in ["post", "download", "processing", "completed"]):
            activity_count += 1
            
        # Look for download patterns 
        if "POST /download" in log:
            match = re.search(r'([0-9:.]+) - - \[([^\]]+)\] "POST ([^"]+)"', log)
            if match:
                ip = match.group(1).split(':')[-1]
                timestamp = match.group(2).split()[1] if ' ' in match.group(2) else match.group(2)
                downloads.append((f"Download from {ip}", timestamp))
        
        # Look for download progress
        elif "[download]" in log and "%" in log:
            progress_match = re.search(r'\[download\]\s+([0-9.]+)%\s+of\s+([0-9.]+[KMGT]?[iB]*)', log)
            if progress_match and float(progress_match.group(1)) == 100.0:
                downloads.append((f"Completed {progress_match.group(2)}", "recent"))
        
        # Look for errors
        elif any(error_word in log.lower() for error_word in ["error", "failed", "exception"]):
            if not last_error:  # Only keep the most recent error
                error_match = re.search(r'(error|failed|exception)[:\s]+(.{0,40})', log.lower())
                if error_match:
                    last_error = error_match.group(2)[:30] + "..."

    # Create summary content
    content_lines = []
    
    if not logs:
        content_lines.append("No recent logs found.")
    else:
        if not last_error:
            content_lines.append("No errors found in recent logs.")
        
    content_lines.append("")
    content_lines.append("Recent Activity:")
    
    if activity_count > 0:
        content_lines.append(f"{activity_count} recent activities detected")
    else:
        content_lines.append("Only health check requests in recent logs")

    # Show recent downloads (limit to 3 most recent)
    if downloads:
        content_lines.append("")
        content_lines.append("Recent Downloads:")
        for download, timestamp in downloads[-3:]:
            content_lines.append(f"• {download}")
    
    # Show errors if any
    if last_error:
        content_lines.append("")
        content_lines.append(f"⚠️ Last Error: {last_error}")

    content = "\n".join(content_lines)
    
    # Determine border color based on activity
    border_color = "red" if last_error else "green" if downloads else "blue"
    
    return Panel(content, title=title, border_style=border_color)

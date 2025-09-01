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
    logs = monitor.get_recent_logs(container, 25)  # Get more lines to capture full download sequences

    # Parse logs for essential info
    downloads = []
    last_error = None
    activity_count = 0

    for log in reversed(logs):
        # Count any activity
        if any(keyword in log.lower() for keyword in ["post", "download", "processing", "completed", "info", "converted"]):
            activity_count += 1
            
        # Look for Instagram/video download start
        if "INFO Downloading:" in log:
            url_match = re.search(r'INFO Downloading:\s+(https?://[^\s]+)', log)
            if url_match:
                url = url_match.group(1)
                # Extract platform and video ID for cleaner display
                if "instagram.com" in url:
                    video_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
                    video_id = video_id.split('?')[0]  # Remove query params
                    downloads.append((f"📱 Instagram: {video_id[:15]}...", "downloading"))
                elif "youtube.com" in url or "youtu.be" in url:
                    downloads.append((f"📺 YouTube video", "downloading"))
                else:
                    platform = url.split('//')[1].split('/')[0].replace('www.', '')
                    downloads.append((f"🎥 {platform} video", "downloading"))
        
        # Look for completed conversions/uploads
        elif "Final file for IPFS upload:" in log:
            file_match = re.search(r'Final file for IPFS upload:\s+(.+)', log)
            if file_match:
                filename = file_match.group(1).split('/')[-1]  # Get just the filename
                # Clean up the filename for display
                if len(filename) > 30:
                    filename = filename[:27] + "..."
                downloads.append((f"✅ Ready: {filename}", "completed"))
        
        # Look for traditional download patterns (keeping for compatibility)
        elif "POST /download" in log:
            match = re.search(r'([0-9:.]+) - - \[([^\]]+)\] "POST ([^"]+)"', log)
            if match:
                ip = match.group(1).split(':')[-1]
                timestamp = match.group(2).split()[1] if ' ' in match.group(2) else match.group(2)
                downloads.append((f"📥 Request from {ip}", timestamp))
        
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

    # Show recent downloads (limit to 5 most recent)
    if downloads:
        content_lines.append("")
        content_lines.append("Recent Downloads:")
        for download, timestamp in downloads[-5:]:
            content_lines.append(f"• {download}")
    else:
        content_lines.append("")
        content_lines.append("No recent downloads detected")
            content_lines.append(f"• {download}")
    
    # Show errors if any
    if last_error:
        content_lines.append("")
        content_lines.append(f"⚠️ Last Error: {last_error}")

    content = "\n".join(content_lines)
    
    # Determine border color based on activity
    recent_downloads = [d for d, t in downloads if "completed" in t or "✅" in d[0]]
    border_color = "red" if last_error else "green" if recent_downloads else "yellow" if downloads else "blue"
    
    return Panel(content, title=title, border_style=border_color)

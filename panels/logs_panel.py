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
        # Count any activity (but ignore health checks)
        if any(keyword in log.lower() for keyword in ["downloading", "converted", "final file", "post /download"]) and "health" not in log.lower():
            activity_count += 1
            
        # Look for Instagram/video download start
        if "INFO Downloading:" in log:
            url_match = re.search(r'INFO Downloading:\s+(https?://[^\s]+)', log)
            if url_match:
                url = url_match.group(1)
                # Extract platform and video ID for cleaner display
                if "instagram.com" in url:
                    if "/reel/" in url:
                        video_id = url.split('/reel/')[-1].split('?')[0][:12]
                        downloads.append((f"📱 IG Reel: {video_id}", "downloading"))
                    elif "/p/" in url:
                        video_id = url.split('/p/')[-1].split('?')[0][:12]
                        downloads.append((f"📱 IG Post: {video_id}", "downloading"))
                    else:
                        downloads.append((f"📱 Instagram content", "downloading"))
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
                if len(filename) > 25:
                    filename = filename[:22] + "..."
                downloads.append((f"✅ Ready: {filename}", "completed"))
        
        # Look for specific Instagram errors
        elif "There is no video in this post" in log:
            downloads.append((f"❌ No video in IG post", "error"))
            if not last_error:
                last_error = "Instagram post contains no video"
        
        # Look for other specific errors
        elif "ERROR:" in log and "[Instagram]" in log:
            error_match = re.search(r'ERROR: \[Instagram\] ([^:]+): (.+)', log)
            if error_match and not last_error:
                video_id = error_match.group(1)[:10]
                error_msg = error_match.group(2)[:30]
                last_error = f"IG {video_id}: {error_msg}"
                downloads.append((f"❌ Failed: {video_id}", "error"))
        
        # Look for HTTP POST requests
        elif "POST /download" in log:
            if "500 Internal Server Error" in log:
                downloads.append((f"❌ Download failed", "error"))
            elif "200 OK" in log:
                downloads.append((f"📥 Download request", "success"))
        
        # Look for general errors (but avoid long stack traces)
        elif any(error_word in log.lower() for error_word in ["error", "failed", "exception"]) and "Traceback" not in log:
            if not last_error and len(log) < 100:  # Avoid long error messages
                error_match = re.search(r'(error|failed|exception)[:\s]+(.{0,35})', log.lower())
                if error_match:
                    last_error = error_match.group(2)[:30] + "..."

    # Create summary content
    content_lines = []
    
    if not logs:
        content_lines.append("No recent logs found.")
    else:
        # Show error status first
        if last_error:
            content_lines.append(f"⚠️ Last Error: {last_error}")
        else:
            content_lines.append("✅ No errors in recent logs.")
        
    content_lines.append("")
    content_lines.append("Recent Activity:")
    
    if activity_count > 0:
        content_lines.append(f"📊 {activity_count} download activities detected")
    else:
        content_lines.append("🔍 Only health checks in recent logs")

    # Show recent downloads (limit to 4 most recent)
    if downloads:
        content_lines.append("")
        content_lines.append("Recent Downloads:")
        # Show most recent downloads first
        for download, status in downloads[-4:]:
            content_lines.append(f"• {download}")
    else:
        content_lines.append("")
        content_lines.append("❓ No downloads detected in recent logs")
    
    # Show errors if any
    if last_error:
        content_lines.append("")
        content_lines.append(f"⚠️ Last Error: {last_error}")

    content = "\n".join(content_lines)
    
    # Determine border color based on activity and errors
    error_downloads = [d for d, s in downloads if "❌" in d]
    successful_downloads = [d for d, s in downloads if "✅" in d]
    
    if last_error or error_downloads:
        border_color = "red"
    elif successful_downloads:
        border_color = "green"  
    elif downloads:
        border_color = "yellow"  # Downloads in progress
    else:
        border_color = "blue"  # No activity
    
    return Panel(content, title=title, border_style=border_color)

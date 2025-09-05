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

    # Determine service type from container name
    is_video_worker = "video-worker" in container
    
    for log in reversed(logs):
        # Count any activity based on service type
        if is_video_worker:
            # For video-worker: look for POST /transcode operations
            if "POST /transcode" in log and "health" not in log.lower():
                activity_count += 1
        else:
            # For ytipfs-worker: look for download operations
            if any(keyword in log.lower() for keyword in ["downloading", "converted", "final file", "post /download"]) and "health" not in log.lower():
                activity_count += 1
            
    for log in reversed(logs):
        # Count any activity based on service type
        if is_video_worker:
            # For video-worker: look for POST /transcode operations
            if "POST /transcode" in log and "health" not in log.lower():
                activity_count += 1
        else:
            # For ytipfs-worker: look for download operations
            if any(keyword in log.lower() for keyword in ["downloading", "converted", "final file", "post /download"]) and "health" not in log.lower():
                activity_count += 1
            
        # Service-specific log parsing
        if is_video_worker:
            # Parse video-worker enhanced logs
            if "TRANSCODE-START" in log:
                # Extract request info from enhanced logs
                request_id_match = re.search(r'ID: ([a-f0-9]{8})', log)
                client_match = re.search(r'Client: ([^\s]+)', log)
                creator_match = re.search(r'Creator: ([^\s]+)', log)
                
                request_id = request_id_match.group(1) if request_id_match else "unknown"
                client = client_match.group(1) if client_match else "unknown"
                creator = creator_match.group(1) if creator_match else "anonymous"
                
                downloads.append((f"🚀 Starting: {request_id} | {creator} | {client[:15]}", "starting"))
                
            elif "TRANSCODE-SUCCESS" in log:
                # Extract completion info
                request_id_match = re.search(r'ID: ([a-f0-9]{8})', log)
                duration_match = re.search(r'Duration: (\d+)ms', log)
                
                request_id = request_id_match.group(1) if request_id_match else "unknown"
                duration = duration_match.group(1) if duration_match else "unknown"
                
                downloads.append((f"✅ Completed: {request_id} ({duration}ms)", "completed"))
                
            elif "TRANSCODE-FAILED" in log:
                # Extract failure info
                request_id_match = re.search(r'ID: ([a-f0-9]{8})', log)
                error_match = re.search(r'Error: ([^|]+)', log)
                
                request_id = request_id_match.group(1) if request_id_match else "unknown"
                error = error_match.group(1).strip() if error_match else "unknown error"
                
                downloads.append((f"❌ Failed: {request_id} - {error[:30]}", "error"))
                if not last_error:
                    last_error = f"Request {request_id}: {error[:50]}"
                    
            elif "FFMPEG-PROGRESS" in log:
                # Extract progress info
                request_id_match = re.search(r'ID: ([a-f0-9]{8})', log)
                time_match = re.search(r'Time: ([\d:\.]+)', log)
                
                if request_id_match and time_match:
                    request_id = request_id_match.group(1)
                    time_progress = time_match.group(1)
                    downloads.append((f"⏳ Processing: {request_id} @ {time_progress}", "processing"))
                    
            elif "IPFS-UPLOAD-START" in log:
                # Extract IPFS upload start
                request_id_match = re.search(r'ID: ([a-f0-9]{8})', log)
                if request_id_match:
                    request_id = request_id_match.group(1)
                    downloads.append((f"☁️ Uploading: {request_id}", "uploading"))
                    
            elif "POST /transcode" in log:
                # Parse Apache-style log: IP - - [timestamp] "POST /transcode HTTP/1.1" status size
                if '" 200 ' in log:
                    # Extract response size to show activity
                    size_match = re.search(r'" 200 (\d+) "', log)
                    response_size = size_match.group(1) if size_match else "unknown"
                    downloads.append((f"✅ HTTP Success ({response_size}B)", "completed"))
                elif '" 500 ' in log or '" 400 ' in log:
                    downloads.append((f"❌ HTTP Error", "error"))
                    if not last_error:
                        last_error = "HTTP error in transcode request"
                elif '" 4' in log:  # 4xx errors
                    downloads.append((f"❌ Client error", "error"))
                    if not last_error:
                        last_error = "Client error in transcode request"
        else:
            # Parse ytipfs-worker download logs (original logic)
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
        
        # Look for general errors (but avoid long stack traces) - applies to both services
        if any(error_word in log.lower() for error_word in ["error", "failed", "exception"]) and "Traceback" not in log:
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
    if is_video_worker:
        content_lines.append("Recent Activity:")
    else:
        content_lines.append("Recent Activity:")
    
    if activity_count > 0:
        if is_video_worker:
            content_lines.append(f"🎬 {activity_count} transcode operations detected")
        else:
            content_lines.append(f"📊 {activity_count} download activities detected")
    else:
        content_lines.append("🔍 Only health checks in recent logs")

    # Show recent downloads (limit to 4 most recent)
    if downloads:
        content_lines.append("")
        if is_video_worker:
            content_lines.append("Recent Transcodes:")
        else:
            content_lines.append("Recent Downloads:")
        # Show most recent downloads first
        for download, status in downloads[-4:]:
            content_lines.append(f"• {download}")
    else:
        content_lines.append("")
        if is_video_worker:
            content_lines.append("❓ No transcode operations in recent logs")
        else:
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

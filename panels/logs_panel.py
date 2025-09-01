#!/usr/bin/env python3
"""
Logs Panel
Displays and parses container logs for download tracking and error detection
"""

import re
from rich.panel import Panel
from rich.text import Text


def create_logs_panel(monitor, container: str, title: str) -> Panel:
    """Create logs panel for a service"""
    logs = monitor.get_recent_logs(container, 30)  # Get more lines for better context

    # Parse logs for prettified info
    downloads = []  # (content, user, timestamp)
    last_error = None
    last_error_user = None

    for log in reversed(logs):
        # Look for various download patterns 
        # Pattern 1: POST /download requests (actual download initiation)
        if "POST /download" in log:
            # Extract IP, timestamp from HTTP log
            match = re.search(r'([0-9:.]+) - - \[([^\]]+)\] "POST ([^"]+)"', log)
            if match:
                ip = match.group(1)
                timestamp = match.group(2)
                endpoint = match.group(3)
                downloads.append(("Download Request", ip.split(':')[-1], timestamp))
        
        # Pattern 2: Download progress indicators from yt-dlp/youtube-dl
        elif "[download]" in log and "%" in log:
            # Look for download progress like "[download] 63.0% of 6.27M"
            progress_match = re.search(r'\[download\]\s+([0-9.]+)%\s+of\s+([0-9.]+[KMGT]?[iB]*)', log)
            if progress_match:
                percentage = progress_match.group(1)
                size = progress_match.group(2)
                # Only count completed downloads (100%)
                if float(percentage) == 100.0:
                    downloads.append((f"{size} file", "system", "completed"))
        
        # Pattern 3: INFO messages about downloading specific content
        elif "INFO Downloading:" in log:
            # Extract the URL being downloaded
            url_match = re.search(r'INFO Downloading: (.+)', log)
            if url_match:
                url = url_match.group(1)
                # Extract video ID or meaningful part
                if "youtube.com" in url or "youtu.be" in url:
                    video_id = url.split('/')[-1].split('?')[0][-11:]  # Last 11 chars for YT video ID
                    downloads.append((f"YT:{video_id}", "system", "downloading"))
                else:
                    domain = url.split('/')[2] if len(url.split('/')) > 2 else "external"
                    downloads.append((domain, "system", "downloading"))
        
        # Pattern 4: INFO messages about converted file paths
        elif "INFO Converted file path:" in log:
            path_match = re.search(r'INFO Converted file path: (.+)', log)
            if path_match:
                filepath = path_match.group(1)
                filename = filepath.split('/')[-1][:20]  # Get filename, truncate if long
                downloads.append((filename, "system", "converted"))
                
        if len(downloads) >= 5:
            break

    # Find last error and user
    for log in reversed(logs):
        # Look for HTTP errors (4xx, 5xx status codes) or explicit error messages
        if any(pattern in log.lower() for pattern in ["error", " 4", " 5"]) and not "GET /health" in log:
            # Check for HTTP error status codes
            http_error_match = re.search(r'"[^"]*" ([45]\d\d) ', log)
            if http_error_match:
                status_code = http_error_match.group(1)
                last_error = f"HTTP {status_code} error in: {log.strip()}"
                # Extract IP as user
                ip_match = re.search(r'([0-9:.]+) - -', log)
                if ip_match:
                    last_error_user = ip_match.group(1).split(':')[-1]
                break
            elif "error" in log.lower():
                last_error = log.strip()
                # Try to extract user from error log
                match = re.search(r"user: ([^ ]+)", log, re.IGNORECASE)
                if match:
                    last_error_user = match.group(1)
                else:
                    # Try to extract IP
                    ip_match = re.search(r'([0-9:.]+) - -', log)
                    if ip_match:
                        last_error_user = ip_match.group(1).split(':')[-1]
                break

    # Build human readable output
    log_text = Text()
    if downloads:
        log_text.append("Latest Downloads:\n", style="bold green")
        for idx, (content, user, timestamp) in enumerate(downloads, 1):
            # Handle different types of activity
            if user == "system":
                if timestamp == "completed":
                    log_text.append(f"  {idx}. ", style="white")
                    log_text.append(f"{content}", style="cyan")
                    log_text.append(" ✓ completed", style="green")
                    log_text.append("\n")
                elif timestamp == "downloading":
                    log_text.append(f"  {idx}. ", style="white")
                    log_text.append(f"{content}", style="cyan")
                    log_text.append(" ⏬ downloading", style="yellow")
                    log_text.append("\n")
                elif timestamp == "converted":
                    log_text.append(f"  {idx}. ", style="white")
                    log_text.append(f"{content}", style="cyan")
                    log_text.append(" 🔄 converted", style="blue")
                    log_text.append("\n")
                else:
                    log_text.append(f"  {idx}. ", style="white")
                    log_text.append(f"{content}", style="cyan")
                    log_text.append(f" {timestamp}", style="white")
                    log_text.append("\n")
            else:
                # User-initiated downloads
                display_user = user.split('.')[-1] if '.' in user else user[:10]
                
                if timestamp != "recent":
                    try:
                        if '/' in timestamp and ':' in timestamp:
                            time_part = timestamp.split()[0]
                            display_time = time_part.split(':')[1:3]
                            time_str = ":".join(display_time)
                        else:
                            time_str = timestamp[-8:] if len(timestamp) > 8 else timestamp
                    except:
                        time_str = "recent"
                else:
                    time_str = "recent"
                
                log_text.append(f"  {idx}. ", style="white")
                log_text.append(f"{content}", style="cyan")
                log_text.append(" by ", style="white")
                log_text.append(f"{display_user}", style="magenta")
                log_text.append(" at ", style="white")
                log_text.append(f"{time_str}", style="yellow")
                log_text.append("\n")
    else:
        log_text.append("No recent downloads found.\n", style="dim")
        log_text.append("Looking for: POST /download, [download] progress, INFO messages\n", style="dim")

    if last_error:
        log_text.append("\nLast Error:\n", style="bold red")
        log_text.append(f"  {last_error}\n", style="red")
        if last_error_user:
            log_text.append(f"  User affected: [magenta]{last_error_user}[/magenta]\n")
    else:
        log_text.append("\nNo errors found in recent logs.\n", style="dim")

    # Show filtered recent log lines (excluding health checks)
    log_text.append("\nRecent Activity:\n", style="bold yellow")
    filtered_logs = [log for log in logs[-10:] if not any(hc in log for hc in ["GET /health", "GET /healthz"])]
    
    if filtered_logs:
        for log in filtered_logs[-3:]:  # Show last 3 non-health-check logs
            # Truncate very long log lines
            display_log = log[:80] + "..." if len(log) > 80 else log
            log_text.append(f"  {display_log}\n", style="white")
    else:
        log_text.append("  Only health check requests in recent logs\n", style="dim")

    return Panel(log_text, title=title, border_style="yellow")

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

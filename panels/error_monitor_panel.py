#!/usr/bin/env python3
"""
Enhanced Error Tracking for Dashboard Services
Provides better error capture, storage, and display functionality
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
import sys
from pathlib import Path

# Import configuration
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    TAILSCALE_HOSTNAME,
    VIDEO_EXTERNAL_URL,
    INSTAGRAM_EXTERNAL_URL,
    VIDEO_FUNNEL_PATH,
    INSTAGRAM_FUNNEL_PATH,
)


class ErrorTracker:
    """Track and manage errors from both video transcoder and Instagram downloader"""
    
    def __init__(self):
        self.base_url = f"https://{TAILSCALE_HOSTNAME}" if TAILSCALE_HOSTNAME else "http://localhost"
        self.error_cache = {
            'video_transcoder': [],
            'instagram_downloader': []
        }
        self.last_error_check = {
            'video_transcoder': None,
            'instagram_downloader': None
        }
    
    def get_video_transcoder_errors(self) -> List[Dict]:
        """Get recent errors from video transcoder"""
        try:
            response = requests.get(f"{self.base_url}{VIDEO_FUNNEL_PATH}/logs", timeout=10)
            if response.status_code == 200:
                data = response.json()
                logs = data.get('logs', [])  # Fix: Extract logs array from response
                errors = []
                
                for log in logs:
                    status = log.get('status', '')
                    if status in ['failed', 'error']:
                        error_data = {
                            'timestamp': log.get('timestamp', ''),
                            'user': log.get('user', 'unknown'),
                            'filename': log.get('filename', 'unknown'),
                            'error': log.get('error', 'Unknown error'),
                            'status': status,
                            'duration': log.get('duration', 0),
                            'device': log.get('device', 'unknown')
                        }
                        errors.append(error_data)
                
                # Sort by timestamp (newest first)
                errors.sort(key=lambda x: x['timestamp'], reverse=True)
                self.error_cache['video_transcoder'] = errors[:20]  # Keep last 20 errors
                self.last_error_check['video_transcoder'] = datetime.now()
                return errors[:10]  # Return last 10 for display
                
        except Exception as e:
            print(f"Error fetching video transcoder errors: {e}")
        
        return []
    
    def get_instagram_downloader_errors(self) -> List[Dict]:
        """Get recent errors from Instagram downloader"""
        try:
            response = requests.get(f"{self.base_url}{INSTAGRAM_FUNNEL_PATH}/logs", timeout=10)
            if response.status_code == 200:
                data = response.json()
                logs = data.get('logs', [])
                errors = []
                
                for log in logs:
                    status = log.get('status', '')
                    success = log.get('success', True)
                    
                    if status == 'failed' or not success:
                        error_data = {
                            'timestamp': log.get('timestamp', ''),
                            'url': log.get('url', 'unknown'),
                            'filename': log.get('filename', 'unknown'),
                            'error': log.get('error', log.get('message', 'Unknown error')),
                            'status': status,
                            'duration': log.get('duration', 0)
                        }
                        errors.append(error_data)
                
                # Sort by timestamp (newest first)
                errors.sort(key=lambda x: x['timestamp'], reverse=True)
                self.error_cache['instagram_downloader'] = errors[:20]  # Keep last 20 errors
                self.last_error_check['instagram_downloader'] = datetime.now()
                return errors[:10]  # Return last 10 for display
                
        except Exception as e:
            print(f"Error fetching Instagram downloader errors: {e}")
        
        return []
    
    def get_error_summary(self) -> Dict:
        """Get a summary of recent errors for both services"""
        video_errors = self.get_video_transcoder_errors()
        instagram_errors = self.get_instagram_downloader_errors()
        
        # Count errors in the last 24 hours
        now = datetime.now()
        cutoff = now - timedelta(hours=24)
        
        recent_video_errors = 0
        recent_instagram_errors = 0
        
        for error in video_errors:
            try:
                if error['timestamp']:
                    error_time = datetime.fromisoformat(error['timestamp'].replace('Z', '+00:00'))
                    if error_time.replace(tzinfo=None) > cutoff:
                        recent_video_errors += 1
            except:
                continue
        
        for error in instagram_errors:
            try:
                if error['timestamp']:
                    error_time = datetime.fromisoformat(error['timestamp'].replace('Z', '+00:00'))
                    if error_time.replace(tzinfo=None) > cutoff:
                        recent_instagram_errors += 1
            except:
                continue
        
        return {
            'video_transcoder': {
                'total_errors': len(video_errors),
                'recent_errors': recent_video_errors,
                'latest_errors': video_errors[:3]
            },
            'instagram_downloader': {
                'total_errors': len(instagram_errors),
                'recent_errors': recent_instagram_errors,
                'latest_errors': instagram_errors[:3]
            }
        }
    
    def create_error_panel(self) -> Panel:
        """Create a panel showing recent errors from both services"""
        summary = self.get_error_summary()
        
        table = Table(show_header=True, header_style="bold red", padding=(0, 1), box=box.ROUNDED)
        table.add_column("Service", style="cyan", width=20)
        table.add_column("24h Errors", style="red", width=10)
        table.add_column("Latest Error", style="yellow", width=40)
        table.add_column("Time", style="dim", width=10)
        
        # Video Transcoder errors
        video_summary = summary['video_transcoder']
        if video_summary['latest_errors']:
            latest = video_summary['latest_errors'][0]
            error_msg = latest['error'][:37] + "..." if len(latest['error']) > 40 else latest['error']
            try:
                time_str = datetime.fromisoformat(latest['timestamp'].replace('Z', '+00:00')).strftime('%H:%M:%S')
            except:
                time_str = "Unknown"
            
            table.add_row(
                "📹 Video Transcoder",
                str(video_summary['recent_errors']),
                error_msg,
                time_str
            )
        else:
            table.add_row("📹 Video Transcoder", "0", "No recent errors", "")
        
        # Instagram Downloader errors
        instagram_summary = summary['instagram_downloader']
        if instagram_summary['latest_errors']:
            latest = instagram_summary['latest_errors'][0]
            error_msg = latest['error'][:37] + "..." if len(latest['error']) > 40 else latest['error']
            try:
                time_str = datetime.fromisoformat(latest['timestamp'].replace('Z', '+00:00')).strftime('%H:%M:%S')
            except:
                time_str = "Unknown"
            
            table.add_row(
                "📱 Instagram Downloader",
                str(instagram_summary['recent_errors']),
                error_msg,
                time_str
            )
        else:
            table.add_row("📱 Instagram Downloader", "0", "No recent errors", "")
        
        # Overall status
        total_recent_errors = video_summary['recent_errors'] + instagram_summary['recent_errors']
        
        if total_recent_errors == 0:
            border_style = "green"
            title = "🟢 Error Monitor - All Clear"
        elif total_recent_errors < 5:
            border_style = "yellow"
            title = f"🟡 Error Monitor - {total_recent_errors} Recent Errors"
        else:
            border_style = "red"
            title = f"🔴 Error Monitor - {total_recent_errors} Recent Errors"
        
        return Panel(table, title=title, border_style=border_style)


# Global error tracker instance
error_tracker = ErrorTracker()


def create_error_monitor_panel(monitor) -> Panel:
    """Create the error monitoring panel for the dashboard"""
    try:
        # Get recent activity from both services
        video_activity = get_recent_video_activity()
        instagram_activity = get_recent_instagram_activity()
        
        # Create a more informative panel
        table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
        table.add_column("Service", style="cyan", width=14)
        table.add_column("Status", style="green", width=8)
        table.add_column("Last Activity", style="yellow", width=25)
        table.add_column("Issues", style="red", width=8)
        
        # Video Transcoder Status
        video_issues = len([a for a in video_activity if a.get('status') == 'failed'])
        video_status = "🔴 Issues" if video_issues > 0 else "🟢 OK"
        video_last = video_activity[0] if video_activity else None
        video_activity_str = "No recent activity"
        
        if video_last:
            timestamp = video_last.get('timestamp', '')
            user = video_last.get('user', 'unknown')
            status = video_last.get('status', 'unknown')
            
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
            except:
                time_str = timestamp[-8:] if len(timestamp) >= 8 else 'unknown'
            
            video_activity_str = f"{time_str} {user} ({status})"
        
        table.add_row(
            "📹 Video Transcoder",
            video_status,
            video_activity_str,
            str(video_issues) if video_issues > 0 else "0"
        )
        
        # Instagram Downloader Status
        instagram_issues = len([a for a in instagram_activity if not a.get('success', True)])
        instagram_status = "🔴 Issues" if instagram_issues > 0 else "🟢 OK"
        instagram_last = instagram_activity[0] if instagram_activity else None
        instagram_activity_str = "No recent activity"
        
        if instagram_last:
            timestamp = instagram_last.get('timestamp', '')
            url = instagram_last.get('url', 'unknown')
            status = instagram_last.get('status', 'unknown')
            
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
            except:
                time_str = timestamp[-8:] if len(timestamp) >= 8 else 'unknown'
            
            # Extract post ID from URL
            post_id = "unknown"
            if '/p/' in url:
                post_id = url.split('/p/')[-1].split('/')[0][:8]
            
            instagram_activity_str = f"{time_str} {post_id} ({status})"
        
        table.add_row(
            "📱 Instagram Downloader",
            instagram_status,
            instagram_activity_str,
            str(instagram_issues) if instagram_issues > 0 else "0"
        )
        
        # System Health
        system_issues = 0
        try:
            # Check if services are responding using config URLs
            video_health = requests.get(f"{VIDEO_EXTERNAL_URL}/healthz", timeout=5)
            instagram_health = requests.get(f"{INSTAGRAM_EXTERNAL_URL}/health", timeout=5)
            
            if video_health.status_code != 200:
                system_issues += 1
            if instagram_health.status_code != 200:
                system_issues += 1
        except:
            system_issues += 1
        
        system_status = "🔴 Issues" if system_issues > 0 else "🟢 OK"
        system_activity = "All services responding" if system_issues == 0 else f"{system_issues} services down"
        
        table.add_row(
            "⚙️ System Health",
            system_status,
            system_activity,
            str(system_issues)
        )
        
        # Determine overall status
        total_issues = video_issues + instagram_issues + system_issues
        
        if total_issues == 0:
            title = "🟢 Error Monitor - All Systems OK"
            border_style = "green"
        elif total_issues <= 2:
            title = f"🟡 Error Monitor - {total_issues} Issues"
            border_style = "yellow"
        else:
            title = f"🔴 Error Monitor - {total_issues} Issues"
            border_style = "red"
        
        return Panel(table, title=title, border_style=border_style)
        
    except Exception as e:
        # Fallback error panel
        return Panel(
            f"❌ Error Monitor Unavailable\nError: {str(e)}",
            title="🔴 Error Monitor",
            border_style="red"
        )


def get_recent_video_activity():
    """Get recent video transcoder activity"""
    try:
        response = requests.get(f"{VIDEO_EXTERNAL_URL}/logs", timeout=5)
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            return logs[:10]  # Last 10 activities
    except:
        pass
    return []


def get_recent_instagram_activity():
    """Get recent Instagram downloader activity"""
    try:
        response = requests.get(f"{INSTAGRAM_EXTERNAL_URL}/logs", timeout=5)
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            return logs[:10]  # Last 10 activities
    except:
        pass
    return []

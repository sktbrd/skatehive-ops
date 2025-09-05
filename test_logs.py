#!/usr/bin/env python3
"""
Test script to verify video-worker log parsing
"""

import sys
import os
sys.path.append('/home/pi/skatehive-ops')

from monitors.service_monitor import ServiceMonitor
from panels.logs_panel import create_logs_panel

# Create monitor and get video-worker logs
monitor = ServiceMonitor()
print("Testing video-worker log parsing...")
print()

# Get logs
logs = monitor.get_recent_logs("video-worker", 10)
print("Recent video-worker logs:")
for i, log in enumerate(logs[-5:]):  # Show last 5 logs
    print(f"{i+1}. {log}")
print()

# Test the panel creation
panel = create_logs_panel(monitor, "video-worker", "Video Worker Logs")
print("Generated panel content:")
print("=" * 50)
print(panel.renderable)
print("=" * 50)

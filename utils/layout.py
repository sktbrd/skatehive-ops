#!/usr/bin/env python3
"""
Layout Utilities
Functions for creating dashboard layouts and panels
"""

from datetime import datetime
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align


def create_dashboard_layout() -> Layout:
    """Create the dashboard layout"""
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    
    layout["left"].split_column(
        Layout(name="internet", size=11),
        Layout(name="services", size=12),
        Layout(name="hive_stats", size=12)
    )
    
    layout["right"].split_column(
        Layout(name="video_worker_logs", size=10),
        Layout(name="ytipfs_logs", size=10)
    )
    
    return layout


def create_header_panel() -> Panel:
    """Create header panel"""
    title = Text("🛠️  SkatehiveOps Dashboard", style="bold magenta")
    subtitle = Text(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
    
    header_text = Align.center(title + "\n" + subtitle)
    return Panel(header_text, style="bright_blue")


def create_footer_panel() -> Panel:
    """Create footer panel"""
    footer_text = Text("Press Ctrl+C to exit | Auto-refresh every 10s | Speed test every 5min", 
                      style="dim", justify="center")
    return Panel(footer_text, style="bright_black")

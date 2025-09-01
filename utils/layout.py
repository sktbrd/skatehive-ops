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
    """Create the dashboard layout with better proportions"""
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="main"),
        Layout(name="footer", size=2)
    )
    
    layout["main"].split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=3)
    )
    
    layout["left"].split_column(
        Layout(name="internet", size=7),
        Layout(name="services", size=7),
        Layout(name="hive_stats", size=8)
    )
    
    layout["right"].split_column(
        Layout(name="top_logs"),
        Layout(name="bottom_logs")
    )
    
    return layout


def create_header_panel() -> Panel:
    """Create header panel with clean branding"""
    content = """
🛠️ SKATEHIVE OPS DASHBOARD 🛠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Updated: {time} | Monitoring: Video Worker • YTIPFS Worker • Hive Community
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".format(time=datetime.now().strftime('%H:%M:%S'))
    
    return Panel(content.strip(), style="bold bright_blue", border_style="cyan")


def create_footer_panel() -> Panel:
    """Create footer panel"""
    footer_text = Text("Press Ctrl+C to exit | Auto-refresh every 10s | Speed test every 15min", 
                      style="dim", justify="center")
    return Panel(footer_text, style="bright_black")

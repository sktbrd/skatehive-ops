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
    """Create the dashboard layout with optimal space distribution"""
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=2)
    )
    
    layout["main"].split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=5)
    )
    
    layout["left"].split_column(
        Layout(name="internet", size=8),
        Layout(name="services", size=7),
        Layout(name="hive_stats", size=12)
    )
    
    layout["right"].split_column(
        Layout(name="video_transcoder", size=18),
        Layout(name="top_logs", size=9),
        Layout(name="bottom_logs", size=9)
    )
    
    return layout


def create_header_panel() -> Panel:
    """Create header panel with clean branding"""
    content = f"🛠️ SKATEHIVE OPS DASHBOARD 🛠️ | Updated: {datetime.now().strftime('%H:%M:%S')} | Monitoring: Video Worker • YTIPFS Worker • Hive Community"
    
    return Panel(content, style="bold bright_blue", border_style="cyan")


def create_footer_panel() -> Panel:
    """Create footer panel"""
    footer_text = Text("Press Ctrl+C to exit | Auto-refresh every 10s | Speed test every 15min", 
                      style="dim", justify="center")
    return Panel(footer_text, style="bright_black")

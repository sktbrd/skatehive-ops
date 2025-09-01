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
        Layout(name="footer", size=2)
    )
    
    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    
    layout["left"].split_column(
        Layout(name="internet", size=8),
        Layout(name="services", size=6),
        Layout(name="hive_stats", size=10)
    )
    
    layout["right"].split_column(
        Layout(name="video_worker_logs"),
        Layout(name="ytipfs_logs")
    )
    
    return layout


def create_header_panel() -> Panel:
    """Create header panel with ASCII art"""
    ascii_art = """
🛠️ SKATEHIVE OPS DASHBOARD 🛠️    ╔══════════════════════════════╗
                               ║  ╔══╗ ║  ╔══╗ ╔══════╗ ╔══════╗ ║
Updated: {time}                ║  ║  ║ ║  ║  ║    ║    ║      ║ ║
                               ║  ╚══╝ ╠══╣  ║    ║    ╠══════╣ ║
Monitoring Services            ║       ║  ║  ║    ║    ║      ║ ║
                               ╚═══════════════════════════════╝
""".format(time=datetime.now().strftime('%H:%M:%S'))
    
    return Panel(ascii_art, style="bright_blue", border_style="cyan")


def create_footer_panel() -> Panel:
    """Create footer panel"""
    footer_text = Text("Press Ctrl+C to exit | Auto-refresh every 10s | Speed test every 15min", 
                      style="dim", justify="center")
    return Panel(footer_text, style="bright_black")

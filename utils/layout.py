#!/usr/bin/env python3
"""
L    layout["left"].split_column(
        Layout(name="internet", size=9),
        Layout(name="services", size=10),
        Layout(name="hive_stats", size=15)
    ) Utilities
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
        Layout(name="header", size=25),
        Layout(name="main"),
        Layout(name="footer", size=2)
    )
    
    layout["header"].split_row(
        Layout(name="ascii_art"),
        Layout(name="header_info", ratio=1)
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


def create_ascii_art_panel() -> Panel:
    """Create ASCII art panel with skatehive logo"""
    ascii_art = """
  ╔═══════════════════════════════════════════════════════════╗
  ║                                                           ║
  ║     ********    **.     .**      ******    ************   ║
  ║     ********    **.     .**      ******    ************   ║
  ║   **            **.   =*+      **      **        **      ║
  ║     ******      ******-        **********        **      ║
  ║           **    **.   =*+      **      **        **      ║
  ║   ********      **.     :**    **      **        **      ║
  ║   ********      **.     :**    **      **        **      ║
  ║                                                           ║
  ║   ****        **    +**********    ****          ****    ║
  ║   ****        **    +**********    ****          ****    ║
  ║   ****        **        .****      ****          ****    ║
  ║   ****        **        .****      ****          ****    ║
  ║   **************        .****          ****  ****        ║
  ║   **************        .****          ****  ****        ║
  ║   ****        **    +**********            **            ║
  ║   ****        **    +**********            **            ║
  ║                                                           ║
  ╚═══════════════════════════════════════════════════════════╝
"""
    return Panel(Text(ascii_art, style="bright_blue"), border_style="cyan")


def create_header_info_panel() -> Panel:
    """Create header info panel"""
    lines = [
        "🛠️ SkatehiveOps Dashboard",
        "",
        f"Updated: {datetime.now().strftime('%H:%M:%S')}",
        "",
        "Monitoring Services:",
        "• Video Worker Status",
        "• YTIPFS Worker Status", 
        "• Internet Connection",
        "• Hive Community Stats",
        "",
        "─" * 25,
        "",
        "Press Ctrl+C to exit"
    ]
    
    content = "\n".join(lines)
    return Panel(content, style="bright_blue", title="[bold magenta]Info[/bold magenta]")


def create_header_panel() -> Panel:
    """Create header panel - kept for backward compatibility"""
    return create_header_info_panel()


def create_footer_panel() -> Panel:
    """Create footer panel"""
    footer_text = Text("Press Ctrl+C to exit | Auto-refresh every 10s | Speed test every 15min", 
                      style="dim", justify="center")
    return Panel(footer_text, style="bright_black")

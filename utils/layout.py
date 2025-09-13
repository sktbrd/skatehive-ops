#!/usr/bin/env python3
"""
Layout Utilities
Functions for creating dashboard layouts and panels with responsive design
"""

import os
import shutil
from datetime import datetime
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.console import Console

console = Console()

def get_terminal_size():
    """Get current terminal size"""
    try:
        size = shutil.get_terminal_size()
        return size.columns, size.lines
    except:
        return 80, 24  # Fallback size

def create_responsive_layout() -> Layout:
    """Create responsive layout based on terminal size"""
    width, height = get_terminal_size()
    
    layout = Layout()
    
    # Adjust layout based on terminal size
    if height < 30:
        # Small terminal - compact layout
        layout.split_column(
            Layout(name="header", size=1),
            Layout(name="main"),
            Layout(name="footer", size=1)
        )
        
        # Single column for small screens
        if width < 120:
            layout["main"].split_column(
                Layout(name="services", size=8),
                Layout(name="error_monitor", size=10),
                Layout(name="logs", size=15)
            )
        else:
            # Two columns for medium screens
            layout["main"].split_row(
                Layout(name="left", ratio=1),
                Layout(name="right", ratio=2)
            )
            layout["left"].split_column(
                Layout(name="services", size=8),
                Layout(name="error_monitor", size=8)
            )
            layout["right"].update(Layout(name="logs"))
    
    elif height < 50:
        # Medium terminal - standard layout
        layout.split_column(
            Layout(name="header", size=2),
            Layout(name="main"),
            Layout(name="footer", size=1)
        )
        
        layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=3)
        )
        
        layout["left"].split_column(
            Layout(name="internet", size=6),
            Layout(name="services", size=8),
            Layout(name="error_monitor", size=8),
            Layout(name="instagram", size=10)
        )
        
        layout["right"].split_column(
            Layout(name="video_transcoder", size=12),
            Layout(name="video_logs", size=8),
            Layout(name="instagram_logs", size=10)
        )
    
    else:
        # Large terminal - full layout
        layout.split_column(
            Layout(name="header", size=2),
            Layout(name="main"),
            Layout(name="footer", size=1)
        )
        
        layout["main"].split_row(
            Layout(name="left", ratio=3),
            Layout(name="right", ratio=4)
        )
        
        layout["left"].split_column(
            Layout(name="internet", size=7),
            Layout(name="nas", size=7),
            Layout(name="services", size=8),
            Layout(name="error_monitor", size=10),
            Layout(name="instagram", size=12),
            Layout(name="hive_stats", size=10)
        )
        
        layout["right"].split_column(
            Layout(name="video_transcoder", size=15),
            Layout(name="video_logs", size=10),
            Layout(name="instagram_logs", size=12)
        )
    
    return layout


def create_fullscreen_layout() -> Layout:
    """Create a full-screen layout optimized for error monitoring and logs"""
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=2),
        Layout(name="main"),
        Layout(name="footer", size=1)
    )
    
    # Full width main area
    layout["main"].split_column(
        Layout(name="services_row", size=6),
        Layout(name="error_monitor", size=15),  # Large error monitor
        Layout(name="logs_row")  # Flexible logs area
    )
    
    # Top row with services
    layout["services_row"].split_row(
        Layout(name="internet", ratio=1),
        Layout(name="nas", ratio=1),
        Layout(name="services", ratio=1),
        Layout(name="hive_stats", ratio=2)
    )
    
    # Bottom row with logs
    layout["logs_row"].split_row(
        Layout(name="video_transcoder", ratio=1),
        Layout(name="video_logs", ratio=1),
        Layout(name="instagram", ratio=1),
        Layout(name="instagram_logs", ratio=1)
    )
    
    return layout


def create_dashboard_layout() -> Layout:
    """Legacy function - use create_responsive_layout() for better experience"""
    return create_responsive_layout()


def create_responsive_header_panel() -> Panel:
    """Create responsive header based on terminal width"""
    width, _ = get_terminal_size()
    
    if width < 80:
        # Compact header for narrow terminals
        content = f"🛠️ SKATEHIVE OPS | {datetime.now().strftime('%H:%M:%S')}"
    elif width < 120:
        # Medium header
        content = f"🛠️ SKATEHIVE OPS DASHBOARD | {datetime.now().strftime('%H:%M:%S')} | NAS • Video • Instagram • Hive"
    else:
        # Full header
        content = f"🛠️ SKATEHIVE OPS DASHBOARD 🛠️ | Updated: {datetime.now().strftime('%H:%M:%S')} | Monitoring: NAS • Video Worker • YTIPFS Worker • Hive Community"
    
    return Panel(content, style="bold bright_blue", border_style="cyan")


def create_header_panel() -> Panel:
    """Create compact header panel - legacy function"""
    return create_responsive_header_panel()


def create_responsive_footer_panel() -> Panel:
    """Create responsive footer based on terminal width"""
    width, _ = get_terminal_size()
    
    if width < 80:
        footer_text = Text("Ctrl+C: Exit", style="dim", justify="center")
    else:
        footer_text = Text("Ctrl+C: Exit | Auto-refresh: 10s", style="dim", justify="center")
    
    return Panel(footer_text, style="bright_black")


def create_footer_panel() -> Panel:
    """Create compact footer panel - legacy function"""
    return create_responsive_footer_panel()

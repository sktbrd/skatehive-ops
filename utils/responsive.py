#!/usr/bin/env python3
"""
Responsive Panel Utilities
Functions to create panels that adapt to terminal size
"""

import shutil
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box


def get_terminal_width():
    """Get current terminal width"""
    try:
        size = shutil.get_terminal_size()
        return size.columns
    except:
        return 80  # Fallback width


def create_responsive_table(title: str, headers: list, max_width: int = None) -> Table:
    """Create a table that adapts to terminal size"""
    terminal_width = get_terminal_width()
    
    if max_width is None:
        max_width = terminal_width // 4  # Quarter of screen for side panels
    
    # Adjust table style based on available width
    if terminal_width < 80:
        # Very compact table for narrow terminals
        table = Table(show_header=True, header_style="bold cyan", padding=(0, 0), box=None)
        # Use shorter column widths
        col_width = max(8, max_width // len(headers))
    elif terminal_width < 120:
        # Compact table for medium terminals
        table = Table(show_header=True, header_style="bold cyan", padding=(0, 1), box=None)
        col_width = max(10, max_width // len(headers))
    else:
        # Full table for wide terminals
        table = Table(show_header=True, header_style="bold cyan", padding=(0, 1), box=box.ROUNDED)
        col_width = max(12, max_width // len(headers))
    
    # Add columns with responsive width
    for i, header in enumerate(headers):
        if i == 0:
            # First column slightly wider
            table.add_column(header, style="cyan", width=col_width + 2)
        elif i == len(headers) - 1:
            # Last column takes remaining space
            table.add_column(header, style="white")
        else:
            table.add_column(header, style="yellow", width=col_width)
    
    return table


def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to fit in available space"""
    if len(text) <= max_length:
        return text
    elif max_length <= 3:
        return text[:max_length]
    else:
        return text[:max_length-3] + "..."


def create_responsive_services_table() -> Table:
    """Create responsive services table"""
    terminal_width = get_terminal_width()
    
    if terminal_width < 80:
        # Very compact for small screens
        table = Table(show_header=True, header_style="bold cyan", padding=(0, 0), box=None)
        table.add_column("Service", style="cyan", width=8)
        table.add_column("Status", style="green", width=6)
        table.add_column("Time", style="yellow", width=6)
    elif terminal_width < 120:
        # Medium layout
        table = Table(show_header=True, header_style="bold cyan", padding=(0, 1), box=None)
        table.add_column("Service", style="cyan", width=12)
        table.add_column("Status", style="green", width=8)
        table.add_column("Response", style="yellow", width=8)
        table.add_column("Details", style="magenta", width=20)
    else:
        # Full layout
        table = Table(show_header=True, header_style="bold cyan", padding=(0, 1), box=None)
        table.add_column("Service", style="cyan", width=14)
        table.add_column("Status", style="green", width=8)
        table.add_column("Response", style="yellow", width=8)
        table.add_column("Details", style="magenta", width=25)
        table.add_column("CPU", style="red", width=6)
        table.add_column("Memory", style="blue", width=8)
    
    return table


def create_responsive_error_table() -> Table:
    """Create responsive error monitor table"""
    terminal_width = get_terminal_width()
    
    if terminal_width < 80:
        # Compact error table
        table = Table(show_header=True, header_style="bold red", padding=(0, 0), box=None)
        table.add_column("Service", style="cyan", width=8)
        table.add_column("Status", style="red", width=6)
        table.add_column("Last Error", style="white", width=20)
    elif terminal_width < 120:
        # Medium error table
        table = Table(show_header=True, header_style="bold red", padding=(0, 1), box=None)
        table.add_column("Service", style="cyan", width=12)
        table.add_column("Status", style="red", width=8)
        table.add_column("Last Activity", style="yellow", width=15)
        table.add_column("Issues", style="red", width=8)
    else:
        # Full error table
        table = Table(show_header=True, header_style="bold red", padding=(0, 1), box=box.ROUNDED)
        table.add_column("Service", style="cyan", width=14)
        table.add_column("Status", style="green", width=8)
        table.add_column("Last Activity", style="yellow", width=18)
        table.add_column("Issues", style="red", width=8)
    
    return table


def format_responsive_text(text: str, panel_type: str = "default") -> str:
    """Format text responsively based on terminal size and panel type"""
    terminal_width = get_terminal_width()
    
    # Calculate available width based on panel type
    if panel_type == "side":
        available_width = terminal_width // 4 - 4  # Side panel width minus borders
    elif panel_type == "main":
        available_width = (terminal_width * 3) // 4 - 4  # Main panel width minus borders
    else:
        available_width = terminal_width // 2 - 4  # Default panel width
    
    # Split long lines and wrap text
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        if len(line) <= available_width:
            formatted_lines.append(line)
        else:
            # Break long lines
            while len(line) > available_width:
                # Try to break at space
                break_point = line.rfind(' ', 0, available_width)
                if break_point == -1:
                    break_point = available_width
                
                formatted_lines.append(line[:break_point])
                line = line[break_point:].lstrip()
            
            if line:
                formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)


def create_responsive_panel(content, title: str, border_style: str = "green", panel_type: str = "default") -> Panel:
    """Create a responsive panel that adapts its content to terminal size"""
    terminal_width = get_terminal_width()
    
    # Format content responsively
    if isinstance(content, str):
        content = format_responsive_text(content, panel_type)
    
    # Adjust title length
    if terminal_width < 80 and len(title) > 15:
        title = title[:12] + "..."
    elif terminal_width < 120 and len(title) > 25:
        title = title[:22] + "..."
    
    return Panel(content, title=title, border_style=border_style)
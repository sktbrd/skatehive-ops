#!/usr/bin/env python3
"""
Test script to demonstrate responsive dashboard behavior across different terminal sizes.
"""

import os
import sys
import asyncio
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.layout import get_terminal_size, create_responsive_layout
from utils.responsive import create_responsive_table, format_responsive_text
from monitors.service_monitor import ServiceMonitor

console = Console()

def create_demo_content():
    """Create demo content to test responsive behavior"""
    width, height = get_terminal_size()
    
    # Create responsive tables
    small_table = create_responsive_table(
        title="Services",
        headers=["Service", "Status"],
        rows=[
            ["NAS", "🟢 Online"],
            ["Instagram", "🟢 Online"],
            ["Video", "🟢 Online"]
        ]
    )
    
    large_table = create_responsive_table(
        title="Detailed Services",
        headers=["Service", "Status", "Response Time", "Last Check", "Endpoint"],
        rows=[
            ["NAS", "🟢 Online", "45ms", "12:34:56", "nas.example.com"],
            ["Instagram Downloader", "🟢 Online", "120ms", "12:34:55", "instagram.example.com"],
            ["Video Transcoder", "🟡 Slow", "850ms", "12:34:54", "video.example.com"]
        ]
    )
    
    # Format text responsively
    description = format_responsive_text(
        "This dashboard automatically adapts to your terminal size. " +
        "When the terminal is small, it shows a compact layout with essential information. " +
        "In larger terminals, it displays detailed views with comprehensive monitoring data. " +
        "Try resizing your terminal to see the responsive behavior in action!"
    )
    
    return {
        "small_table": small_table,
        "large_table": large_table,
        "description": description,
        "terminal_size": f"Terminal: {width}x{height}"
    }

async def test_responsive_dashboard():
    """Test the responsive dashboard with different layouts"""
    console.print("[bold blue]🔧 Responsive Dashboard Test[/bold blue]")
    console.print("Resize your terminal to see different layouts!\n")
    
    try:
        while True:
            width, height = get_terminal_size()
            
            # Create responsive layout
            layout = create_responsive_layout()
            demo_content = create_demo_content()
            
            # Update layout with demo content
            if "header" in layout:
                layout["header"].update(Panel(
                    f"[bold]Responsive Dashboard Demo[/bold]\n{demo_content['terminal_size']}",
                    title="📊 Header",
                    border_style="blue"
                ))
            
            # Show different content based on layout type
            if width < 80:  # Small terminal
                if "services" in layout:
                    layout["services"].update(demo_content["small_table"])
                if "main" in layout:
                    layout["main"].update(Panel(
                        demo_content["description"],
                        title="💡 Compact View",
                        border_style="yellow"
                    ))
            else:  # Large terminal
                if "services" in layout:
                    layout["services"].update(demo_content["large_table"])
                if "instagram" in layout:
                    layout["instagram"].update(Panel(
                        "📱 Instagram Downloader\nDetailed monitoring panel",
                        title="Instagram Service",
                        border_style="green"
                    ))
                if "video_transcoder" in layout:
                    layout["video_transcoder"].update(Panel(
                        "🎥 Video Transcoder\nDetailed monitoring panel",
                        title="Video Service", 
                        border_style="purple"
                    ))
                if "main" in layout:
                    layout["main"].update(Panel(
                        demo_content["description"],
                        title="💡 Full View",
                        border_style="cyan"
                    ))
            
            if "footer" in layout:
                layout["footer"].update(Panel(
                    f"[dim]Press Ctrl+C to exit • Updates every 2 seconds • Layout: {width}x{height}[/dim]",
                    border_style="dim"
                ))
            
            # Display the layout
            console.clear()
            console.print(layout)
            
            await asyncio.sleep(2)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Responsive test complete![/yellow]")

if __name__ == "__main__":
    asyncio.run(test_responsive_dashboard())
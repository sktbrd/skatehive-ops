#!/usr/bin/env python3
"""
Layout Space Optimization Test
Shows the improvements in space utilization
"""

from utils.layout import create_dashboard_layout, create_fullscreen_layout
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

def show_layout_comparison():
    console = Console()
    
    # Create comparison table
    table = Table(title="🎯 Dashboard Layout Optimization", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="cyan")
    table.add_column("Before", style="red")
    table.add_column("After", style="green")
    table.add_column("Change", style="yellow")
    
    # Space optimization changes
    table.add_row("Header Size", "3", "2", "⬇️ -33%")
    table.add_row("Footer Size", "2", "1", "⬇️ -50%")
    table.add_row("Left Panel Ratio", "2", "3", "⬆️ +50%")
    table.add_row("Right Panel Ratio", "5", "4", "⬇️ -20%")
    table.add_row("Error Monitor Size", "6", "12", "⬆️ +100%")
    table.add_row("Instagram Logs Size", "12", "15", "⬆️ +25%")
    table.add_row("Video Logs Size", "9", "10", "⬆️ +11%")
    
    console.print(table)
    console.print()
    
    # Benefits summary
    benefits = Panel(
        """✅ More content space (reduced header/footer)
✅ Better error visibility (doubled error monitor size)
✅ Enhanced log viewing (larger log panels)
✅ Balanced layout (better left/right ratio)
✅ Compact headers (shorter text, same info)
✅ Optional fullscreen layout available""",
        title="🚀 Optimization Benefits",
        border_style="green"
    )
    
    console.print(benefits)
    console.print()
    
    # Usage instructions
    usage = Panel(
        """Standard Layout: python3 dashboard.py
Fullscreen Mode: Available in layout.py (future enhancement)
Quick Test: python3 layout_test.py""",
        title="💡 Usage Instructions",
        border_style="blue"
    )
    
    console.print(usage)

if __name__ == "__main__":
    show_layout_comparison()
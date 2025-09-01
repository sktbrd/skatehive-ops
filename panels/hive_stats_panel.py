#!/usr/bin/env python3
"""
Hive Community Stats Panel
Displays statistics from the Hive blockchain community API
"""

from datetime import datetime
from rich.panel import Panel
from rich.table import Table


def create_hive_stats_panel(monitor) -> Panel:
    """Create Hive community stats panel"""
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan", width=20)
    table.add_column("Value", style="green", width=12)
    
    # Fetch fresh stats every 5 minutes or if no data
    if (not monitor.last_hive_stats_fetch or 
        (datetime.now() - monitor.last_hive_stats_fetch).total_seconds() > 300):
        monitor.fetch_hive_stats()
    
    if monitor.hive_stats:
        stats = monitor.hive_stats
        
        # Community Overview (most important stats first)
        table.add_row("👥 Subscribers", f"{stats.get('total_subscribers', 'N/A')}")
        table.add_row("📝 Posts", f"{stats.get('total_posts', 'N/A')}")
        table.add_row("💬 Comments", f"{stats.get('total_comments', 'N/A')}")
        
        # Recent Activity (30 days) - condensed
        table.add_row("✍️ Authors(30d)", f"{stats.get('unique_post_authors_last_30_days', 'N/A')}")
        table.add_row("💭 Comment(30d)", f"{stats.get('unique_comment_authors_last_30_days', 'N/A')}")
        
        # Payouts - most important
        try:
            total_payouts = float(stats.get('total_payouts_hbd', 0))
            table.add_row("🏆 Total HBD", f"{total_payouts:,.0f}")
        except (ValueError, TypeError):
            table.add_row("🏆 Total HBD", f"{stats.get('total_payouts_hbd', 'N/A')}")
            
        # Last updated
        if monitor.last_hive_stats_fetch:
            age = datetime.now() - monitor.last_hive_stats_fetch
            table.add_row("🕒 Updated", f"{int(age.total_seconds()//60)}m ago")
            
    elif monitor.hive_stats_error:
        # Show the actual error for debugging
        error_msg = monitor.hive_stats_error
        if len(error_msg) > 25:
            error_msg = error_msg[:22] + "..."
        table.add_row("❌ Error", error_msg)
        table.add_row("🔗 API", "hivehub.dev")
        table.add_row("📡 Check", "Network/DNS")
    else:
        table.add_row("⏳ Loading", "API call...")
    
    return Panel(table, title="🐝 Hive Stats", border_style="magenta")

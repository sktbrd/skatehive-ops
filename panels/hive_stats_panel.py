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
    table.add_column("Metric", style="cyan", width=25)
    table.add_column("Value", style="green", width=15)
    
    # Fetch fresh stats every 5 minutes or if no data
    if (not monitor.last_hive_stats_fetch or 
        (datetime.now() - monitor.last_hive_stats_fetch).total_seconds() > 300):
        monitor.fetch_hive_stats()
    
    if monitor.hive_stats:
        stats = monitor.hive_stats
        
        # Community Overview
        table.add_row("👥 Total Subscribers", f"{stats.get('total_subscribers', 'N/A')}")
        table.add_row("📝 Total Posts", f"{stats.get('total_posts', 'N/A')}")
        table.add_row("💬 Total Comments", f"{stats.get('total_comments', 'N/A')}")
        
        # Recent Activity (30 days)
        table.add_row("", "")  # Separator
        table.add_row("✍️ Authors (30d)", f"{stats.get('unique_post_authors_last_30_days', 'N/A')}")
        table.add_row("💭 Commenters (30d)", f"{stats.get('unique_comment_authors_last_30_days', 'N/A')}")
        
        # Daily Averages
        table.add_row("", "")  # Separator
        table.add_row("📊 Avg Daily Authors", f"{stats.get('average_daily_unique_post_authors', 'N/A')}")
        table.add_row("📈 Avg Daily Comments", f"{stats.get('average_daily_unique_comment_authors', 'N/A')}")
        
        # Payouts
        table.add_row("", "")  # Separator
        try:
            post_payouts = float(stats.get('post_payouts_hbd', 0))
            comment_payouts = float(stats.get('comment_payouts_hbd', 0))
            total_payouts = float(stats.get('total_payouts_hbd', 0))
            
            table.add_row("💰 Post Payouts", f"{post_payouts:,.1f} HBD")
            table.add_row("💸 Comment Payouts", f"{comment_payouts:,.1f} HBD") 
            table.add_row("🏆 Total Payouts", f"{total_payouts:,.1f} HBD")
        except (ValueError, TypeError):
            table.add_row("💰 Post Payouts", f"{stats.get('post_payouts_hbd', 'N/A')} HBD")
            table.add_row("💸 Comment Payouts", f"{stats.get('comment_payouts_hbd', 'N/A')} HBD")
            table.add_row("🏆 Total Payouts", f"{stats.get('total_payouts_hbd', 'N/A')} HBD")
            
        # Last updated
        if monitor.last_hive_stats_fetch:
            age = datetime.now() - monitor.last_hive_stats_fetch
            table.add_row("", "")  # Separator  
            table.add_row("🕒 Last Updated", f"{int(age.total_seconds()//60)}min ago")
            
    elif monitor.hive_stats_error:
        table.add_row("❌ Error", monitor.hive_stats_error[:30] + "..." if len(monitor.hive_stats_error) > 30 else monitor.hive_stats_error)
    else:
        table.add_row("⏳ Loading", "Fetching stats...")
    
    return Panel(table, title="🐝 Hive Community Stats", border_style="magenta")

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
    table = Table(show_header=True, header_style="bold cyan", padding=(0, 1), box=None)
    table.add_column("Metric", style="cyan", width=15)
    table.add_column("Value", style="green", width=12)
    
    # Fetch fresh stats every 5 minutes or if no data
    if (not monitor.last_hive_stats_fetch or 
        (datetime.now() - monitor.last_hive_stats_fetch).total_seconds() > 300):
        monitor.fetch_hive_stats()
    
    if monitor.hive_stats:
        stats = monitor.hive_stats
        
        # Community Overview
        subs = stats.get('total_subscribers', 'N/A')
        posts = stats.get('total_posts', 'N/A')
        comments = stats.get('total_comments', 'N/A')
        
        table.add_row("👥 Subscribers", f"{subs:,}" if isinstance(subs, int) else str(subs))
        table.add_row("📝 Posts", f"{posts:,}" if isinstance(posts, int) else str(posts))
        table.add_row("💬 Comments", f"{comments:,}" if isinstance(comments, int) else str(comments))
        
        # Recent Activity (30 days)
        authors_30d = stats.get('unique_post_authors_last_30_days', 'N/A')
        commenters_30d = stats.get('unique_comment_authors_last_30_days', 'N/A')
        
        table.add_row("✍️ Authors (30d)", str(authors_30d))
        table.add_row("💭 Users (30d)", str(commenters_30d))
        
        # Payouts
        try:
            total_payouts = float(stats.get('total_payouts_hbd', 0))
            table.add_row("🏆 Payouts", f"{total_payouts:,.0f} HBD")
        except (ValueError, TypeError):
            table.add_row("🏆 Payouts", f"{stats.get('total_payouts_hbd', 'N/A')} HBD")
            
        # Status
        if monitor.last_hive_stats_fetch:
            age = datetime.now() - monitor.last_hive_stats_fetch
            age_min = int(age.total_seconds()//60)
            table.add_row("🕒 Updated", f"{age_min}m ago")
            
    elif monitor.hive_stats_error:
        table.add_row("❌ Status", "API Failed")
        if "requests" in str(monitor.hive_stats_error).lower():
            table.add_row("💡 Fix", "pip install requests")
        else:
            error_short = str(monitor.hive_stats_error)[:10] + "..." if len(str(monitor.hive_stats_error)) > 10 else str(monitor.hive_stats_error)
            table.add_row("Details", error_short)
    else:
        table.add_row("⏳ Status", "Loading...")
    
    return Panel(table, title="🐝 Hive Community", border_style="magenta")

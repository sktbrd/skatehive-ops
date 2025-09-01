#!/usr/bin/env python3
"""
Hive Community Stats Panel
Displays statistics from the Hive blockchain community API
"""

from datetime import datetime
from rich.panel import Panel
from rich.table import Table


def create_hive_stats_panel(monitor) -> Panel:
    """Create Hive community stats panel with better organization"""
    table = Table(show_header=True, header_style="bold cyan", padding=(0, 1))
    table.add_column("Metric", style="cyan", width=15, no_wrap=True)
    table.add_column("Value", style="green", width=12, no_wrap=True)
    
    # Fetch fresh stats every 5 minutes or if no data
    if (not monitor.last_hive_stats_fetch or 
        (datetime.now() - monitor.last_hive_stats_fetch).total_seconds() > 300):
        monitor.fetch_hive_stats()
    
    if monitor.hive_stats:
        stats = monitor.hive_stats
        
        # Community Overview with formatting
        subs = stats.get('total_subscribers', 'N/A')
        posts = stats.get('total_posts', 'N/A')
        comments = stats.get('total_comments', 'N/A')
        
        table.add_row("👥 Subscribers", f"[bright_blue]{subs:,}[/bright_blue]" if isinstance(subs, int) else str(subs))
        table.add_row("📝 Posts", f"[bright_green]{posts:,}[/bright_green]" if isinstance(posts, int) else str(posts))
        table.add_row("💬 Comments", f"[bright_yellow]{comments:,}[/bright_yellow]" if isinstance(comments, int) else str(comments))
        
        # Recent Activity (30 days) with emphasis
        authors_30d = stats.get('unique_post_authors_last_30_days', 'N/A')
        commenters_30d = stats.get('unique_comment_authors_last_30_days', 'N/A')
        
        table.add_row("✍️ Active Authors", f"[magenta]{authors_30d}[/magenta]" if authors_30d != 'N/A' else str(authors_30d))
        table.add_row("💭 Active Users", f"[cyan]{commenters_30d}[/cyan]" if commenters_30d != 'N/A' else str(commenters_30d))
        
        # Payouts with currency formatting
        try:
            total_payouts = float(stats.get('total_payouts_hbd', 0))
            formatted_payouts = f"[bright_green]{total_payouts:,.0f}[/bright_green] HBD"
            table.add_row("🏆 Total Payouts", formatted_payouts)
        except (ValueError, TypeError):
            table.add_row("🏆 Total Payouts", f"{stats.get('total_payouts_hbd', 'N/A')} HBD")
            
        # Status indicator
        if monitor.last_hive_stats_fetch:
            age = datetime.now() - monitor.last_hive_stats_fetch
            age_min = int(age.total_seconds()//60)
            if age_min < 5:
                status_color = "bright_green"
                status_icon = "🟢"
            elif age_min < 15:
                status_color = "yellow" 
                status_icon = "🟡"
            else:
                status_color = "red"
                status_icon = "🔴"
            table.add_row("🕒 Data Age", f"[{status_color}]{status_icon} {age_min}m ago[/{status_color}]")
            
    elif monitor.hive_stats_error:
        table.add_row("❌ Status", "[red]API Failed[/red]")
        if "requests" in str(monitor.hive_stats_error).lower():
            table.add_row("💡 Solution", "[yellow]Install requests[/yellow]")
        else:
            error_short = str(monitor.hive_stats_error)[:12] + "..." if len(str(monitor.hive_stats_error)) > 12 else str(monitor.hive_stats_error)
            table.add_row("Details", f"[red]{error_short}[/red]")
    else:
        table.add_row("⏳ Status", "[yellow]Loading...[/yellow]")
    
    return Panel(table, title="🐝 Hive Community", border_style="magenta")

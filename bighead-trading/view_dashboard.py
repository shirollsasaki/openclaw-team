"""
Platform Revenue Dashboard Viewer
Quick view of current pipeline and performance
"""
import csv
from datetime import datetime, timedelta
from collections import defaultdict

def load_dashboard():
    """Load dashboard data"""
    try:
        with open('platform-revenue-dashboard.csv', 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except:
        return []

def show_pipeline():
    """Show current pipeline status"""
    data = load_dashboard()
    
    if not data:
        print("No data yet. Add jobs with: python3 add_job_manual.py")
        return
    
    print("="*70)
    print("PLATFORM REVENUE DASHBOARD")
    print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    print()
    
    # Count by status
    status_counts = defaultdict(int)
    for row in data:
        status_counts[row['Status']] += 1
    
    print("📊 PIPELINE OVERVIEW")
    print()
    print(f"  Prospecting:     {status_counts['Prospecting']:>3}")
    print(f"  Proposal Sent:   {status_counts['Proposal Sent']:>3}")
    print(f"  Negotiating:     {status_counts['Negotiating']:>3}")
    print(f"  Closed (Won):    {status_counts['Closed']:>3}")
    print(f"  Lost:            {status_counts['Lost']:>3}")
    print(f"  {'─'*30}")
    print(f"  Total:           {len(data):>3}")
    print()
    
    # Revenue
    total_revenue = sum(float(row['Revenue Amount']) for row in data if row['Revenue Amount'] and row['Revenue Amount'].replace('.','').isdigit())
    
    print("💰 REVENUE")
    print()
    print(f"  Total closed:    ${total_revenue:>8,.2f}")
    print()
    
    # By agent
    agent_revenue = defaultdict(float)
    agent_deals = defaultdict(int)
    
    for row in data:
        if row['Status'] == 'Closed' and row['Revenue Amount']:
            try:
                revenue = float(row['Revenue Amount'])
                agents = [a.strip() for a in row['Agent'].split(',')]
                for agent in agents:
                    agent_revenue[agent] += revenue / len(agents)  # Split if multiple agents
                    agent_deals[agent] += 1
            except:
                pass
    
    if agent_revenue:
        print("💼 BY AGENT")
        print()
        sorted_agents = sorted(agent_revenue.items(), key=lambda x: x[1], reverse=True)
        for agent, rev in sorted_agents:
            deals = agent_deals[agent]
            print(f"  {agent:<15} ${rev:>8,.2f}  ({deals} deal{'s' if deals != 1 else ''})")
        print()
    
    # By platform
    platform_revenue = defaultdict(float)
    platform_deals = defaultdict(int)
    
    for row in data:
        if row['Status'] == 'Closed' and row['Revenue Amount']:
            try:
                revenue = float(row['Revenue Amount'])
                platform_revenue[row['Platform']] += revenue
                platform_deals[row['Platform']] += 1
            except:
                pass
    
    if platform_revenue:
        print("🏢 BY PLATFORM")
        print()
        sorted_platforms = sorted(platform_revenue.items(), key=lambda x: x[1], reverse=True)
        for platform, rev in sorted_platforms:
            deals = platform_deals[platform]
            print(f"  {platform:<15} ${rev:>8,.2f}  ({deals} deal{'s' if deals != 1 else ''})")
        print()
    
    # Recent activity
    print("📋 RECENT ACTIVITY (Last 10)")
    print()
    
    recent = data[-10:]
    for row in recent:
        date = row['Date']
        status = row['Status']
        agent = row['Agent'][:20] if len(row['Agent']) > 20 else row['Agent']
        title = row['Lead Source'][:40] if len(row['Lead Source']) > 40 else row['Lead Source']
        platform = row['Platform']
        
        status_emoji = {
            'Prospecting': '🔍',
            'Proposal Sent': '📤',
            'Negotiating': '💬',
            'Closed': '✅',
            'Lost': '❌'
        }.get(status, '•')
        
        print(f"  {status_emoji} {date} | {platform:<12} | {agent:<15} | {title}")
    
    print()
    print("="*70)

def show_conversion_rates():
    """Show conversion rate by agent and platform"""
    data = load_dashboard()
    
    if not data:
        return
    
    print()
    print("📈 CONVERSION RATES")
    print()
    
    # By agent
    agent_stats = defaultdict(lambda: {'proposals': 0, 'closed': 0, 'lost': 0})
    
    for row in data:
        agents = [a.strip() for a in row['Agent'].split(',')]
        for agent in agents:
            if row['Proposal Sent'] == 'Y':
                agent_stats[agent]['proposals'] += 1
            if row['Status'] == 'Closed':
                agent_stats[agent]['closed'] += 1
            if row['Status'] == 'Lost':
                agent_stats[agent]['lost'] += 1
    
    print("BY AGENT:")
    print()
    print(f"  {'Agent':<15} {'Proposals':>10} {'Closed':>8} {'Lost':>6} {'Conv %':>8}")
    print(f"  {'-'*60}")
    
    for agent, stats in sorted(agent_stats.items()):
        proposals = stats['proposals']
        closed = stats['closed']
        lost = stats['lost']
        conv_rate = (closed / proposals * 100) if proposals > 0 else 0
        
        print(f"  {agent:<15} {proposals:>10} {closed:>8} {lost:>6} {conv_rate:>7.1f}%")
    
    print()

if __name__ == "__main__":
    show_pipeline()
    show_conversion_rates()

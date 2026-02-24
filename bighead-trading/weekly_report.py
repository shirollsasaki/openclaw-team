"""
Weekly Performance Report Generator
Answers: Which agent converts best? Which platform has best ROI? Where to focus?
"""
import csv
from datetime import datetime, timedelta
from collections import defaultdict

def generate_weekly_report():
    """Generate comprehensive weekly performance report"""
    
    # Load data
    try:
        with open('platform-revenue-dashboard.csv', 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
    except:
        print("No data available yet.")
        return
    
    if not data:
        print("No data available yet.")
        return
    
    # Filter to last 7 days
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    recent_data = [row for row in data if row['Date'] >= seven_days_ago]
    
    print("="*70)
    print("WEEKLY PERFORMANCE REPORT")
    print(f"Period: {seven_days_ago} to {datetime.now().strftime('%Y-%m-%d')}")
    print("="*70)
    print()
    
    # 1. Which agent has best conversion rate?
    print("📊 AGENT PERFORMANCE")
    print()
    
    agent_stats = defaultdict(lambda: {
        'leads': 0,
        'proposals': 0,
        'responses': 0,
        'closed': 0,
        'lost': 0,
        'revenue': 0
    })
    
    for row in recent_data:
        agents = [a.strip() for a in row['Agent'].split(',')]
        for agent in agents:
            agent_stats[agent]['leads'] += 1
            if row['Proposal Sent'] == 'Y':
                agent_stats[agent]['proposals'] += 1
            if row['Client Response'] == 'Y':
                agent_stats[agent]['responses'] += 1
            if row['Status'] == 'Closed':
                agent_stats[agent]['closed'] += 1
                try:
                    revenue = float(row['Revenue Amount']) if row['Revenue Amount'] else 0
                    agent_stats[agent]['revenue'] += revenue / len(agents)
                except:
                    pass
            if row['Status'] == 'Lost':
                agent_stats[agent]['lost'] += 1
    
    print(f"{'Agent':<12} {'Leads':>6} {'Props':>6} {'Closed':>7} {'Conv%':>7} {'Revenue':>10}")
    print("-"*70)
    
    agent_rankings = []
    for agent, stats in agent_stats.items():
        conv_rate = (stats['closed'] / stats['proposals'] * 100) if stats['proposals'] > 0 else 0
        agent_rankings.append((agent, stats, conv_rate))
    
    # Sort by conversion rate
    agent_rankings.sort(key=lambda x: x[2], reverse=True)
    
    for agent, stats, conv_rate in agent_rankings:
        print(f"{agent:<12} {stats['leads']:>6} {stats['proposals']:>6} {stats['closed']:>7} {conv_rate:>6.1f}% ${stats['revenue']:>9,.2f}")
    
    print()
    
    if agent_rankings:
        best_agent = agent_rankings[0]
        print(f"✅ **BEST CONVERTER:** {best_agent[0]} ({best_agent[2]:.1f}% conversion)")
        print()
    
    # 2. Which platform has best ROI?
    print("🏢 PLATFORM PERFORMANCE")
    print()
    
    platform_stats = defaultdict(lambda: {
        'leads': 0,
        'proposals': 0,
        'closed': 0,
        'revenue': 0,
        'time_spent': 0  # Would need time tracking
    })
    
    for row in recent_data:
        platform = row['Platform']
        platform_stats[platform]['leads'] += 1
        if row['Proposal Sent'] == 'Y':
            platform_stats[platform]['proposals'] += 1
        if row['Status'] == 'Closed':
            platform_stats[platform]['closed'] += 1
            try:
                revenue = float(row['Revenue Amount']) if row['Revenue Amount'] else 0
                platform_stats[platform]['revenue'] += revenue
            except:
                pass
    
    print(f"{'Platform':<15} {'Leads':>6} {'Props':>6} {'Closed':>7} {'Conv%':>7} {'Revenue':>10}")
    print("-"*70)
    
    platform_rankings = []
    for platform, stats in platform_stats.items():
        conv_rate = (stats['closed'] / stats['proposals'] * 100) if stats['proposals'] > 0 else 0
        platform_rankings.append((platform, stats, conv_rate))
    
    # Sort by revenue
    platform_rankings.sort(key=lambda x: x[1]['revenue'], reverse=True)
    
    for platform, stats, conv_rate in platform_rankings:
        print(f"{platform:<15} {stats['leads']:>6} {stats['proposals']:>6} {stats['closed']:>7} {conv_rate:>6.1f}% ${stats['revenue']:>9,.2f}")
    
    print()
    
    if platform_rankings:
        best_platform = platform_rankings[0]
        print(f"✅ **BEST PLATFORM:** {best_platform[0]} (${best_platform[1]['revenue']:,.2f} revenue)")
        print()
    
    # 3. Where should we focus more effort?
    print("🎯 STRATEGIC RECOMMENDATIONS")
    print()
    
    # Analyze trends
    recommendations = []
    
    # High conversion agents
    high_conv_agents = [a for a, s, c in agent_rankings if c > 50]
    if high_conv_agents:
        recommendations.append(f"✅ DOUBLE DOWN: {', '.join(high_conv_agents)} have >50% conversion")
    
    # Low conversion agents
    low_conv_agents = [a for a, s, c in agent_rankings if c < 20 and s['proposals'] >= 3]
    if low_conv_agents:
        recommendations.append(f"⚠️  IMPROVE OR PAUSE: {', '.join(low_conv_agents)} have <20% conversion")
    
    # Best platform
    if platform_rankings:
        best = platform_rankings[0]
        if best[1]['revenue'] > 0:
            recommendations.append(f"✅ FOCUS PLATFORM: {best[0]} generating best revenue")
    
    # Agents with low activity
    inactive_agents = [a for a, s, c in agent_rankings if s['leads'] < 2]
    if inactive_agents:
        recommendations.append(f"📢 ACTIVATE: {', '.join(inactive_agents)} have <2 leads this week")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print()
    
    # 4. Summary metrics
    print("📈 SUMMARY METRICS")
    print()
    
    total_leads = len(recent_data)
    total_proposals = sum(1 for row in recent_data if row['Proposal Sent'] == 'Y')
    total_closed = sum(1 for row in recent_data if row['Status'] == 'Closed')
    total_revenue = sum(float(row['Revenue Amount']) for row in recent_data 
                       if row['Revenue Amount'] and row['Revenue Amount'].replace('.','').replace('-','').isdigit())
    
    overall_conv = (total_closed / total_proposals * 100) if total_proposals > 0 else 0
    
    print(f"  Total leads:          {total_leads}")
    print(f"  Proposals sent:       {total_proposals}")
    print(f"  Deals closed:         {total_closed}")
    print(f"  Overall conversion:   {overall_conv:.1f}%")
    print(f"  Total revenue:        ${total_revenue:,.2f}")
    if total_closed > 0:
        print(f"  Avg deal size:        ${total_revenue/total_closed:,.2f}")
    print()
    
    print("="*70)
    print()
    
    # Export to file
    report_filename = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(report_filename, 'w') as f:
        f.write(f"WEEKLY PERFORMANCE REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"\nBest agent: {agent_rankings[0][0] if agent_rankings else 'N/A'}\n")
        f.write(f"Best platform: {platform_rankings[0][0] if platform_rankings else 'N/A'}\n")
        f.write(f"Total revenue: ${total_revenue:,.2f}\n")
        f.write(f"Overall conversion: {overall_conv:.1f}%\n")
    
    print(f"📄 Report saved to: {report_filename}")

if __name__ == "__main__":
    generate_weekly_report()

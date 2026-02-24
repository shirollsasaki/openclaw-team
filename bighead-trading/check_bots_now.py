#!/usr/bin/env python3
"""
Quick bot status check - reads last 50 lines of each log
"""

import os
import re
from datetime import datetime

BOTS = {
    'V1 Baseline': 'strategy1_bot.log',
    'V2 Enhanced': 'strategy1_v2.log',
    'V2+Squeeze': 'strategy1_v2_squeeze.log',
    'V2+Sq+All3': 'strategy1_v2_squeeze_all3.log'
}

def get_latest_stats(log_file):
    """Extract latest stats from log file"""
    if not os.path.exists(log_file):
        return None
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Read last 50 lines
        recent = lines[-50:] if len(lines) > 50 else lines
        
        stats = {
            'equity': 30.0,
            'unrealized': 0.0,
            'realized': 0.0,
            'total': 30.0,
            'open': 0,
            'long': 0,
            'short': 0,
            'last_update': 'Unknown',
            'running': False
        }
        
        # Parse from end (most recent first)
        for line in reversed(recent):
            # Extract equity line
            if 'Equity:' in line:
                equity_match = re.search(r'Equity: \$(\d+\.\d+)', line)
                unrealized_match = re.search(r'Unrealized: \$([+-]?\d+\.\d+)', line)
                total_match = re.search(r'Total: \$(\d+\.\d+)', line)
                realized_match = re.search(r'Realized: \$([+-]?\d+\.\d+)', line)
                open_match = re.search(r'Open: (\d+)', line)
                ls_match = re.search(r'\(L:(\d+)/S:(\d+)\)', line)
                
                if equity_match:
                    stats['equity'] = float(equity_match.group(1))
                if unrealized_match:
                    stats['unrealized'] = float(unrealized_match.group(1))
                if total_match:
                    stats['total'] = float(total_match.group(1))
                if realized_match:
                    stats['realized'] = float(realized_match.group(1))
                if open_match:
                    stats['open'] = int(open_match.group(1))
                if ls_match:
                    stats['long'] = int(ls_match.group(1))
                    stats['short'] = int(ls_match.group(2))
                
                # Extract timestamp
                ts_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
                if ts_match:
                    stats['last_update'] = ts_match.group(1)
                
                stats['running'] = True
                break
        
        return stats
    except Exception as e:
        return None

print("=" * 80)
print(f"🤖 BOT STATUS CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print()

all_stats = {}

for bot_name, log_file in BOTS.items():
    stats = get_latest_stats(log_file)
    all_stats[bot_name] = stats
    
    if stats:
        status = "🟢 RUNNING" if stats['running'] else "🔴 STOPPED"
        pnl = stats['total'] - 30.0
        pnl_pct = (pnl / 30.0) * 100
        
        pnl_emoji = "📈" if pnl > 0 else "📉" if pnl < 0 else "➡️"
        
        print(f"{bot_name:<15} {status}")
        print(f"  💰 Equity: ${stats['equity']:.2f} | Unrealized: ${stats['unrealized']:+.2f} | Total: ${stats['total']:.2f}")
        print(f"  {pnl_emoji} P&L: ${pnl:+.2f} ({pnl_pct:+.1f}%)")
        print(f"  📊 Positions: {stats['open']} open (L:{stats['long']}/S:{stats['short']})")
        print(f"  ⏰ Last update: {stats['last_update']}")
        print()
    else:
        print(f"{bot_name:<15} ❌ No data / not started")
        print()

# Comparison
print("=" * 80)
print("📊 LEADERBOARD (Sorted by Total Equity)")
print("=" * 80)

sorted_bots = sorted(
    [(name, stats) for name, stats in all_stats.items() if stats],
    key=lambda x: x[1]['total'],
    reverse=True
)

for i, (bot_name, stats) in enumerate(sorted_bots, 1):
    pnl = stats['total'] - 30.0
    pnl_pct = (pnl / 30.0) * 100
    
    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
    
    print(f"{medal} {i}. {bot_name:<15} ${stats['total']:.2f} ({pnl:+.2f} | {pnl_pct:+.1f}%) | {stats['open']} open")

print("=" * 80)

#!/usr/bin/env python3
"""
Compare V2+Squeeze performance across different timeframes
"""

import re
from datetime import datetime

def parse_log(log_file):
    """Extract latest equity and position info from log"""
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Find last equity line
        equity_line = None
        positions_line = None
        
        for line in reversed(lines):
            if 'Equity:' in line and equity_line is None:
                equity_line = line
            if ('No open positions' in line or 'open positions' in line.lower()) and positions_line is None:
                positions_line = line
            if equity_line and positions_line:
                break
        
        if not equity_line:
            return None
        
        # Parse equity line
        # Format: [timestamp] [INFO] Equity: $30.00 | Unrealized: $+0.00 | Total: $30.00 | Open: 0 (L:0/S:0) | Realized: $+0.00 | Losses: 0
        
        equity_match = re.search(r'Equity: \$([0-9.]+)', equity_line)
        unrealized_match = re.search(r'Unrealized: \$([+-]?[0-9.]+)', equity_line)
        total_match = re.search(r'Total: \$([0-9.]+)', equity_line)
        open_match = re.search(r'Open: (\d+)', equity_line)
        realized_match = re.search(r'Realized: \$([+-]?[0-9.]+)', equity_line)
        losses_match = re.search(r'Losses: (\d+)', equity_line)
        
        equity = float(equity_match.group(1)) if equity_match else 30.0
        unrealized = float(unrealized_match.group(1)) if unrealized_match else 0.0
        total = float(total_match.group(1)) if total_match else 30.0
        positions = int(open_match.group(1)) if open_match else 0
        realized = float(realized_match.group(1)) if realized_match else 0.0
        losses = int(losses_match.group(1)) if losses_match else 0
        
        # Get timestamp
        timestamp_match = re.search(r'\[([0-9-]+ [0-9:]+)\]', equity_line)
        timestamp = timestamp_match.group(1) if timestamp_match else 'N/A'
        
        return {
            'equity': equity,
            'unrealized': unrealized,
            'total': total,
            'positions': positions,
            'realized': realized,
            'losses': losses,
            'timestamp': timestamp
        }
        
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error parsing {log_file}: {e}")
        return None

def count_trades(log_file):
    """Count total trades executed"""
    try:
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Count OPENED and CLOSED
        opened = content.count('OPENED')
        closed = content.count('CLOSED')
        
        return opened
        
    except FileNotFoundError:
        return 0
    except:
        return 0

def main():
    print("="*80)
    print("📊 TIMEFRAME COMPARISON - V2+Squeeze")
    print("="*80)
    print()
    
    timeframes = [
        {
            'name': '15m (LIVE)',
            'log': 'strategy1_v2_squeeze.log',
            'mode': '🔴 LIVE',
            'check_interval': '60s'
        },
        {
            'name': '5m (Sim)',
            'log': 'strategy1_v2_squeeze_5m.log',
            'mode': '📊 SIM',
            'check_interval': '30s'
        },
        {
            'name': '1m (Sim)',
            'log': 'strategy1_v2_squeeze_1m.log',
            'mode': '📊 SIM',
            'check_interval': '15s'
        }
    ]
    
    results = []
    
    for tf in timeframes:
        data = parse_log(tf['log'])
        trades = count_trades(tf['log'])
        
        if data:
            pnl = data['total'] - 30.0
            pnl_pct = (pnl / 30.0) * 100
            
            results.append({
                'name': tf['name'],
                'mode': tf['mode'],
                'total': data['total'],
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'positions': data['positions'],
                'trades': trades,
                'realized': data['realized'],
                'unrealized': data['unrealized'],
                'losses': data['losses'],
                'timestamp': data['timestamp'],
                'check_interval': tf['check_interval']
            })
        else:
            results.append({
                'name': tf['name'],
                'mode': tf['mode'],
                'total': 0,
                'pnl': 0,
                'pnl_pct': 0,
                'positions': 0,
                'trades': 0,
                'realized': 0,
                'unrealized': 0,
                'losses': 0,
                'timestamp': 'N/A',
                'check_interval': tf['check_interval']
            })
    
    # Print results
    for r in results:
        print(f"{r['mode']} {r['name']}")
        print(f"  Check: Every {r['check_interval']}")
        print(f"  💰 Total: ${r['total']:.2f} ({r['pnl']:+.2f} / {r['pnl_pct']:+.1f}%)")
        print(f"  📊 Positions: {r['positions']} open | {r['trades']} total trades | {r['losses']} losses")
        print(f"  💵 Realized: ${r['realized']:+.2f} | Unrealized: ${r['unrealized']:+.2f}")
        print(f"  ⏰ Last update: {r['timestamp']}")
        print()
    
    print("="*80)
    print("📈 LEADERBOARD (By Total Equity)")
    print("="*80)
    
    # Sort by total
    sorted_results = sorted(results, key=lambda x: x['total'], reverse=True)
    
    for i, r in enumerate(sorted_results, 1):
        medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f'{i}.'
        print(f"{medal} {r['name']:<15} ${r['total']:>6.2f} ({r['pnl']:+6.2f} | {r['pnl_pct']:+5.1f}%) | {r['positions']} open | {r['trades']} trades")
    
    print("="*80)
    print()
    
    # Recommendations
    print("💡 INSIGHTS:")
    print()
    
    if all(r['trades'] == 0 for r in results):
        print("  ⏳ All timeframes waiting for first signal")
        print("  ⚠️  Squeeze filter is very selective - this is normal")
        print("  📊 Check back in 1-2 hours for comparison data")
    else:
        best = sorted_results[0]
        print(f"  🏆 Best performer: {best['name']} (${best['total']:.2f})")
        
        if best['trades'] > 0:
            win_rate = ((best['trades'] - best['losses']) / best['trades']) * 100
            print(f"  ✅ Win rate: {win_rate:.1f}%")
        
        # Trade frequency comparison
        print()
        print("  📊 Trade Frequency:")
        for r in sorted_results:
            if r['trades'] > 0:
                print(f"     {r['name']}: {r['trades']} trades")
        
        # Best for LIVE trading
        if sorted_results[0]['trades'] > 5:  # Need enough data
            print()
            print(f"  💡 Recommendation for LIVE: {sorted_results[0]['name']}")
    
    print()

if __name__ == "__main__":
    main()

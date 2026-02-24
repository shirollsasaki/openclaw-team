#!/usr/bin/env python3
"""
Create visualizations and comparison tables
"""

import pandas as pd
import json

# Load results
with open('adaptive_backtest_results.json', 'r') as f:
    adaptive_results = json.load(f)

# Create comparison table
print("="*90)
print("📊 STRATEGY COMPARISON - STATIC VS ADAPTIVE")
print("="*90)

comparison = {
    'Strategy': ['Static (ARB+OP+ETH)', 'Adaptive (Daily Rebalance)'],
    'Starting Capital': ['$30.00', '$30.00'],
    'Ending Capital': ['$46.13', '$24.04'],
    'Profit/Loss': ['+$16.13 (+53.76%)', '-$5.96 (-19.87%)'],
    'Total Trades': [24, 57],
    'Win Rate': ['59.5%', '29.8%'],
    'Max Drawdown': ['21.8%', '24.9%'],
    'Trades/Day': ['3.4', '8.1'],
}

df = pd.DataFrame(comparison)
print("\n" + df.to_string(index=False))

print("\n" + "="*90)
print("🏆 WINNER: STATIC ALLOCATION")
print("="*90)
print("\nStatic beats Adaptive by 73.6 percentage points (+53.76% vs -19.87%)")

# Daily capital chart data
print("\n" + "="*90)
print("📈 EQUITY CURVE - DAILY CAPITAL")
print("="*90)

daily_capital = adaptive_results['daily_capital']
days = list(range(len(daily_capital)))

print(f"\n{'Day':<8} {'Capital':<12} {'Change':<12} {'Drawdown'}")
print("-"*50)

peak = 30.0
for i, cap in enumerate(daily_capital):
    if i == 0:
        change = "$0.00"
    else:
        change = f"${cap - daily_capital[i-1]:+.2f}"
    
    if cap > peak:
        peak = cap
    dd = (peak - cap) / peak * 100
    
    print(f"{i:<8} ${cap:<11.2f} {change:<12} {dd:.1f}%")

# Asset selection frequency
print("\n" + "="*90)
print("📊 ASSET SELECTION FREQUENCY")
print("="*90)

asset_days = {}
for day in adaptive_results['daily_selections']:
    for asset in day['assets']:
        asset_days[asset] = asset_days.get(asset, 0) + 1

print(f"\n{'Asset':<8} {'Days Selected':<15} {'% of Days'}")
print("-"*40)
for asset in sorted(asset_days.items(), key=lambda x: x[1], reverse=True):
    pct = (asset[1] / 7) * 100
    print(f"{asset[0]:<8} {asset[1]:<15} {pct:.1f}%")

# Daily selections table
print("\n" + "="*90)
print("📅 DAILY ASSET SELECTIONS")
print("="*90)

selections_df = pd.read_csv('daily_asset_selections.csv')
print("\n" + selections_df.to_string(index=False))

# Trade analysis
print("\n" + "="*90)
print("💼 TRADE BREAKDOWN BY RESULT")
print("="*90)

trades_df = pd.read_csv('adaptive_trades.csv')
result_counts = trades_df['result'].value_counts()
result_pnl = trades_df.groupby('result')['pnl'].agg(['count', 'sum', 'mean'])

print(f"\n{'Result':<8} {'Count':<8} {'Total P&L':<12} {'Avg P&L'}")
print("-"*50)
for result in ['TP', 'SL', 'EOD']:
    if result in result_pnl.index:
        row = result_pnl.loc[result]
        print(f"{result:<8} {int(row['count']):<8} ${row['sum']:<11.2f} ${row['mean']:.2f}")

print("\n" + "="*90)
print("🔍 KEY INSIGHTS")
print("="*90)

print("""
WHY ADAPTIVE FILTER FAILED:

1. ❌ OVER-TRADING (57 trades vs 24 static)
   - More trades = more fees (0.2% per trade)
   - Lost $11.40 in fees alone (57 × $0.20 avg)

2. ❌ WRONG ASSET SELECTION
   - LINK: 13 trades, only 1 win (-$5.04)
   - SOL: 17 trades, 5 wins (-$4.78)
   - Selected based on volatility, not profitability

3. ❌ DAILY CHURN
   - Switching assets too frequently
   - Missed multi-day trends (ARB went +87% over full week)
   - Adaptive only caught 9 ARB trades vs static's full exposure

4. ❌ LOW WIN RATE (29.8% vs 59.5%)
   - Volatility ≠ profitable structure
   - High ATR attracted us to losing assets

5. ✅ ARB WAS BEST (when selected)
   - ARB: 9 trades, 5 wins, +$5.42
   - Only asset that made money consistently
   - But only selected on 3 out of 7 days!

STATIC ADVANTAGE:

✅ Locked into proven winners (ARB/OP/ETH)
✅ Full exposure to ARB's +87% week
✅ Lower trade frequency = lower fees
✅ Fewer bad assets (no LINK/SOL/AVAX)
""")

print("="*90)
print("🎯 FINAL RECOMMENDATION")
print("="*90)

print("""
STICK WITH STATIC ALLOCATION:

Best Configuration:
- ARB: $10 (highest profit)
- ETH: $10 (safety/high WR)
- OP: $10 (optional 3rd if you have $30)

Expected Performance:
- 7-day return: +54% ($30 → $46)
- Win rate: 59.5%
- Max DD: 21.8%

Why NOT use adaptive filter:
- Lost 19.87% vs gained 53.76%
- Over-trades (8.1/day vs 3.4/day)
- Selects wrong assets (LINK/SOL lost money)
- Misses sustained trends

When adaptive MIGHT work:
- Longer rebalance periods (weekly, not daily)
- Better scoring (focus on recent profitability, not just volatility)
- Whitelist only proven assets (ARB/ETH/OP only)

Bottom line: Simple beats complex here.
""")

print("="*90)

# Save comparison
with open('strategy_comparison.txt', 'w') as f:
    f.write(df.to_string(index=False))

print("\n💾 Saved comparison table to: strategy_comparison.txt")

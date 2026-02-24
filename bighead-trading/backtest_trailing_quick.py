"""
Quick backtest: Compare trailing SL activation levels
Using simplified SMC signals
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt

TIMEFRAME = '15m'
LOOKBACK_DAYS = 60
LEVERAGE = 15
CAPITAL = 30

# Test these activation levels (% profit on position)
TEST_LEVELS = [5, 7.5, 10, 12.5, 15, 20]
TRAILING_DISTANCE = 0.005  # 0.5%

def calculate_indicators(df):
    """Calculate indicators"""
    # EMA
    df['ema20'] = df['close'].ewm(span=20).mean()
    df['ema50'] = df['close'].ewm(span=50).mean()
    
    # ATR
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()
    
    # Simple momentum breakout signals
    df['swing_high'] = df['high'].rolling(5, center=True).max()
    df['swing_low'] = df['low'].rolling(5, center=True).min()
    
    return df

def generate_signal(df, i):
    """Generate trading signal"""
    if i < 50:
        return None
    
    close = df['close'].iloc[i]
    ema20 = df['ema20'].iloc[i]
    ema50 = df['ema50'].iloc[i]
    
    # Recent highs/lows
    recent_high = df['high'].iloc[i-20:i].max()
    recent_low = df['low'].iloc[i-20:i].min()
    
    # LONG: breakout above recent high + above EMAs
    if close > recent_high and close > ema20 and ema20 > ema50:
        return 'LONG'
    
    # SHORT: breakdown below recent low + below EMAs
    if close < recent_low and close < ema20 and ema20 < ema50:
        return 'SHORT'
    
    return None

def simulate_trade(df, entry_idx, direction, entry, sl, tp, activation_pct):
    """Simulate a single trade with trailing SL"""
    
    size = CAPITAL
    highest = entry
    lowest = entry
    trailing_active = False
    
    # Walk forward from entry
    for i in range(entry_idx + 1, len(df)):
        row = df.iloc[i]
        current = row['close']
        high = row['high']
        low = row['low']
        
        # Calculate P&L
        if direction == 'LONG':
            price_change_pct = (current - entry) / entry
        else:
            price_change_pct = (entry - current) / entry
        
        exposure = size * LEVERAGE
        gross_pnl = exposure * price_change_pct
        net_pnl = gross_pnl - 0.002  # fee estimate
        pnl_pct = (net_pnl / size) * 100
        
        # Activate trailing if threshold reached
        if pnl_pct >= activation_pct and not trailing_active:
            trailing_active = True
        
        # Update trailing SL
        if trailing_active:
            if direction == 'LONG':
                if current > highest:
                    highest = current
                new_sl = highest * (1 - TRAILING_DISTANCE)
                if new_sl > sl:
                    sl = new_sl
            else:
                if current < lowest:
                    lowest = current
                new_sl = lowest * (1 + TRAILING_DISTANCE)
                if new_sl < sl:
                    sl = new_sl
        
        # Check exit
        if direction == 'LONG':
            if high >= tp:
                # TP hit
                final_price_change = (tp - entry) / entry
                final_pnl = (size * LEVERAGE * final_price_change) - 0.002
                return {'pnl': final_pnl, 'exit': 'TP', 'trailing_used': trailing_active}
            elif low <= sl:
                # SL hit
                final_price_change = (sl - entry) / entry
                final_pnl = (size * LEVERAGE * final_price_change) - 0.002
                return {'pnl': final_pnl, 'exit': 'SL', 'trailing_used': trailing_active}
        else:
            if low <= tp:
                # TP hit
                final_price_change = (entry - tp) / entry
                final_pnl = (size * LEVERAGE * final_price_change) - 0.002
                return {'pnl': final_pnl, 'exit': 'TP', 'trailing_used': trailing_active}
            elif high >= sl:
                # SL hit
                final_price_change = (entry - sl) / entry
                final_pnl = (size * LEVERAGE * final_price_change) - 0.002
                return {'pnl': final_pnl, 'exit': 'SL', 'trailing_used': trailing_active}
    
    # No exit (end of data)
    return None

def backtest_activation_level(df, activation_pct):
    """Backtest with specific activation level"""
    
    df = calculate_indicators(df)
    trades = []
    
    i = 50
    while i < len(df) - 100:  # Leave room for trade to complete
        signal = generate_signal(df, i)
        
        if signal and pd.notna(df['atr'].iloc[i]):
            entry = df['close'].iloc[i]
            atr = df['atr'].iloc[i]
            
            # Set SL/TP
            if signal == 'LONG':
                sl = entry - (2 * atr)
                tp = entry + (4 * atr)  # 2:1 RR
            else:
                sl = entry + (2 * atr)
                tp = entry - (4 * atr)
            
            # Validate SL distance
            sl_pct = abs(entry - sl) / entry
            if sl_pct > 0.08:  # max 8% SL
                i += 1
                continue
            
            # Simulate trade
            result = simulate_trade(df, i, signal, entry, sl, tp, activation_pct)
            
            if result:
                trades.append(result)
                i += 50  # Skip ahead after trade
            else:
                i += 1
        else:
            i += 1
    
    return trades

print("="*70)
print("TRAILING SL ACTIVATION - QUICK BACKTEST")
print("="*70)
print()

# Fetch data
exchange = ccxt.binance()
results_by_level = {}

for asset in ['ARB/USDT', 'OP/USDT']:
    print(f"Testing {asset}...")
    
    since = exchange.parse8601((datetime.now() - timedelta(days=LOOKBACK_DAYS)).isoformat())
    ohlcv = exchange.fetch_ohlcv(asset, TIMEFRAME, since=since, limit=1000)
    
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    for activation in TEST_LEVELS:
        trades = backtest_activation_level(df, activation)
        
        if activation not in results_by_level:
            results_by_level[activation] = []
        
        results_by_level[activation].extend(trades)
    
    print(f"  ✅ Done")

print()
print("="*70)
print("RESULTS")
print("="*70)
print()

# Analyze results
print(f"{'Activation':<12} {'Trades':<8} {'Win%':<8} {'Total P&L':<12} {'Avg P&L':<12} {'Trail Saves':<12}")
print("-"*70)

best_total = None
best_avg = None

for activation in sorted(TEST_LEVELS):
    trades = results_by_level[activation]
    
    if not trades:
        continue
    
    wins = [t for t in trades if t['pnl'] > 0]
    total_pnl = sum(t['pnl'] for t in trades)
    avg_pnl = total_pnl / len(trades)
    win_rate = len(wins) / len(trades) * 100
    trailing_saves = len([t for t in trades if t['trailing_used'] and t['exit'] == 'SL' and t['pnl'] > -1])
    
    print(f"{activation}%{' '*(10-len(str(activation)))} {len(trades):<8} {win_rate:<7.1f}% ${total_pnl:<11.2f} ${avg_pnl:<11.2f} {trailing_saves:<12}")
    
    if best_total is None or total_pnl > best_total[1]:
        best_total = (activation, total_pnl, avg_pnl, win_rate)
    
    if best_avg is None or avg_pnl > best_avg[1]:
        best_avg = (activation, avg_pnl, total_pnl, win_rate)

print()
print("="*70)
print("RECOMMENDATION")
print("="*70)
print()

print(f"Best Total P&L:  {best_total[0]}% activation (${best_total[1]:.2f} total, ${best_total[2]:.2f}/trade, {best_total[3]:.1f}% WR)")
print(f"Best Avg P&L:    {best_avg[0]}% activation (${best_avg[2]:.2f} total, ${best_avg[1]:.2f}/trade, {best_avg[3]:.1f}% WR)")
print()

# Current equivalent
current_setting = 15  # 1% price = 15% P&L with 15x
if current_setting in TEST_LEVELS and results_by_level[current_setting]:
    current_trades = results_by_level[current_setting]
    current_total = sum(t['pnl'] for t in current_trades)
    current_avg = current_total / len(current_trades)
    
    print(f"Your Current (15%): ${current_total:.2f} total, ${current_avg:.2f}/trade")
    
    if best_total[0] != current_setting:
        improvement = ((best_total[1] - current_total) / abs(current_total) * 100) if current_total != 0 else 0
        print(f"Switching to {best_total[0]}%: {improvement:+.1f}% improvement")
    else:
        print("✅ Already using optimal setting!")

print()
print(f"🎯 OPTIMAL SETTING: {best_total[0]}% activation")
print(f"   (Maximizes total P&L over {LOOKBACK_DAYS} days)")

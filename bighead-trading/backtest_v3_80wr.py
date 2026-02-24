"""
Backtest V3 (80% WR Target) vs Baseline
Test all 5 improvements
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt

TIMEFRAME = '15m'
LOOKBACK_DAYS = 90
LEVERAGE = 15
CAPITAL = 30

def calculate_indicators(df):
    """Calculate all indicators"""
    df = df.copy()
    
    # Swing Points
    SWING_LENGTH = 3
    df['swing_high'] = False
    df['swing_low'] = False
    
    for i in range(SWING_LENGTH, len(df) - SWING_LENGTH):
        if df['high'].iloc[i] == df['high'].iloc[i-SWING_LENGTH:i+SWING_LENGTH+1].max():
            df.loc[df.index[i], 'swing_high'] = True
        if df['low'].iloc[i] == df['low'].iloc[i-SWING_LENGTH:i+SWING_LENGTH+1].min():
            df.loc[df.index[i], 'swing_low'] = True
    
    # BOS
    df['bos_bull'] = False
    df['bos_bear'] = False
    
    last_high = None
    last_low = None
    
    for i in range(len(df)):
        if df['swing_high'].iloc[i]:
            last_high = df['high'].iloc[i]
        if df['swing_low'].iloc[i]:
            last_low = df['low'].iloc[i]
        
        if last_high is not None and last_low is not None:
            if df['close'].iloc[i] > last_high:
                df.loc[df.index[i], 'bos_bull'] = True
            elif df['close'].iloc[i] < last_low:
                df.loc[df.index[i], 'bos_bear'] = True
    
    # Range
    LOOKBACK_PERIOD = 20
    df['range_high'] = df['high'].rolling(LOOKBACK_PERIOD).max()
    df['range_low'] = df['low'].rolling(LOOKBACK_PERIOD).min()
    
    # Volume
    df['volume_avg'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_avg']
    
    # Trend
    df['ema_20'] = df['close'].ewm(span=20).mean()
    df['ema_50'] = df['close'].ewm(span=50).mean()
    df['trend_bullish'] = df['close'] > df['ema_20']
    
    # Squeeze
    bb_basis = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    bb_upper = bb_basis + (2.0 * bb_std)
    bb_lower = bb_basis - (2.0 * bb_std)
    
    high, low, close = df['high'], df['low'], df['close']
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    
    kc_basis = df['ema_20']
    kc_range = atr * 1.5
    kc_upper = kc_basis + kc_range
    kc_lower = kc_basis - kc_range
    
    df['squeeze_on'] = (bb_lower > kc_lower) & (bb_upper < kc_upper)
    
    highest = df['high'].rolling(20).max()
    lowest = df['low'].rolling(20).min()
    df['sqz_mom'] = df['close'] - ((highest + lowest) / 2 + bb_basis) / 2
    
    # Signals
    df['signal'] = 0
    for i in range(LOOKBACK_PERIOD, len(df)):
        if df['bos_bull'].iloc[i]:
            df.loc[df.index[i], 'signal'] = 1
        elif df['bos_bear'].iloc[i]:
            df.loc[df.index[i], 'signal'] = -1
    
    return df

def check_mtf_trend(df_1h, current_idx, signal):
    """Check 1H trend alignment"""
    # Map 15m index to 1H (4 bars = 1 hour)
    h1_idx = current_idx // 4
    
    if h1_idx < 20 or h1_idx >= len(df_1h):
        return True
    
    row = df_1h.iloc[h1_idx]
    
    if signal == 1:  # LONG
        return row['close'] > row['ema_20'] and row['ema_20'] > row['ema_50']
    else:  # SHORT
        return row['close'] < row['ema_20'] and row['ema_20'] < row['ema_50']

def check_momentum_confirmation(df, i, signal):
    """Check if next bar confirms momentum"""
    if i >= len(df) - 1:
        return False
    
    signal_bar = df.iloc[i]
    confirm_bar = df.iloc[i+1]
    
    if signal == 1:  # LONG
        return (confirm_bar['close'] > signal_bar['close'] and 
                confirm_bar['close'] > confirm_bar['open'])
    else:  # SHORT
        return (confirm_bar['close'] < signal_bar['close'] and 
                confirm_bar['close'] < confirm_bar['open'])

def is_valid_trading_hour(timestamp):
    """Check if valid trading time"""
    hour = timestamp.hour
    # Skip 12 AM - 6 AM UTC
    return not (hour >= 0 and hour < 6)

def simulate_trade_with_immediate_be(df, entry_idx, signal, entry, sl, tp):
    """Simulate trade with immediate breakeven"""
    immediate_be_triggered = False
    
    for j in range(entry_idx + 1, min(entry_idx + 200, len(df))):
        high = df['high'].iloc[j]
        low = df['low'].iloc[j]
        close = df['close'].iloc[j]
        
        # Check for immediate breakeven (1% favorable)
        if not immediate_be_triggered:
            if signal == 1:  # LONG
                favorable_pct = (close - entry) / entry
            else:  # SHORT
                favorable_pct = (entry - close) / entry
            
            if favorable_pct >= 0.01:
                sl = entry  # Move SL to breakeven
                immediate_be_triggered = True
        
        # Check TP/SL
        if signal == 1:  # LONG
            if high >= tp:
                pnl = CAPITAL * LEVERAGE * ((tp - entry) / entry) - 0.002
                return pnl, 'TP', j - entry_idx, immediate_be_triggered
            elif low <= sl:
                pnl = CAPITAL * LEVERAGE * ((sl - entry) / entry) - 0.002
                return pnl, 'SL' if not immediate_be_triggered else 'BE', j - entry_idx, immediate_be_triggered
        else:  # SHORT
            if low <= tp:
                pnl = CAPITAL * LEVERAGE * ((entry - tp) / entry) - 0.002
                return pnl, 'TP', j - entry_idx, immediate_be_triggered
            elif high >= sl:
                pnl = CAPITAL * LEVERAGE * ((entry - sl) / entry) - 0.002
                return pnl, 'SL' if not immediate_be_triggered else 'BE', j - entry_idx, immediate_be_triggered
    
    return 0, 'TIMEOUT', 0, immediate_be_triggered

def backtest_baseline(df_15m, df_1h):
    """Baseline: V2+Squeeze (current live bot)"""
    df = calculate_indicators(df_15m)
    
    trades = []
    i = 50
    
    while i < len(df) - 50:
        row = df.iloc[i]
        signal = row['signal']
        
        if signal == 0:
            i += 1
            continue
        
        # Basic filters only
        if row['squeeze_on']:
            i += 1
            continue
        
        if (signal == 1 and row['sqz_mom'] <= 0) or (signal == -1 and row['sqz_mom'] >= 0):
            i += 1
            continue
        
        if row['volume_ratio'] < 1.5:
            i += 1
            continue
        
        if (signal == 1 and not row['trend_bullish']) or (signal == -1 and row['trend_bullish']):
            i += 1
            continue
        
        # Execute
        entry = row['close']
        
        if signal == 1:
            sl = row['range_low'] if row['range_low'] < entry else entry * 0.985
            tp = entry + (entry - sl) * 2.0
        else:
            sl = row['range_high'] if row['range_high'] > entry else entry * 1.015
            tp = entry - (sl - entry) * 2.0
        
        if abs(entry - sl) / entry > 0.10:
            i += 1
            continue
        
        pnl, exit_type, bars_held, _ = simulate_trade_with_immediate_be(df, i, signal, entry, sl, tp)
        
        if exit_type != 'TIMEOUT':
            trades.append({'pnl': pnl, 'type': exit_type, 'signal': 'LONG' if signal == 1 else 'SHORT'})
            i += bars_held + 10
        else:
            i += 1
    
    return trades

def backtest_v3(df_15m, df_1h):
    """V3: All 5 improvements"""
    df = calculate_indicators(df_15m)
    
    trades = []
    skipped_reasons = {'mtf': 0, 'momentum': 0, 'volume': 0, 'time': 0}
    i = 50
    
    while i < len(df) - 50:
        row = df.iloc[i]
        signal = row['signal']
        
        if signal == 0:
            i += 1
            continue
        
        # Basic filters
        if row['squeeze_on']:
            i += 1
            continue
        
        if (signal == 1 and row['sqz_mom'] <= 0) or (signal == -1 and row['sqz_mom'] >= 0):
            i += 1
            continue
        
        # NEW: Volume 2.5x (increased from 1.5x)
        if row['volume_ratio'] < 2.5:
            skipped_reasons['volume'] += 1
            i += 1
            continue
        
        if (signal == 1 and not row['trend_bullish']) or (signal == -1 and row['trend_bullish']):
            i += 1
            continue
        
        # NEW: Time filter
        if not is_valid_trading_hour(row.name):
            skipped_reasons['time'] += 1
            i += 1
            continue
        
        # NEW: MTF filter
        if not check_mtf_trend(df_1h, i, signal):
            skipped_reasons['mtf'] += 1
            i += 1
            continue
        
        # NEW: Momentum confirmation
        if not check_momentum_confirmation(df, i, signal):
            skipped_reasons['momentum'] += 1
            i += 1
            continue
        
        # Execute
        entry = row['close']
        
        if signal == 1:
            sl = row['range_low'] if row['range_low'] < entry else entry * 0.985
            tp = entry + (entry - sl) * 2.0
        else:
            sl = row['range_high'] if row['range_high'] > entry else entry * 1.015
            tp = entry - (sl - entry) * 2.0
        
        if abs(entry - sl) / entry > 0.10:
            i += 1
            continue
        
        # NEW: Simulate with immediate breakeven
        pnl, exit_type, bars_held, be_triggered = simulate_trade_with_immediate_be(df, i, signal, entry, sl, tp)
        
        if exit_type != 'TIMEOUT':
            trades.append({
                'pnl': pnl,
                'type': exit_type,
                'signal': 'LONG' if signal == 1 else 'SHORT',
                'be_triggered': be_triggered
            })
            i += bars_held + 10
        else:
            i += 1
    
    return trades, skipped_reasons

print("="*80)
print("BACKTEST: BASELINE vs V3 (80% WR TARGET)")
print("="*80)
print()

exchange = ccxt.binance()

baseline_all = []
v3_all = []
all_skipped = {'mtf': 0, 'momentum': 0, 'volume': 0, 'time': 0}

for asset in ['ARB/USDT', 'OP/USDT']:
    print(f"Testing {asset}...")
    
    since = exchange.parse8601((datetime.now() - timedelta(days=LOOKBACK_DAYS)).isoformat())
    
    # Fetch 15m
    ohlcv_15m = exchange.fetch_ohlcv(asset, '15m', since=since, limit=1000)
    df_15m = pd.DataFrame(ohlcv_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_15m['timestamp'] = pd.to_datetime(df_15m['timestamp'], unit='ms')
    df_15m.set_index('timestamp', inplace=True)
    
    # Fetch 1h
    ohlcv_1h = exchange.fetch_ohlcv(asset, '1h', since=since, limit=1000)
    df_1h = pd.DataFrame(ohlcv_1h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_1h['timestamp'] = pd.to_datetime(df_1h['timestamp'], unit='ms')
    df_1h.set_index('timestamp', inplace=True)
    df_1h = calculate_indicators(df_1h)
    
    # Backtest baseline
    baseline_trades = backtest_baseline(df_15m, df_1h)
    baseline_all.extend(baseline_trades)
    
    # Backtest V3
    v3_trades, skipped = backtest_v3(df_15m, df_1h)
    v3_all.extend(v3_trades)
    
    for key in skipped:
        all_skipped[key] += skipped[key]
    
    print(f"  Baseline: {len(baseline_trades)} trades")
    print(f"  V3: {len(v3_trades)} trades")
    print()

print("="*80)
print("RESULTS COMPARISON")
print("="*80)
print()

# Baseline stats
baseline_wins = [t for t in baseline_all if t['pnl'] > 0]
baseline_losses = [t for t in baseline_all if t['pnl'] <= 0]
baseline_wr = (len(baseline_wins) / len(baseline_all) * 100) if baseline_all else 0
baseline_pnl = sum(t['pnl'] for t in baseline_all)

# V3 stats
v3_wins = [t for t in v3_all if t['pnl'] > 0]
v3_losses = [t for t in v3_all if t['pnl'] <= 0]
v3_wr = (len(v3_wins) / len(v3_all) * 100) if v3_all else 0
v3_pnl = sum(t['pnl'] for t in v3_all)

# Immediate BE stats
v3_be_saves = len([t for t in v3_all if t.get('be_triggered') and t['type'] == 'BE'])

print(f"{'Metric':<25} {'Baseline':<20} {'V3 (Target 80%)':<20} {'Improvement':<15}")
print("-"*80)
print(f"{'Total Trades':<25} {len(baseline_all):<20} {len(v3_all):<20} {len(v3_all) - len(baseline_all):+}")
print(f"{'Wins':<25} {len(baseline_wins):<20} {len(v3_wins):<20} {len(v3_wins) - len(baseline_wins):+}")
print(f"{'Losses':<25} {len(baseline_losses):<20} {len(v3_losses):<20} {len(v3_losses) - len(baseline_losses):+}")
print(f"{'Win Rate':<25} {baseline_wr:.1f}%{'':<15} {v3_wr:.1f}%{'':<15} {v3_wr - baseline_wr:+.1f}pp")
print(f"{'Total P&L':<25} ${baseline_pnl:.2f}{'':<13} ${v3_pnl:.2f}{'':<13} ${v3_pnl - baseline_pnl:+.2f}")

if v3_all:
    print(f"{'Avg P&L/Trade':<25} ${baseline_pnl/len(baseline_all):.2f}{'':<13} ${v3_pnl/len(v3_all):.2f}{'':<13}")
    print(f"{'Immediate BE Saves':<25} {'-':<20} {v3_be_saves:<20}")

print()
print("="*80)
print("V3 FILTER EFFECTIVENESS")
print("="*80)
print()

print(f"Trades filtered by each improvement:")
print(f"  MTF (1H trend): {all_skipped['mtf']} trades skipped")
print(f"  Momentum confirmation: {all_skipped['momentum']} trades skipped")
print(f"  Volume 2.5x: {all_skipped['volume']} trades skipped")
print(f"  Time filter: {all_skipped['time']} trades skipped")
print(f"  Immediate BE: {v3_be_saves} trades saved from loss")
print()

print("="*80)
print("VERDICT")
print("="*80)
print()

if v3_wr >= 80:
    print(f"🎯 TARGET HIT: {v3_wr:.1f}% WR (target: 80%)")
    print(f"✅ V3 is ready for deployment!")
elif v3_wr >= 70:
    print(f"🎯 CLOSE: {v3_wr:.1f}% WR (target: 80%)")
    print(f"⚠️  Nearly there, may need minor tuning")
elif v3_wr >= 60:
    print(f"📈 IMPROVING: {v3_wr:.1f}% WR (baseline: {baseline_wr:.1f}%)")
    print(f"⚠️  Need more optimization to hit 80%")
else:
    print(f"❌ BELOW TARGET: {v3_wr:.1f}% WR (target: 80%)")
    print(f"⚠️  Significant work needed")

print()
print(f"Improvement: {v3_wr - baseline_wr:+.1f}pp WR, ${v3_pnl - baseline_pnl:+.2f} P&L")

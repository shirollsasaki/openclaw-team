"""
Comprehensive Backtest: All 3 Phases
Compare baseline vs enhancements
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt
import warnings
warnings.filterwarnings('ignore')

TIMEFRAME = '15m'
LOOKBACK_DAYS = 90
LEVERAGE = 15
CAPITAL = 30

def calculate_indicators(df):
    """All indicators"""
    df['ema20'] = df['close'].ewm(span=20).mean()
    df['ema50'] = df['close'].ewm(span=50).mean()
    
    high, low, close = df['high'], df['low'], df['close']
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()
    
    # Squeeze
    df['bb_basis'] = df['close'].rolling(20).mean()
    std = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_basis'] + (2.0 * std)
    df['bb_lower'] = df['bb_basis'] - (2.0 * std)
    
    df['kc_range'] = df['atr'] * 1.5
    df['kc_upper'] = df['ema20'] + df['kc_range']
    df['kc_lower'] = df['ema20'] - df['kc_range']
    
    df['squeeze_on'] = (df['bb_lower'] > df['kc_lower']) & (df['bb_upper'] < df['kc_upper'])
    
    highest = df['high'].rolling(20).max()
    lowest = df['low'].rolling(20).min()
    df['sqz_mom'] = df['close'] - ((highest + lowest) / 2 + df['bb_basis']) / 2
    
    df['volume_ma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma']
    
    return df

def detect_signal(df, i):
    """SMC signal"""
    if i < 50:
        return None
    
    close = df['close'].iloc[i]
    ema20 = df['ema20'].iloc[i]
    ema50 = df['ema50'].iloc[i]
    
    recent_high = df['high'].iloc[i-20:i].max()
    recent_low = df['low'].iloc[i-20:i].min()
    
    if close > recent_high and close > ema20 and ema20 > ema50:
        return 'LONG'
    elif close < recent_low and close < ema20 and ema20 < ema50:
        return 'SHORT'
    
    return None

def check_volume_cluster(df, i, lookback=50):
    """Simple volume cluster check"""
    recent = df.iloc[max(0, i-lookback):i+1]
    
    # High volume areas
    vol_mean = recent['volume'].mean()
    vol_std = recent['volume'].std()
    
    # Current price in high-volume zone?
    current_price = df['close'].iloc[i]
    
    # Find prices with high volume
    high_vol_prices = recent[recent['volume'] > vol_mean + 0.5 * vol_std]['close'].values
    
    if len(high_vol_prices) == 0:
        return False
    
    # Check if current price near any high-volume area
    for hvp in high_vol_prices:
        if abs(current_price - hvp) / hvp < 0.01:  # Within 1%
            return True
    
    return False

def check_mtf_alignment(df_1h, current_15m_idx, signal):
    """Multi-timeframe alignment check"""
    # Map 15m index to 1h (4 bars = 1 hour)
    h1_idx = current_15m_idx // 4
    
    if h1_idx < 20 or h1_idx >= len(df_1h):
        return True  # Default allow
    
    # Check 1H trend
    h1_close = df_1h['close'].iloc[h1_idx]
    h1_ema20 = df_1h['ema20'].iloc[h1_idx]
    h1_ema50 = df_1h['ema50'].iloc[h1_idx]
    
    if signal == 'LONG':
        # Require 1H bullish for LONG
        return h1_close > h1_ema20 and h1_ema20 > h1_ema50
    else:
        # Require 1H bearish for SHORT
        return h1_close < h1_ema20 and h1_ema20 < h1_ema50

def simulate_trade(df, entry_idx, signal, entry, sl, tp):
    """Simulate single trade"""
    for j in range(entry_idx+1, min(entry_idx+100, len(df))):
        high, low = df['high'].iloc[j], df['low'].iloc[j]
        
        if signal == 'LONG':
            if high >= tp:
                return CAPITAL * LEVERAGE * ((tp - entry) / entry), 'TP'
            elif low <= sl:
                return CAPITAL * LEVERAGE * ((sl - entry) / entry), 'SL'
        else:
            if low <= tp:
                return CAPITAL * LEVERAGE * ((entry - tp) / entry), 'TP'
            elif high >= sl:
                return CAPITAL * LEVERAGE * ((entry - sl) / entry), 'SL'
    
    return 0, 'TIMEOUT'

def backtest_baseline(df):
    """Baseline: V2 + Squeeze only"""
    df = calculate_indicators(df)
    trades = []
    
    i = 50
    while i < len(df) - 50:
        signal = detect_signal(df, i)
        
        if signal and pd.notna(df['atr'].iloc[i]):
            row = df.iloc[i]
            
            # Squeeze filter
            if row['squeeze_on']:
                i += 1
                continue
            
            # Momentum filter
            if (signal == 'LONG' and row['sqz_mom'] <= 0) or (signal == 'SHORT' and row['sqz_mom'] >= 0):
                i += 1
                continue
            
            # Volume filter
            if row['volume_ratio'] < 1.5:
                i += 1
                continue
            
            # Execute
            entry, atr = row['close'], row['atr']
            sl = entry + (2 * atr * (-1 if signal == 'LONG' else 1))
            tp = entry + (4 * atr * (1 if signal == 'LONG' else -1))
            
            if abs(entry - sl) / entry > 0.08:
                i += 1
                continue
            
            pnl, exit_type = simulate_trade(df, i, signal, entry, sl, tp)
            if exit_type != 'TIMEOUT':
                trades.append(pnl)
                i += 50
            else:
                i += 1
        else:
            i += 1
    
    return trades

def backtest_phase1(df):
    """Phase 1: + Volume Profile"""
    df = calculate_indicators(df)
    trades = []
    
    i = 50
    while i < len(df) - 50:
        signal = detect_signal(df, i)
        
        if signal and pd.notna(df['atr'].iloc[i]):
            row = df.iloc[i]
            
            if row['squeeze_on']:
                i += 1
                continue
            
            if (signal == 'LONG' and row['sqz_mom'] <= 0) or (signal == 'SHORT' and row['sqz_mom'] >= 0):
                i += 1
                continue
            
            if row['volume_ratio'] < 1.5:
                i += 1
                continue
            
            # NEW: Volume cluster check
            if not check_volume_cluster(df, i):
                i += 1
                continue
            
            entry, atr = row['close'], row['atr']
            sl = entry + (2 * atr * (-1 if signal == 'LONG' else 1))
            tp = entry + (4 * atr * (1 if signal == 'LONG' else -1))
            
            if abs(entry - sl) / entry > 0.08:
                i += 1
                continue
            
            pnl, exit_type = simulate_trade(df, i, signal, entry, sl, tp)
            if exit_type != 'TIMEOUT':
                trades.append(pnl)
                i += 50
            else:
                i += 1
        else:
            i += 1
    
    return trades

def backtest_phase2(df, df_1h):
    """Phase 2: + Multi-Timeframe"""
    df = calculate_indicators(df)
    trades = []
    
    i = 50
    while i < len(df) - 50:
        signal = detect_signal(df, i)
        
        if signal and pd.notna(df['atr'].iloc[i]):
            row = df.iloc[i]
            
            if row['squeeze_on']:
                i += 1
                continue
            
            if (signal == 'LONG' and row['sqz_mom'] <= 0) or (signal == 'SHORT' and row['sqz_mom'] >= 0):
                i += 1
                continue
            
            if row['volume_ratio'] < 1.5:
                i += 1
                continue
            
            if not check_volume_cluster(df, i):
                i += 1
                continue
            
            # NEW: MTF alignment
            if not check_mtf_alignment(df_1h, i, signal):
                i += 1
                continue
            
            entry, atr = row['close'], row['atr']
            sl = entry + (2 * atr * (-1 if signal == 'LONG' else 1))
            tp = entry + (4 * atr * (1 if signal == 'LONG' else -1))
            
            if abs(entry - sl) / entry > 0.08:
                i += 1
                continue
            
            pnl, exit_type = simulate_trade(df, i, signal, entry, sl, tp)
            if exit_type != 'TIMEOUT':
                trades.append(pnl)
                i += 50
            else:
                i += 1
        else:
            i += 1
    
    return trades

def analyze_results(trades, name):
    """Analyze backtest results"""
    if not trades:
        return None
    
    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t <= 0]
    
    return {
        'name': name,
        'trades': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': (len(wins) / len(trades)) * 100 if trades else 0,
        'total_pnl': sum(trades),
        'avg_win': np.mean(wins) if wins else 0,
        'avg_loss': np.mean(losses) if losses else 0,
        'avg_trade': np.mean(trades),
        'max_win': max(wins) if wins else 0,
        'max_loss': min(losses) if losses else 0
    }

print("="*80)
print("COMPREHENSIVE BACKTEST - ALL PHASES")
print("="*80)
print()
print(f"Period: {LOOKBACK_DAYS} days")
print(f"Timeframe: {TIMEFRAME}")
print(f"Capital: ${CAPITAL} per asset")
print(f"Leverage: {LEVERAGE}x")
print()

exchange = ccxt.binance()

all_results = {
    'Baseline (V2+Squeeze)': [],
    'Phase 1 (+Volume Profile)': [],
    'Phase 2 (+Multi-Timeframe)': []
}

for asset in ['ARB/USDT', 'OP/USDT']:
    print(f"Testing {asset}...")
    
    # Fetch 15m data
    since = exchange.parse8601((datetime.now() - timedelta(days=LOOKBACK_DAYS)).isoformat())
    ohlcv_15m = exchange.fetch_ohlcv(asset, '15m', since=since, limit=1000)
    df_15m = pd.DataFrame(ohlcv_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Fetch 1h data for MTF
    ohlcv_1h = exchange.fetch_ohlcv(asset, '1h', since=since, limit=1000)
    df_1h = pd.DataFrame(ohlcv_1h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_1h = calculate_indicators(df_1h)
    
    # Run all backtests
    baseline_trades = backtest_baseline(df_15m.copy())
    phase1_trades = backtest_phase1(df_15m.copy())
    phase2_trades = backtest_phase2(df_15m.copy(), df_1h)
    
    all_results['Baseline (V2+Squeeze)'].extend(baseline_trades)
    all_results['Phase 1 (+Volume Profile)'].extend(phase1_trades)
    all_results['Phase 2 (+Multi-Timeframe)'].extend(phase2_trades)
    
    print(f"  ✅ Completed")

print()
print("="*80)
print("RESULTS COMPARISON")
print("="*80)
print()

summary = []
for name, trades in all_results.items():
    result = analyze_results(trades, name)
    if result:
        summary.append(result)

# Print comparison table
print(f"{'Strategy':<30} {'Trades':<8} {'WR%':<8} {'Total P&L':<12} {'Avg/Trade':<12}")
print("-"*80)

for r in summary:
    print(f"{r['name']:<30} {r['trades']:<8} {r['win_rate']:<7.1f}% ${r['total_pnl']:<11.2f} ${r['avg_trade']:<11.2f}")

print()
print("="*80)
print("IMPROVEMENT ANALYSIS")
print("="*80)
print()

baseline = summary[0]
for r in summary[1:]:
    pnl_improvement = ((r['total_pnl'] - baseline['total_pnl']) / abs(baseline['total_pnl']) * 100) if baseline['total_pnl'] != 0 else 0
    wr_improvement = r['win_rate'] - baseline['win_rate']
    
    print(f"{r['name']}:")
    print(f"  Win Rate: {r['win_rate']:.1f}% ({wr_improvement:+.1f}pp vs baseline)")
    print(f"  Total P&L: ${r['total_pnl']:.2f} ({pnl_improvement:+.1f}% vs baseline)")
    print(f"  Avg/Trade: ${r['avg_trade']:.2f}")
    print()

# Recommendation
best = max(summary, key=lambda x: x['total_pnl'])
print("="*80)
print("RECOMMENDATION")
print("="*80)
print()
print(f"🏆 BEST PERFORMER: {best['name']}")
print(f"   Win Rate: {best['win_rate']:.1f}%")
print(f"   Total P&L: ${best['total_pnl']:.2f}")
print(f"   Avg/Trade: ${best['avg_trade']:.2f}")
print()
print("Deploy this version for live trading ✅")

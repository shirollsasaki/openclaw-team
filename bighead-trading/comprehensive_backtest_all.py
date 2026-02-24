"""
COMPREHENSIVE BACKTEST - Strategy 1 V2 Squeeze
Test: BTC, ETH, SOL, ARB, OP
Timeframes: 1m, 5m, 15m
Find what works, what doesn't, path to 80% WR
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt
import warnings
warnings.filterwarnings('ignore')

class Config:
    LEVERAGE = {'BTC': 15, 'ETH': 15, 'SOL': 15, 'ARB': 15, 'OP': 10}
    CAPITAL = 30
    SWING_LENGTH = 3
    LOOKBACK_PERIOD = 20
    RR_RATIO = 2.0
    
    # Current filters
    VOLUME_THRESHOLD = 1.5
    USE_SQUEEZE_FILTER = True
    USE_TREND_FILTER = True
    USE_VOLUME_FILTER = True

def calculate_indicators(df, swing_length=3, lookback=20):
    """Calculate all indicators"""
    df = df.copy()
    
    # Swing Points
    df['swing_high'] = False
    df['swing_low'] = False
    
    for i in range(swing_length, len(df) - swing_length):
        if df['high'].iloc[i] == df['high'].iloc[i-swing_length:i+swing_length+1].max():
            df.loc[df.index[i], 'swing_high'] = True
        if df['low'].iloc[i] == df['low'].iloc[i-swing_length:i+swing_length+1].min():
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
    df['range_high'] = df['high'].rolling(lookback).max()
    df['range_low'] = df['low'].rolling(lookback).min()
    
    # Volume
    df['volume_avg'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_avg']
    
    # Trend
    df['ema_20'] = df['close'].ewm(span=20).mean()
    df['ema_50'] = df['close'].ewm(span=50).mean()
    df['trend_bullish'] = df['close'] > df['ema_20']
    
    # ATR
    high, low, close = df['high'], df['low'], df['close']
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()
    
    # Squeeze
    bb_basis = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    bb_upper = bb_basis + (2.0 * bb_std)
    bb_lower = bb_basis - (2.0 * bb_std)
    
    kc_basis = df['ema_20']
    kc_range = df['atr'] * 1.5
    kc_upper = kc_basis + kc_range
    kc_lower = kc_basis - kc_range
    
    df['squeeze_on'] = (bb_lower > kc_lower) & (bb_upper < kc_upper)
    
    highest = df['high'].rolling(20).max()
    lowest = df['low'].rolling(20).min()
    df['sqz_mom'] = df['close'] - ((highest + lowest) / 2 + bb_basis) / 2
    
    # Signals
    df['signal'] = 0
    for i in range(lookback, len(df)):
        if df['bos_bull'].iloc[i]:
            df.loc[df.index[i], 'signal'] = 1
        elif df['bos_bear'].iloc[i]:
            df.loc[df.index[i], 'signal'] = -1
    
    return df

def check_filters(row, signal):
    """Check all filters"""
    # Squeeze
    if Config.USE_SQUEEZE_FILTER:
        if row['squeeze_on']:
            return False, 'squeeze_on'
        
        if signal == 1 and row['sqz_mom'] <= 0:
            return False, 'sqz_mom'
        if signal == -1 and row['sqz_mom'] >= 0:
            return False, 'sqz_mom'
    
    # Volume
    if Config.USE_VOLUME_FILTER:
        if row['volume_ratio'] < Config.VOLUME_THRESHOLD:
            return False, 'volume'
    
    # Trend
    if Config.USE_TREND_FILTER:
        if signal == 1 and not row['trend_bullish']:
            return False, 'trend'
        if signal == -1 and row['trend_bullish']:
            return False, 'trend'
    
    return True, None

def analyze_trade(df, entry_idx, signal, entry, sl, tp, asset, leverage):
    """Detailed trade analysis"""
    trade = {
        'asset': asset,
        'signal': 'LONG' if signal == 1 else 'SHORT',
        'entry': entry,
        'sl': sl,
        'tp': tp,
        'sl_pct': abs(entry - sl) / entry,
        'entry_time': df.index[entry_idx]
    }
    
    # Simulate trade
    for j in range(entry_idx + 1, min(entry_idx + 200, len(df))):
        high = df['high'].iloc[j]
        low = df['low'].iloc[j]
        
        if signal == 1:
            if high >= tp:
                pnl = Config.CAPITAL * leverage * ((tp - entry) / entry) - 0.002
                trade['exit'] = tp
                trade['exit_type'] = 'TP'
                trade['pnl'] = pnl
                trade['bars_held'] = j - entry_idx
                trade['exit_time'] = df.index[j]
                return trade
            elif low <= sl:
                pnl = Config.CAPITAL * leverage * ((sl - entry) / entry) - 0.002
                trade['exit'] = sl
                trade['exit_type'] = 'SL'
                trade['pnl'] = pnl
                trade['bars_held'] = j - entry_idx
                trade['exit_time'] = df.index[j]
                return trade
        else:
            if low <= tp:
                pnl = Config.CAPITAL * leverage * ((entry - tp) / entry) - 0.002
                trade['exit'] = tp
                trade['exit_type'] = 'TP'
                trade['pnl'] = pnl
                trade['bars_held'] = j - entry_idx
                trade['exit_time'] = df.index[j]
                return trade
            elif high >= sl:
                pnl = Config.CAPITAL * leverage * ((entry - sl) / entry) - 0.002
                trade['exit'] = sl
                trade['exit_type'] = 'SL'
                trade['pnl'] = pnl
                trade['bars_held'] = j - entry_idx
                trade['exit_time'] = df.index[j]
                return trade
    
    return None

def backtest(df, asset, timeframe):
    """Run backtest"""
    df = calculate_indicators(df, Config.SWING_LENGTH, Config.LOOKBACK_PERIOD)
    
    trades = []
    skip_reasons = {}
    i = Config.LOOKBACK_PERIOD
    
    while i < len(df) - 50:
        row = df.iloc[i]
        signal = row['signal']
        
        if signal == 0:
            i += 1
            continue
        
        # Check filters
        passed, reason = check_filters(row, signal)
        if not passed:
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            i += 1
            continue
        
        # Calculate SL/TP
        entry = row['close']
        
        if signal == 1:
            sl = row['range_low'] if row['range_low'] < entry else entry * 0.985
            tp = entry + (entry - sl) * Config.RR_RATIO
        else:
            sl = row['range_high'] if row['range_high'] > entry else entry * 1.015
            tp = entry - (sl - entry) * Config.RR_RATIO
        
        # Validate SL
        sl_pct = abs(entry - sl) / entry
        if sl_pct > 0.10:
            skip_reasons['sl_too_wide'] = skip_reasons.get('sl_too_wide', 0) + 1
            i += 1
            continue
        
        # Analyze trade
        leverage = Config.LEVERAGE.get(asset, 15)
        trade = analyze_trade(df, i, signal, entry, sl, tp, asset, leverage)
        
        if trade:
            # Add context
            trade['volume_ratio'] = row['volume_ratio']
            trade['timeframe'] = timeframe
            trades.append(trade)
            i += trade['bars_held'] + 10
        else:
            i += 1
    
    return trades, skip_reasons

print("="*100)
print("COMPREHENSIVE BACKTEST - Strategy 1 V2 Squeeze")
print("="*100)
print()
print("Testing:")
print("  Assets: BTC, ETH, SOL, ARB, OP")
print("  Timeframes: 1m, 5m, 15m")
print("  Period: Last 30 days (1m/5m) or 90 days (15m)")
print()

exchange = ccxt.binance()

# Test configurations
assets = ['BTC', 'ETH', 'SOL', 'ARB', 'OP']
timeframes = ['1m', '5m', '15m']

results = {}

for timeframe in timeframes:
    print(f"\n{'='*100}")
    print(f"TIMEFRAME: {timeframe}")
    print(f"{'='*100}\n")
    
    # Adjust lookback based on timeframe
    if timeframe == '1m':
        lookback_days = 7
        limit = 10000
    elif timeframe == '5m':
        lookback_days = 14
        limit = 4000
    else:  # 15m
        lookback_days = 90
        limit = 1000
    
    tf_results = {}
    
    for asset in assets:
        try:
            print(f"Testing {asset}/{timeframe}... ", end='', flush=True)
            
            symbol = f"{asset}/USDT"
            since = exchange.parse8601((datetime.now() - timedelta(days=lookback_days)).isoformat())
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            trades, skip_reasons = backtest(df, asset, timeframe)
            
            if trades:
                wins = [t for t in trades if t['pnl'] > 0]
                losses = [t for t in trades if t['pnl'] <= 0]
                
                wr = (len(wins) / len(trades)) * 100
                total_pnl = sum(t['pnl'] for t in trades)
                
                tf_results[asset] = {
                    'trades': len(trades),
                    'wins': len(wins),
                    'losses': len(losses),
                    'wr': wr,
                    'total_pnl': total_pnl,
                    'avg_win': np.mean([t['pnl'] for t in wins]) if wins else 0,
                    'avg_loss': np.mean([t['pnl'] for t in losses]) if losses else 0,
                    'skip_reasons': skip_reasons,
                    'trade_data': trades
                }
                
                print(f"{len(trades)} trades, {wr:.1f}% WR, ${total_pnl:+.2f}")
            else:
                tf_results[asset] = None
                print("No trades")
        
        except Exception as e:
            print(f"Error: {e}")
            tf_results[asset] = None
    
    results[timeframe] = tf_results

# Analysis
print("\n" + "="*100)
print("RESULTS SUMMARY")
print("="*100 + "\n")

print(f"{'Asset':<8} {'TF':<6} {'Trades':<8} {'WR%':<8} {'Total P&L':<12} {'Avg Win':<10} {'Avg Loss':<10}")
print("-"*100)

all_data = []

for timeframe in timeframes:
    for asset in assets:
        result = results[timeframe].get(asset)
        if result:
            print(f"{asset:<8} {timeframe:<6} {result['trades']:<8} {result['wr']:<7.1f}% ${result['total_pnl']:<11.2f} ${result['avg_win']:<9.2f} ${result['avg_loss']:<9.2f}")
            all_data.append({
                'tf': timeframe,
                'asset': asset,
                **result
            })

# Best performers
print("\n" + "="*100)
print("BEST PERFORMERS")
print("="*100 + "\n")

valid_results = [r for r in all_data if r['trades'] >= 5]

if valid_results:
    # Best WR
    best_wr = max(valid_results, key=lambda x: x['wr'])
    print(f"🏆 BEST WIN RATE: {best_wr['asset']}/{best_wr['tf']} - {best_wr['wr']:.1f}% ({best_wr['trades']} trades)")
    
    # Best P&L
    best_pnl = max(valid_results, key=lambda x: x['total_pnl'])
    print(f"💰 BEST PROFIT: {best_pnl['asset']}/{best_pnl['tf']} - ${best_pnl['total_pnl']:+.2f} ({best_pnl['trades']} trades)")
    
    # Best avg profit per trade
    best_avg = max(valid_results, key=lambda x: x['total_pnl'] / x['trades'])
    print(f"⭐ BEST AVG/TRADE: {best_avg['asset']}/{best_avg['tf']} - ${best_avg['total_pnl']/best_avg['trades']:+.2f} per trade")

# Analysis by timeframe
print("\n" + "="*100)
print("TIMEFRAME ANALYSIS")
print("="*100 + "\n")

for timeframe in timeframes:
    tf_data = [r for r in all_data if r['tf'] == timeframe and r['trades'] >= 3]
    
    if tf_data:
        avg_wr = np.mean([r['wr'] for r in tf_data])
        total_trades = sum(r['trades'] for r in tf_data)
        total_pnl = sum(r['total_pnl'] for r in tf_data)
        
        print(f"{timeframe}:")
        print(f"  Assets tested: {len(tf_data)}")
        print(f"  Total trades: {total_trades}")
        print(f"  Avg WR: {avg_wr:.1f}%")
        print(f"  Total P&L: ${total_pnl:+.2f}")
        print(f"  Avg P&L/trade: ${total_pnl/total_trades:+.2f}")
        print()

# Analysis by asset
print("="*100)
print("ASSET ANALYSIS")
print("="*100 + "\n")

for asset in assets:
    asset_data = [r for r in all_data if r['asset'] == asset and r['trades'] >= 3]
    
    if asset_data:
        avg_wr = np.mean([r['wr'] for r in asset_data])
        total_trades = sum(r['trades'] for r in asset_data)
        total_pnl = sum(r['total_pnl'] for r in asset_data)
        
        print(f"{asset}:")
        print(f"  Timeframes tested: {len(asset_data)}")
        print(f"  Total trades: {total_trades}")
        print(f"  Avg WR: {avg_wr:.1f}%")
        print(f"  Total P&L: ${total_pnl:+.2f}")
        
        # Best timeframe for this asset
        best_tf = max(asset_data, key=lambda x: x['wr'])
        print(f"  Best TF: {best_tf['tf']} ({best_tf['wr']:.1f}% WR)")
        print()

# What's working vs not working
print("="*100)
print("WHAT'S WORKING vs NOT WORKING")
print("="*100 + "\n")

profitable = [r for r in all_data if r['total_pnl'] > 0 and r['trades'] >= 5]
unprofitable = [r for r in all_data if r['total_pnl'] <= 0 and r['trades'] >= 5]

print("✅ PROFITABLE SETUPS:")
for r in sorted(profitable, key=lambda x: x['total_pnl'], reverse=True)[:5]:
    print(f"  {r['asset']}/{r['tf']}: {r['wr']:.1f}% WR, ${r['total_pnl']:+.2f} ({r['trades']} trades)")

print("\n❌ LOSING SETUPS:")
for r in sorted(unprofitable, key=lambda x: x['total_pnl'])[:5]:
    print(f"  {r['asset']}/{r['tf']}: {r['wr']:.1f}% WR, ${r['total_pnl']:+.2f} ({r['trades']} trades)")

# Path to 80% WR
print("\n" + "="*100)
print("PATH TO 80% WIN RATE")
print("="*100 + "\n")

high_wr = [r for r in all_data if r['wr'] >= 60 and r['trades'] >= 5]

if high_wr:
    print("🎯 SETUPS WITH 60%+ WR (Close to target):")
    for r in sorted(high_wr, key=lambda x: x['wr'], reverse=True):
        print(f"  {r['asset']}/{r['tf']}: {r['wr']:.1f}% WR, ${r['total_pnl']:+.2f} ({r['trades']} trades)")
    
    best = max(high_wr, key=lambda x: x['wr'])
    print(f"\n💡 BEST CANDIDATE: {best['asset']}/{best['tf']}")
    print(f"   WR: {best['wr']:.1f}% (need +{80-best['wr']:.1f}pp to hit 80%)")
    print(f"   Trades: {best['trades']}")
    print(f"   P&L: ${best['total_pnl']:+.2f}")
else:
    print("⚠️  No setups with 60%+ WR found")
    
    print("\n📊 Current best WR:")
    best_wr_all = max(all_data, key=lambda x: x['wr'] if x['trades'] >= 5 else 0)
    print(f"  {best_wr_all['asset']}/{best_wr_all['tf']}: {best_wr_all['wr']:.1f}% WR")
    print(f"  Gap to 80%: {80 - best_wr_all['wr']:.1f}pp")

# Recommendations
print("\n" + "="*100)
print("RECOMMENDATIONS")
print("="*100 + "\n")

if profitable:
    print("✅ Strategy WORKS on some combinations!")
    print(f"   Found {len(profitable)} profitable setups")
    print()
    
    best_setup = max(profitable, key=lambda x: x['total_pnl'])
    print(f"🚀 BEST SETUP TO DEPLOY:")
    print(f"   Asset: {best_setup['asset']}")
    print(f"   Timeframe: {best_setup['tf']}")
    print(f"   Win Rate: {best_setup['wr']:.1f}%")
    print(f"   Total P&L: ${best_setup['total_pnl']:+.2f}")
    print(f"   Trades: {best_setup['trades']}")
    print()
    
    if best_setup['wr'] < 60:
        print(f"⚠️  WR is {best_setup['wr']:.1f}%, need improvements to hit 80%:")
        print(f"   - Add multi-timeframe filter")
        print(f"   - Add momentum confirmation")
        print(f"   - Optimize SL/TP placement")
        print(f"   - Consider tighter entry criteria")
else:
    print("❌ Strategy needs significant work")
    print("   No profitable setups found")
    print()
    print("🔧 Suggested improvements:")
    print("   1. Change signal logic (current BOS might be too aggressive)")
    print("   2. Add more filters (MTF, momentum, volume spike)")
    print("   3. Optimize SL/TP (2:1 RR might not be ideal)")
    print("   4. Consider different strategy entirely")

print("\n" + "="*100)
print("BACKTEST COMPLETE")
print("="*100)

# Save detailed results
results_df = pd.DataFrame(all_data)
results_df.to_csv('comprehensive_backtest_results.csv', index=False)
print("\nDetailed results saved to: comprehensive_backtest_results.csv")

#!/usr/bin/env python3
"""
ULTIMATE BACKTEST - Daily Directional + Volatility Filter
Tests all strategies and finds the true optimal approach
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

PAIRS = {
    'BTC': 'BTCUSDT',
    'ETH': 'ETHUSDT',
    'SOL': 'SOLUSDT',
    'BNB': 'BNBUSDT',
    'AVAX': 'AVAXUSDT',
    'LINK': 'LINKUSDT',
    'ARB': 'ARBUSDT',
    'OP': 'OPUSDT',
}

async def fetch_data(symbol, interval='15m', hours=168):
    """Fetch OHLCV"""
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)
    
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': start_time,
        'endTime': end_time,
        'limit': 1000
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    except:
        return None

def add_directional_indicators(df):
    """Add directional + volatility indicators"""
    df = df.copy()
    
    # 1. ATR (Volatility)
    df['tr'] = df[['high', 'low', 'close']].apply(
        lambda x: max(x['high'] - x['low'], 
                     abs(x['high'] - x['close']), 
                     abs(x['low'] - x['close'])), 
        axis=1
    )
    df['atr_14'] = df['tr'].rolling(14).mean()
    df['atr_pct'] = (df['atr_14'] / df['close']) * 100
    
    # 2. EMAs (Trend)
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # 3. Trend Direction
    df['uptrend'] = (df['ema_9'] > df['ema_21']) & (df['ema_21'] > df['ema_50'])
    df['downtrend'] = (df['ema_9'] < df['ema_21']) & (df['ema_21'] < df['ema_50'])
    
    # 4. Momentum (Rate of Change)
    df['roc_3'] = ((df['close'] - df['close'].shift(3)) / df['close'].shift(3)) * 100
    df['roc_7'] = ((df['close'] - df['close'].shift(7)) / df['close'].shift(7)) * 100
    
    # 5. Higher Highs / Lower Lows (Swing Structure)
    df['hh'] = df['high'] > df['high'].shift(1)
    df['ll'] = df['low'] < df['low'].shift(1)
    
    # Count consecutive HH or LL (trend strength)
    df['hh_streak'] = 0
    df['ll_streak'] = 0
    
    hh_count = 0
    ll_count = 0
    for i in range(len(df)):
        if df['hh'].iloc[i]:
            hh_count += 1
            ll_count = 0
        elif df['ll'].iloc[i]:
            ll_count += 1
            hh_count = 0
        else:
            hh_count = 0
            ll_count = 0
        
        df.loc[df.index[i], 'hh_streak'] = hh_count
        df.loc[df.index[i], 'll_streak'] = ll_count
    
    return df

def score_asset_directional(df, asset_name, recent_pnl=0):
    """
    DIRECTIONAL + VOLATILITY SCORING
    
    Criteria:
    1. Clear trend direction (40%)
    2. Momentum aligned with trend (30%)
    3. Volatility in sweet spot (20%)
    4. Recent performance (10%)
    """
    
    # Get last row for current state
    latest = df.iloc[-1]
    last_24h = df.tail(96)  # Last 24h on 15m = 96 candles
    
    # 1. TREND DIRECTION (40% weight)
    if latest['uptrend']:
        # Strong uptrend
        trend_score = 1.0
        
        # Bonus for consecutive higher highs
        hh_streak = latest['hh_streak']
        trend_score += min(hh_streak / 10, 0.5)  # Up to +0.5
        
    elif latest['downtrend']:
        # Strong downtrend (we can short, but prefer longs)
        trend_score = 0.3
        
    else:
        # Ranging / choppy - AVOID
        return 0
    
    # 2. MOMENTUM (30% weight)
    roc_3 = latest['roc_3']
    roc_7 = latest['roc_7']
    
    # Check if momentum aligns with trend
    if latest['uptrend'] and roc_3 > 0 and roc_7 > 0:
        # Uptrend + positive momentum = STRONG
        momentum_score = 1.0 + min(roc_7 / 10, 0.5)  # Bonus for strong momentum
    elif latest['downtrend'] and roc_3 < 0 and roc_7 < 0:
        # Downtrend + negative momentum (for shorts)
        momentum_score = 0.5
    else:
        # Momentum diverging from trend = WEAK
        momentum_score = 0.2
    
    # 3. VOLATILITY (20% weight)
    atr_pct = latest['atr_pct']
    
    if 0.3 <= atr_pct <= 0.7:
        # Sweet spot
        volatility_score = 1.0
    elif 0.2 <= atr_pct < 0.3:
        # Too calm
        volatility_score = 0.5
    elif 0.7 < atr_pct <= 1.0:
        # High but manageable
        volatility_score = 0.7
    else:
        # Too extreme
        return 0
    
    # 4. RECENT PERFORMANCE (10% weight)
    performance_score = 1.0 + (recent_pnl / 100)  # 10% PnL = 1.1x multiplier
    
    # COMBINED SCORE
    final_score = (
        trend_score * 0.4 +
        momentum_score * 0.3 +
        volatility_score * 0.2
    ) * performance_score
    
    return final_score

def add_smc_indicators(df, swing_len=3, lookback=20):
    """Add SMC structure (BOS) indicators"""
    df = df.copy()
    
    # Swing points
    df['swing_high'] = False
    df['swing_low'] = False
    for i in range(swing_len, len(df) - swing_len):
        if df['high'].iloc[i] == df['high'].iloc[i-swing_len:i+swing_len+1].max():
            df.loc[df.index[i], 'swing_high'] = True
        if df['low'].iloc[i] == df['low'].iloc[i-swing_len:i+swing_len+1].min():
            df.loc[df.index[i], 'swing_low'] = True
    
    # Structure breaks
    df['bos_bull'] = False
    df['bos_bear'] = False
    last_high = None
    last_low = None
    
    for i in range(len(df)):
        if df['swing_high'].iloc[i]:
            last_high = df['high'].iloc[i]
        if df['swing_low'].iloc[i]:
            last_low = df['low'].iloc[i]
        
        if last_high and last_low:
            if df['close'].iloc[i] > last_high:
                df.loc[df.index[i], 'bos_bull'] = True
            elif df['close'].iloc[i] < last_low:
                df.loc[df.index[i], 'bos_bear'] = True
    
    # Zones
    df['range_high'] = df['high'].rolling(lookback).max()
    df['range_low'] = df['low'].rolling(lookback).min()
    
    # Signals (with directional filter)
    df['signal'] = 0
    for i in range(lookback, len(df)):
        # LONG: BOS bull + uptrend
        if df['bos_bull'].iloc[i] and df['uptrend'].iloc[i]:
            df.loc[df.index[i], 'signal'] = 1
        # SHORT: BOS bear + downtrend
        elif df['bos_bear'].iloc[i] and df['downtrend'].iloc[i]:
            df.loc[df.index[i], 'signal'] = -1
    
    return df

def backtest_strategy(all_data, strategy_name, asset_selection_func):
    """Generic backtest function"""
    capital = 30.0
    starting_capital = capital
    peak_capital = capital
    
    all_trades = []
    daily_capital = [capital]
    daily_selections = []
    asset_pnl_history = {name: 0 for name in all_data.keys()}
    
    # Get date range
    first_timestamp = min(df['timestamp'].min() for df in all_data.values())
    last_timestamp = max(df['timestamp'].max() for df in all_data.values())
    
    current_date = first_timestamp.date()
    end_date = last_timestamp.date()
    
    active_positions = []
    
    while current_date <= end_date:
        day_start = pd.Timestamp(current_date)
        day_end = day_start + pd.Timedelta(days=1)
        
        # Select assets for today
        historical_data = {
            name: df[df['timestamp'] < day_start]
            for name, df in all_data.items()
        }
        
        selected_assets = asset_selection_func(historical_data, asset_pnl_history)
        
        daily_selections.append({
            'date': current_date,
            'assets': selected_assets
        })
        
        # Trade selected assets
        for name in selected_assets:
            if name not in all_data:
                continue
            
            df = all_data[name]
            day_df = df[(df['timestamp'] >= day_start) & (df['timestamp'] < day_end)]
            
            if len(day_df) == 0:
                continue
            
            # Process positions and signals
            for idx, row in day_df.iterrows():
                # Update positions
                for pos in active_positions[:]:
                    if pos['asset'] == name:
                        if pos['direction'] == 'LONG':
                            if row['high'] >= pos['tp']:
                                pnl = pos['size'] * ((pos['tp'] - pos['entry']) / pos['entry']) * 7 - pos['size'] * 0.002
                                capital += pnl
                                asset_pnl_history[name] += pnl
                                all_trades.append({
                                    'asset': name,
                                    'direction': 'LONG',
                                    'entry': pos['entry'],
                                    'exit': pos['tp'],
                                    'pnl': pnl,
                                    'result': 'TP'
                                })
                                active_positions.remove(pos)
                            elif row['low'] <= pos['sl']:
                                pnl = pos['size'] * ((pos['sl'] - pos['entry']) / pos['entry']) * 7 - pos['size'] * 0.002
                                capital += pnl
                                asset_pnl_history[name] += pnl
                                all_trades.append({
                                    'asset': name,
                                    'direction': 'LONG',
                                    'entry': pos['entry'],
                                    'exit': pos['sl'],
                                    'pnl': pnl,
                                    'result': 'SL'
                                })
                                active_positions.remove(pos)
                        else:
                            if row['low'] <= pos['tp']:
                                pnl = pos['size'] * ((pos['entry'] - pos['tp']) / pos['entry']) * 7 - pos['size'] * 0.002
                                capital += pnl
                                asset_pnl_history[name] += pnl
                                all_trades.append({
                                    'asset': name,
                                    'direction': 'SHORT',
                                    'entry': pos['entry'],
                                    'exit': pos['tp'],
                                    'pnl': pnl,
                                    'result': 'TP'
                                })
                                active_positions.remove(pos)
                            elif row['high'] >= pos['sl']:
                                pnl = pos['size'] * ((pos['entry'] - pos['sl']) / pos['entry']) * 7 - pos['size'] * 0.002
                                capital += pnl
                                asset_pnl_history[name] += pnl
                                all_trades.append({
                                    'asset': name,
                                    'direction': 'SHORT',
                                    'entry': pos['entry'],
                                    'exit': pos['sl'],
                                    'pnl': pnl,
                                    'result': 'SL'
                                })
                                active_positions.remove(pos)
                
                # New signals
                if row['signal'] != 0 and len([p for p in active_positions if p['asset'] == name]) < 2 and capital > 1:
                    entry = row['close']
                    
                    if row['signal'] == 1:
                        sl = row['range_low'] if row['range_low'] < entry else entry * 0.985
                        tp = entry + (entry - sl) * 2.0
                        direction = 'LONG'
                    else:
                        sl = row['range_high'] if row['range_high'] > entry else entry * 1.015
                        tp = entry - (sl - entry) * 2.0
                        direction = 'SHORT'
                    
                    sl_dist = abs(entry - sl) / entry
                    if 0.005 <= sl_dist <= 0.05:
                        size = min(capital * 0.03 / sl_dist, capital * 0.15)
                        if size >= 0.1:
                            active_positions.append({
                                'asset': name,
                                'entry': entry,
                                'sl': sl,
                                'tp': tp,
                                'size': size,
                                'direction': direction,
                            })
        
        # Update capital tracking
        if capital > peak_capital:
            peak_capital = capital
        
        daily_capital.append(capital)
        current_date += timedelta(days=1)
    
    # Close remaining
    for pos in active_positions:
        df = all_data[pos['asset']]
        exit_price = df['close'].iloc[-1]
        
        if pos['direction'] == 'LONG':
            pnl = pos['size'] * ((exit_price - pos['entry']) / pos['entry']) * 7 - pos['size'] * 0.002
        else:
            pnl = pos['size'] * ((pos['entry'] - exit_price) / pos['entry']) * 7 - pos['size'] * 0.002
        
        capital += pnl
        all_trades.append({
            'asset': pos['asset'],
            'direction': pos['direction'],
            'entry': pos['entry'],
            'exit': exit_price,
            'pnl': pnl,
            'result': 'EOD'
        })
    
    # Calculate metrics
    max_dd = 0
    running_capital = starting_capital
    running_peak = starting_capital
    for t in all_trades:
        running_capital += t['pnl']
        if running_capital > running_peak:
            running_peak = running_capital
        dd = (running_peak - running_capital) / running_peak * 100
        max_dd = max(max_dd, dd)
    
    wins = [t for t in all_trades if t['pnl'] > 0]
    
    return {
        'strategy': strategy_name,
        'starting_capital': starting_capital,
        'ending_capital': capital,
        'pnl': capital - starting_capital,
        'pnl_pct': (capital / starting_capital - 1) * 100,
        'total_trades': len(all_trades),
        'wins': len(wins),
        'win_rate': len(wins) / len(all_trades) if all_trades else 0,
        'max_dd': max_dd,
        'trades': all_trades,
        'daily_selections': daily_selections
    }

async def run_ultimate_backtest():
    """Test all strategies"""
    
    print("="*90)
    print("🚀 ULTIMATE BACKTEST - Finding True Optimal Strategy")
    print("="*90)
    print("\nFetching 7 days of data for all assets...")
    
    # Fetch data
    all_data = {}
    for name, symbol in PAIRS.items():
        df = await fetch_data(symbol, '15m', 168)
        if df is not None and len(df) >= 100:
            # Add ALL indicators
            df = add_directional_indicators(df)
            df = add_smc_indicators(df)
            all_data[name] = df
            print(f"   ✅ {name}")
        await asyncio.sleep(0.3)
    
    print(f"\n✅ Loaded {len(all_data)} assets\n")
    
    # Test different strategies
    results = []
    
    # Strategy 1: Static (ARB + OP + ETH)
    print("📊 Testing Strategy 1: Static (ARB + OP + ETH)...")
    def static_selector(historical_data, pnl_history):
        return ['ARB', 'OP', 'ETH']
    
    result1 = backtest_strategy(all_data, "Static (ARB+OP+ETH)", static_selector)
    results.append(result1)
    print(f"   Result: ${result1['pnl']:+.2f} ({result1['pnl_pct']:+.2f}%) | {result1['total_trades']} trades | {result1['win_rate']*100:.1f}% WR\n")
    
    # Strategy 2: Daily Directional Filter
    print("📊 Testing Strategy 2: Daily Directional + Volatility Filter...")
    def directional_selector(historical_data, pnl_history):
        scores = {}
        for name, df in historical_data.items():
            if len(df) >= 100:
                score = score_asset_directional(df, name, pnl_history.get(name, 0))
                if score > 0:
                    scores[name] = score
        
        if not scores:
            return []
        
        top_3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        return [name for name, score in top_3]
    
    result2 = backtest_strategy(all_data, "Daily Directional Filter", directional_selector)
    results.append(result2)
    print(f"   Result: ${result2['pnl']:+.2f} ({result2['pnl_pct']:+.2f}%) | {result2['total_trades']} trades | {result2['win_rate']*100:.1f}% WR\n")
    
    # Strategy 3: Momentum Only (no volatility filter)
    print("📊 Testing Strategy 3: Pure Momentum (Last 3 Days Performance)...")
    def momentum_selector(historical_data, pnl_history):
        scores = {}
        for name, df in historical_data.items():
            if len(df) >= 20:
                # Last 3 days return (12 candles on 15m)
                last_3d_return = ((df['close'].iloc[-1] - df['close'].iloc[-12]) / df['close'].iloc[-12]) * 100
                if last_3d_return > -5:  # Not in strong downtrend
                    scores[name] = last_3d_return
        
        if not scores:
            return []
        
        top_3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        return [name for name, score in top_3]
    
    result3 = backtest_strategy(all_data, "Pure Momentum (3-day)", momentum_selector)
    results.append(result3)
    print(f"   Result: ${result3['pnl']:+.2f} ({result3['pnl_pct']:+.2f}%) | {result3['total_trades']} trades | {result3['win_rate']*100:.1f}% WR\n")
    
    # Strategy 4: Uptrend Only (strict directional)
    print("📊 Testing Strategy 4: Strict Uptrend Only (EMA alignment)...")
    def uptrend_only_selector(historical_data, pnl_history):
        uptrending = []
        for name, df in historical_data.items():
            if len(df) >= 50:
                latest = df.iloc[-1]
                if latest['uptrend']:  # EMA 9 > 21 > 50
                    # Score by streak
                    score = latest['hh_streak']
                    uptrending.append((name, score))
        
        if not uptrending:
            return []
        
        top_3 = sorted(uptrending, key=lambda x: x[1], reverse=True)[:3]
        return [name for name, score in top_3]
    
    result4 = backtest_strategy(all_data, "Uptrend Only (EMA)", uptrend_only_selector)
    results.append(result4)
    print(f"   Result: ${result4['pnl']:+.2f} ({result4['pnl_pct']:+.2f}%) | {result4['total_trades']} trades | {result4['win_rate']*100:.1f}% WR\n")
    
    # Strategy 5: Hybrid (Uptrend + Momentum + Volatility)
    print("📊 Testing Strategy 5: Hybrid (Uptrend + Momentum + Vol)...")
    def hybrid_selector(historical_data, pnl_history):
        scores = {}
        for name, df in historical_data.items():
            if len(df) >= 50:
                latest = df.iloc[-1]
                
                # Must be uptrending
                if not latest['uptrend']:
                    continue
                
                # Must have decent volatility
                if not (0.25 <= latest['atr_pct'] <= 0.8):
                    continue
                
                # Must have positive momentum
                if latest['roc_7'] <= 0:
                    continue
                
                # Score by momentum + volatility + streak
                score = (
                    latest['roc_7'] * 0.5 +           # 50% momentum
                    latest['atr_pct'] * 20 * 0.3 +    # 30% volatility (scaled)
                    latest['hh_streak'] * 0.2         # 20% trend strength
                )
                
                scores[name] = score
        
        if not scores:
            return []
        
        top_3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        return [name for name, score in top_3]
    
    result5 = backtest_strategy(all_data, "Hybrid Filter", hybrid_selector)
    results.append(result5)
    print(f"   Result: ${result5['pnl']:+.2f} ({result5['pnl_pct']:+.2f}%) | {result5['total_trades']} trades | {result5['win_rate']*100:.1f}% WR\n")
    
    # Print comparison
    print("="*90)
    print("📊 FINAL COMPARISON - ALL STRATEGIES")
    print("="*90)
    
    # Sort by PnL
    results.sort(key=lambda x: x['pnl'], reverse=True)
    
    print(f"\n{'Rank':<6} {'Strategy':<30} {'Return':<15} {'Trades':<10} {'Win Rate':<12} {'Max DD'}")
    print("-"*90)
    
    for i, r in enumerate(results, 1):
        emoji = "🏆" if i == 1 else "📈" if i <= 3 else "📉"
        print(f"{emoji} #{i:<4} {r['strategy']:<30} ${r['pnl']:+7.2f} ({r['pnl_pct']:+6.2f}%) {r['total_trades']:<10} {r['win_rate']*100:>5.1f}%      {r['max_dd']:>5.1f}%")
    
    # Winner analysis
    winner = results[0]
    print(f"\n{'='*90}")
    print(f"🏆 WINNER: {winner['strategy']}")
    print(f"{'='*90}")
    print(f"\nPerformance:")
    print(f"  Starting Capital: ${winner['starting_capital']:.2f}")
    print(f"  Ending Capital: ${winner['ending_capital']:.2f}")
    print(f"  Profit: ${winner['pnl']:+.2f} ({winner['pnl_pct']:+.2f}%)")
    print(f"  Total Trades: {winner['total_trades']}")
    print(f"  Win Rate: {winner['win_rate']*100:.1f}%")
    print(f"  Max Drawdown: {winner['max_dd']:.1f}%")
    print(f"  Trades/Day: {winner['total_trades']/7:.1f}")
    
    # Asset breakdown for winner
    asset_stats = {}
    for t in winner['trades']:
        asset = t['asset']
        if asset not in asset_stats:
            asset_stats[asset] = {'trades': 0, 'wins': 0, 'pnl': 0}
        asset_stats[asset]['trades'] += 1
        if t['pnl'] > 0:
            asset_stats[asset]['wins'] += 1
        asset_stats[asset]['pnl'] += t['pnl']
    
    print(f"\n  Asset Breakdown:")
    for asset in sorted(asset_stats.keys()):
        stats = asset_stats[asset]
        wr = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
        print(f"    {asset}: {stats['trades']} trades | {stats['wins']} wins ({wr:.0f}%) | ${stats['pnl']:+.2f}")
    
    # Save results
    with open('ultimate_backtest_results.json', 'w') as f:
        json.dump({
            'all_results': [
                {k: v for k, v in r.items() if k != 'trades'}  # Exclude trades for size
                for r in results
            ],
            'winner': winner
        }, f, default=str, indent=2)
    
    print(f"\n💾 Results saved to: ultimate_backtest_results.json")
    
    return results

async def main():
    results = await run_ultimate_backtest()

if __name__ == "__main__":
    asyncio.run(main())

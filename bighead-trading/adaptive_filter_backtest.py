#!/usr/bin/env python3
"""
Adaptive Volatility Filter Backtest
Tests dynamic asset selection based on real-time volatility
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
    """Fetch OHLCV from Binance"""
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

def calculate_atr(df, period=14):
    """Calculate ATR as % of price"""
    df = df.copy()
    df['tr'] = df[['high', 'low', 'close']].apply(
        lambda x: max(x['high'] - x['low'], 
                     abs(x['high'] - x['close']), 
                     abs(x['low'] - x['close'])), 
        axis=1
    )
    atr = df['tr'].rolling(period).mean().iloc[-1]
    atr_pct = (atr / df['close'].iloc[-1]) * 100
    return atr_pct

def count_structure_breaks(df, hours_back=24):
    """Count BOS signals in recent period"""
    lookback = int(hours_back * 4)  # 4 candles per hour on 15m
    recent_df = df.tail(lookback)
    
    swing_len = 3
    bos_count = 0
    
    # Quick swing detection
    for i in range(swing_len, len(recent_df) - swing_len):
        is_swing_high = recent_df['high'].iloc[i] == recent_df['high'].iloc[i-swing_len:i+swing_len+1].max()
        is_swing_low = recent_df['low'].iloc[i] == recent_df['low'].iloc[i-swing_len:i+swing_len+1].min()
        
        if is_swing_high or is_swing_low:
            bos_count += 1
    
    return bos_count

def calculate_volume_score(df):
    """Volume relative to 24h average"""
    recent_vol = df['volume'].tail(4).mean()  # Last hour
    avg_vol = df['volume'].tail(96).mean()     # Last 24h
    
    if avg_vol == 0:
        return 0
    
    return min(recent_vol / avg_vol, 2.0)  # Cap at 2x

def score_asset(df, asset_name, recent_pnl=0):
    """
    ADAPTIVE VOLATILITY FILTER CRITERIA
    
    Returns score based on:
    1. ATR in sweet spot (0.3-0.7%)
    2. Structure quality (clean BOS signals)
    3. Volume strength
    4. Recent performance
    """
    
    # 1. ATR (must be in range)
    atr_pct = calculate_atr(df, period=14)
    
    if atr_pct < 0.3:
        return 0  # Too calm, disqualify
    elif atr_pct > 0.8:
        return 0  # Too volatile, risky
    
    # Optimal range: 0.3-0.7, score based on closeness to 0.5
    atr_score = 1.0 - abs(atr_pct - 0.5) / 0.5
    
    # 2. Structure quality
    bos_count = count_structure_breaks(df, hours_back=24)
    structure_score = min(bos_count / 8.0, 1.0)  # Normalize to 0-1
    
    # 3. Volume score
    volume_score = calculate_volume_score(df)
    
    # 4. Recent performance bonus (if asset was profitable recently)
    performance_multiplier = 1.0 + (recent_pnl * 0.01)  # 1% PnL = 1% boost
    
    # Combined score
    final_score = (
        atr_score * 0.4 +           # 40% weight on volatility
        structure_score * 0.3 +      # 30% weight on structure
        volume_score * 0.3           # 30% weight on volume
    ) * performance_multiplier
    
    return final_score

def add_indicators(df, swing_len=3, lookback=20):
    """Add SMC indicators"""
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
    
    # Signals
    df['signal'] = 0
    for i in range(lookback, len(df)):
        if df['bos_bull'].iloc[i]:
            df.loc[df.index[i], 'signal'] = 1
        elif df['bos_bear'].iloc[i]:
            df.loc[df.index[i], 'signal'] = -1
    
    return df

async def run_adaptive_backtest():
    """Run backtest with daily asset rebalancing"""
    
    print("🔄 Adaptive Volatility Filter Backtest\n")
    print("="*90)
    print("CRITERIA:")
    print("  1. ATR in range: 0.3% - 0.8% (optimal: 0.4-0.6%)")
    print("  2. Structure: 4+ BOS signals in last 24h")
    print("  3. Volume: Above average (recent vs 24h avg)")
    print("  4. Performance: Bonus for recently profitable assets")
    print("  5. Rebalance: Daily at 00:00 UTC, select top 3 assets")
    print("="*90 + "\n")
    
    # Fetch all data
    print("📡 Fetching 7 days of data for all assets...")
    all_data = {}
    for name, symbol in PAIRS.items():
        df = await fetch_data(symbol, '15m', 168)
        if df is not None and len(df) >= 100:
            all_data[name] = df
            print(f"   ✅ {name}: {len(df)} candles")
        await asyncio.sleep(0.3)
    
    print(f"\n✅ Loaded {len(all_data)} assets\n")
    
    # Simulate day-by-day
    capital = 30.0  # $10 per asset × 3 assets
    starting_capital = capital
    daily_capital = [capital]
    peak_capital = capital
    max_dd = 0
    
    all_trades = []
    daily_selections = []
    asset_pnl_history = {name: 0 for name in all_data.keys()}
    
    # Split data into days
    first_timestamp = min(df['timestamp'].min() for df in all_data.values())
    last_timestamp = max(df['timestamp'].max() for df in all_data.values())
    
    current_date = first_timestamp.date()
    end_date = last_timestamp.date()
    
    active_positions = []
    
    while current_date <= end_date:
        day_start = pd.Timestamp(current_date)
        day_end = day_start + pd.Timedelta(days=1)
        
        print(f"📅 {current_date.strftime('%Y-%m-%d')}")
        
        # Score all assets based on data up to today
        scores = {}
        for name, df in all_data.items():
            historical_df = df[df['timestamp'] < day_start]
            if len(historical_df) >= 100:
                recent_pnl = asset_pnl_history.get(name, 0)
                score = score_asset(historical_df, name, recent_pnl)
                if score > 0:
                    atr = calculate_atr(historical_df)
                    bos = count_structure_breaks(historical_df, 24)
                    scores[name] = {
                        'score': score,
                        'atr': atr,
                        'bos': bos
                    }
        
        # Select top 3
        top_assets = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)[:3]
        selected = [name for name, data in top_assets]
        
        if selected:
            print(f"   🎯 Selected: {', '.join(selected)}")
            for name, data in top_assets:
                print(f"      {name}: score={data['score']:.3f} | ATR={data['atr']:.2f}% | BOS={data['bos']}")
        else:
            print(f"   ⏸️  No assets qualified (all outside volatility range)")
        
        daily_selections.append({
            'date': current_date,
            'assets': selected,
            'scores': {name: data for name, data in top_assets}
        })
        
        # Trade selected assets for the day
        day_trades = []
        
        for name in selected:
            df = all_data[name]
            day_df = df[(df['timestamp'] >= day_start) & (df['timestamp'] < day_end)].copy()
            
            if len(day_df) == 0:
                continue
            
            # Add indicators
            full_df = df[df['timestamp'] <= day_end].copy()
            full_df = add_indicators(full_df)
            
            # Get day's candles with signals
            day_signals = full_df[(full_df['timestamp'] >= day_start) & (full_df['timestamp'] < day_end)]
            
            # Simulate trading
            for idx, row in day_signals.iterrows():
                # Check existing positions
                for pos in active_positions[:]:
                    if pos['asset'] == name:
                        if pos['direction'] == 'LONG':
                            if row['high'] >= pos['tp']:
                                pnl = pos['size'] * ((pos['tp'] - pos['entry']) / pos['entry']) * 7 - pos['size'] * 0.002
                                capital += pnl
                                asset_pnl_history[name] = pnl
                                day_trades.append({
                                    'asset': name,
                                    'entry_time': pos['entry_time'],
                                    'exit_time': row['timestamp'],
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
                                asset_pnl_history[name] = pnl
                                day_trades.append({
                                    'asset': name,
                                    'entry_time': pos['entry_time'],
                                    'exit_time': row['timestamp'],
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
                                asset_pnl_history[name] = pnl
                                day_trades.append({
                                    'asset': name,
                                    'entry_time': pos['entry_time'],
                                    'exit_time': row['timestamp'],
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
                                asset_pnl_history[name] = pnl
                                day_trades.append({
                                    'asset': name,
                                    'entry_time': pos['entry_time'],
                                    'exit_time': row['timestamp'],
                                    'direction': 'SHORT',
                                    'entry': pos['entry'],
                                    'exit': pos['sl'],
                                    'pnl': pnl,
                                    'result': 'SL'
                                })
                                active_positions.remove(pos)
                
                # New signal
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
                        size = min(capital * 0.03 / sl_dist, capital * 0.15)  # 3% risk, max 15% per position
                        if size >= 0.1:
                            active_positions.append({
                                'asset': name,
                                'entry': entry,
                                'sl': sl,
                                'tp': tp,
                                'size': size,
                                'direction': direction,
                                'entry_time': row['timestamp']
                            })
        
        all_trades.extend(day_trades)
        
        if day_trades:
            day_pnl = sum(t['pnl'] for t in day_trades)
            print(f"   💰 {len(day_trades)} trades | P&L: ${day_pnl:+.2f}")
        
        # Update drawdown
        if capital > peak_capital:
            peak_capital = capital
        dd = (peak_capital - capital) / peak_capital * 100
        max_dd = max(max_dd, dd)
        
        daily_capital.append(capital)
        print(f"   📊 Capital: ${capital:.2f} | DD: {dd:.1f}%\n")
        
        current_date += timedelta(days=1)
    
    # Close remaining positions
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
            'entry_time': pos['entry_time'],
            'exit_time': df['timestamp'].iloc[-1],
            'direction': pos['direction'],
            'entry': pos['entry'],
            'exit': exit_price,
            'pnl': pnl,
            'result': 'EOD'
        })
    
    # Results
    print("="*90)
    print("📊 ADAPTIVE FILTER BACKTEST RESULTS")
    print("="*90)
    
    print(f"\n💰 CAPITAL")
    print(f"   Starting: ${starting_capital:.2f}")
    print(f"   Ending: ${capital:.2f}")
    print(f"   Profit: ${capital - starting_capital:+.2f} ({(capital/starting_capital - 1)*100:+.2f}%)")
    print(f"   Max Drawdown: {max_dd:.2f}%")
    
    if all_trades:
        wins = [t for t in all_trades if t['pnl'] > 0]
        print(f"\n📈 TRADES")
        print(f"   Total: {len(all_trades)}")
        print(f"   Wins: {len(wins)} ({len(wins)/len(all_trades)*100:.1f}%)")
        print(f"   Avg P&L: ${sum(t['pnl'] for t in all_trades)/len(all_trades):.2f}")
        
        # By asset
        print(f"\n📊 BY ASSET:")
        asset_trades = {}
        for t in all_trades:
            if t['asset'] not in asset_trades:
                asset_trades[t['asset']] = []
            asset_trades[t['asset']].append(t)
        
        for asset in sorted(asset_trades.keys()):
            trades = asset_trades[asset]
            asset_pnl = sum(t['pnl'] for t in trades)
            asset_wins = len([t for t in trades if t['pnl'] > 0])
            print(f"   {asset}: {len(trades)} trades | {asset_wins} wins | ${asset_pnl:+.2f}")
    
    # Save detailed results
    results = {
        'daily_selections': daily_selections,
        'trades': all_trades,
        'daily_capital': daily_capital,
        'final_capital': capital,
        'max_dd': max_dd
    }
    
    with open('adaptive_backtest_results.json', 'w') as f:
        json.dump(results, f, default=str, indent=2)
    
    print(f"\n💾 Results saved to: adaptive_backtest_results.json")
    
    return results

async def main():
    results = await run_adaptive_backtest()
    
    # Generate visualizations
    print(f"\n📊 Generating visualizations...")
    
    # Trade log table
    if results['trades']:
        trades_df = pd.DataFrame(results['trades'])
        trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
        trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])
        trades_df.to_csv('adaptive_trades.csv', index=False)
        print(f"   ✅ Trade log: adaptive_trades.csv")
    
    # Daily selections
    selections_data = []
    for day in results['daily_selections']:
        selections_data.append({
            'date': day['date'],
            'asset_1': day['assets'][0] if len(day['assets']) > 0 else '-',
            'asset_2': day['assets'][1] if len(day['assets']) > 1 else '-',
            'asset_3': day['assets'][2] if len(day['assets']) > 2 else '-',
        })
    
    selections_df = pd.DataFrame(selections_data)
    selections_df.to_csv('daily_asset_selections.csv', index=False)
    print(f"   ✅ Daily selections: daily_asset_selections.csv")

if __name__ == "__main__":
    asyncio.run(main())

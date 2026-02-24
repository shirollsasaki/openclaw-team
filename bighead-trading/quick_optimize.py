#!/usr/bin/env python3
"""
Quick Strategy Optimization - Tests key timeframes only
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta

async def fetch_data(interval, hours=168):
    """Fetch OHLCV from Binance"""
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)
    
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': 'ETHUSDT',
        'interval': interval,
        'startTime': start_time,
        'endTime': end_time,
        'limit': 1000
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
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

def add_indicators(df, swing_len=5, lookback=20):
    """Add all indicators"""
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
    df['trend'] = 0
    last_high = None
    last_low = None
    trend = 0
    
    for i in range(len(df)):
        if df['swing_high'].iloc[i]:
            last_high = df['high'].iloc[i]
        if df['swing_low'].iloc[i]:
            last_low = df['low'].iloc[i]
        
        if last_high and last_low:
            if df['close'].iloc[i] > last_high:
                df.loc[df.index[i], 'bos_bull'] = True
                trend = 1
            elif df['close'].iloc[i] < last_low:
                df.loc[df.index[i], 'bos_bear'] = True
                trend = -1
        
        df.loc[df.index[i], 'trend'] = trend
    
    # Zones
    df['range_high'] = df['high'].rolling(lookback).max()
    df['range_low'] = df['low'].rolling(lookback).min()
    df['eq'] = (df['range_high'] + df['range_low']) / 2
    df['in_discount'] = df['close'] < df['eq']
    df['in_premium'] = df['close'] > df['eq']
    
    # Signals (simplified: structure break + zone confirmation)
    df['signal'] = 0
    for i in range(lookback, len(df)):
        if df['bos_bull'].iloc[i] and df['in_discount'].iloc[i]:
            df.loc[df.index[i], 'signal'] = 1
        elif df['bos_bear'].iloc[i] and df['in_premium'].iloc[i]:
            df.loc[df.index[i], 'signal'] = -1
    
    return df

def backtest(df, leverage=10, risk_pct=0.02, rr=2):
    """Simple backtest"""
    capital = 10.0
    trades = []
    positions = []
    
    for i in range(len(df)):
        # Close positions
        for pos in positions[:]:
            if pos['direction'] == 'LONG':
                if df['high'].iloc[i] >= pos['tp']:
                    pnl = pos['size'] * ((pos['tp'] - pos['entry']) / pos['entry']) * leverage - pos['size'] * 0.002
                    capital += pnl
                    trades.append({'pnl': pnl, 'result': 'WIN'})
                    positions.remove(pos)
                elif df['low'].iloc[i] <= pos['sl']:
                    pnl = pos['size'] * ((pos['sl'] - pos['entry']) / pos['entry']) * leverage - pos['size'] * 0.002
                    capital += pnl
                    trades.append({'pnl': pnl, 'result': 'LOSS'})
                    positions.remove(pos)
            else:
                if df['low'].iloc[i] <= pos['tp']:
                    pnl = pos['size'] * ((pos['entry'] - pos['tp']) / pos['entry']) * leverage - pos['size'] * 0.002
                    capital += pnl
                    trades.append({'pnl': pnl, 'result': 'WIN'})
                    positions.remove(pos)
                elif df['high'].iloc[i] >= pos['sl']:
                    pnl = pos['size'] * ((pos['entry'] - pos['sl']) / pos['entry']) * leverage - pos['size'] * 0.002
                    capital += pnl
                    trades.append({'pnl': pnl, 'result': 'LOSS'})
                    positions.remove(pos)
        
        # New signal
        if df['signal'].iloc[i] != 0 and len(positions) < 2 and capital > 0:
            entry = df['close'].iloc[i]
            if df['signal'].iloc[i] == 1:
                sl = df['range_low'].iloc[i] if df['range_low'].iloc[i] < entry else entry * 0.99
                tp = entry + (entry - sl) * rr
                direction = 'LONG'
            else:
                sl = df['range_high'].iloc[i] if df['range_high'].iloc[i] > entry else entry * 1.01
                tp = entry - (sl - entry) * rr
                direction = 'SHORT'
            
            sl_dist = abs(entry - sl) / entry
            if sl_dist > 0.001:
                size = min(capital * risk_pct / sl_dist, capital)
                if size >= 0.1:
                    positions.append({'entry': entry, 'sl': sl, 'tp': tp, 'size': size, 'direction': direction})
    
    # Close remaining
    for pos in positions:
        if pos['direction'] == 'LONG':
            pnl = pos['size'] * ((df['close'].iloc[-1] - pos['entry']) / pos['entry']) * leverage - pos['size'] * 0.002
        else:
            pnl = pos['size'] * ((pos['entry'] - df['close'].iloc[-1]) / pos['entry']) * leverage - pos['size'] * 0.002
        capital += pnl
        trades.append({'pnl': pnl, 'result': 'EOD'})
    
    if not trades:
        return None
    
    wins = [t for t in trades if t['pnl'] > 0]
    return {
        'total_trades': len(trades),
        'wins': len(wins),
        'win_rate': len(wins) / len(trades),
        'final_capital': capital,
        'pnl': capital - 10,
        'pnl_pct': (capital / 10 - 1) * 100
    }

async def main():
    print("🔄 Quick Optimization - Testing Key Configurations\n")
    
    configs = [
        ('5m', 3, 15, 10, 0.02, 2),
        ('15m', 5, 20, 8, 0.02, 2),
        ('15m', 5, 30, 10, 0.03, 2.5),
        ('30m', 5, 30, 8, 0.02, 2),
        ('1h', 7, 40, 6, 0.03, 2.5),
    ]
    
    results = []
    
    for interval, swing, lookback, lev, risk, rr in configs:
        print(f"📊 Testing {interval} (swing={swing}, lookback={lookback}, lev={lev}x, risk={risk*100:.0f}%, RR={rr})...")
        
        try:
            df = await fetch_data(interval, hours=168)
            df = add_indicators(df, swing, lookback)
            result = backtest(df, lev, risk, rr)
            
            if result:
                result['config'] = f"{interval} | swing={swing} | lookback={lookback} | lev={lev}x | risk={risk*100:.0f}% | RR={rr}:1"
                results.append(result)
                print(f"   ✅ {result['total_trades']} trades | {result['win_rate']*100:.1f}% WR | P&L: ${result['pnl']:+.2f} ({result['pnl_pct']:+.2f}%)\n")
            else:
                print(f"   ❌ No trades\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
    
    print("="*90)
    print("📊 RESULTS - RANKED BY PROFITABILITY")
    print("="*90)
    
    results.sort(key=lambda x: x['pnl'], reverse=True)
    
    for i, r in enumerate(results, 1):
        print(f"\n#{i} {r['config']}")
        print(f"   💰 P&L: ${r['pnl']:+.2f} ({r['pnl_pct']:+.2f}%) over 7 days")
        print(f"   📈 {r['total_trades']} trades | {r['wins']} wins | {r['win_rate']*100:.1f}% win rate")
    
    if results:
        best = results[0]
        print(f"\n{'='*90}")
        print("🏆 BEST CONFIGURATION")
        print(f"   {best['config']}")
        print(f"   Expected: {best['pnl_pct']:+.2f}% return over 7 days")
        print(f"   ~{best['total_trades']/7:.1f} trades per day")

if __name__ == "__main__":
    asyncio.run(main())

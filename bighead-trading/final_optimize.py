#!/usr/bin/env python3
"""
Final Strategy Optimization - More aggressive testing
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

def add_indicators(df, swing_len, lookback, use_zone_filter=False):
    """Add indicators with optional zone filtering"""
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
    
    # Zones (for SL/TP calculation)
    df['range_high'] = df['high'].rolling(lookback).max()
    df['range_low'] = df['low'].rolling(lookback).min()
    df['eq'] = (df['range_high'] + df['range_low']) / 2
    df['in_discount'] = df['close'] < df['eq']
    df['in_premium'] = df['close'] > df['eq']
    
    # Signals
    df['signal'] = 0
    for i in range(lookback, len(df)):
        if use_zone_filter:
            # Conservative: require zone confirmation
            if df['bos_bull'].iloc[i] and df['in_discount'].iloc[i]:
                df.loc[df.index[i], 'signal'] = 1
            elif df['bos_bear'].iloc[i] and df['in_premium'].iloc[i]:
                df.loc[df.index[i], 'signal'] = -1
        else:
            # Aggressive: just structure breaks
            if df['bos_bull'].iloc[i]:
                df.loc[df.index[i], 'signal'] = 1
            elif df['bos_bear'].iloc[i]:
                df.loc[df.index[i], 'signal'] = -1
    
    return df

def backtest(df, leverage, risk_pct, rr, max_dd_pct=30):
    """Backtest with drawdown protection"""
    capital = 10.0
    peak_capital = capital
    trades = []
    positions = []
    stopped_out = False
    
    for i in range(len(df)):
        # Check drawdown
        current_dd = (peak_capital - capital) / peak_capital * 100
        if current_dd > max_dd_pct:
            stopped_out = True
            break
        
        # Close positions
        for pos in positions[:]:
            if pos['direction'] == 'LONG':
                if df['high'].iloc[i] >= pos['tp']:
                    pnl = pos['size'] * ((pos['tp'] - pos['entry']) / pos['entry']) * leverage - pos['size'] * 0.002
                    capital += pnl
                    trades.append({'pnl': pnl, 'result': 'TP'})
                    positions.remove(pos)
                elif df['low'].iloc[i] <= pos['sl']:
                    pnl = pos['size'] * ((pos['sl'] - pos['entry']) / pos['entry']) * leverage - pos['size'] * 0.002
                    capital += pnl
                    trades.append({'pnl': pnl, 'result': 'SL'})
                    positions.remove(pos)
            else:
                if df['low'].iloc[i] <= pos['tp']:
                    pnl = pos['size'] * ((pos['entry'] - pos['tp']) / pos['entry']) * leverage - pos['size'] * 0.002
                    capital += pnl
                    trades.append({'pnl': pnl, 'result': 'TP'})
                    positions.remove(pos)
                elif df['high'].iloc[i] >= pos['sl']:
                    pnl = pos['size'] * ((pos['entry'] - pos['sl']) / pos['entry']) * leverage - pos['size'] * 0.002
                    capital += pnl
                    trades.append({'pnl': pnl, 'result': 'SL'})
                    positions.remove(pos)
        
        if capital > peak_capital:
            peak_capital = capital
        
        # New signal
        if df['signal'].iloc[i] != 0 and len(positions) < 2 and capital > 0.5:
            entry = df['close'].iloc[i]
            if df['signal'].iloc[i] == 1:
                sl = df['range_low'].iloc[i] if df['range_low'].iloc[i] < entry else entry * 0.985
                tp = entry + (entry - sl) * rr
                direction = 'LONG'
            else:
                sl = df['range_high'].iloc[i] if df['range_high'].iloc[i] > entry else entry * 1.015
                tp = entry - (sl - entry) * rr
                direction = 'SHORT'
            
            sl_dist = abs(entry - sl) / entry
            if 0.005 <= sl_dist <= 0.05:  # Between 0.5% and 5% SL
                size = min(capital * risk_pct / sl_dist, capital * 0.5)  # Max 50% of capital per trade
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
    tps = [t for t in trades if t['result'] == 'TP']
    
    max_dd = 0
    running_capital = 10.0
    running_peak = 10.0
    for t in trades:
        running_capital += t['pnl']
        if running_capital > running_peak:
            running_peak = running_capital
        dd = (running_peak - running_capital) / running_peak * 100
        max_dd = max(max_dd, dd)
    
    return {
        'total_trades': len(trades),
        'wins': len(wins),
        'tps': len(tps),
        'win_rate': len(wins) / len(trades),
        'tp_rate': len(tps) / len(trades),
        'final_capital': capital,
        'pnl': capital - 10,
        'pnl_pct': (capital / 10 - 1) * 100,
        'max_dd': max_dd,
        'stopped_out': stopped_out
    }

async def main():
    print("🔄 Final Optimization - Testing Best Timeframes & Configurations\n")
    print("="*90)
    
    configs = [
        # (interval, swing, lookback, leverage, risk%, RR, use_zone_filter, name)
        ('15m', 3, 20, 7, 0.03, 2.0, False, "15m Aggressive"),
        ('15m', 5, 30, 6, 0.025, 2.5, False, "15m Balanced"),
        ('15m', 5, 20, 8, 0.02, 2.0, True, "15m Conservative"),
        ('30m', 3, 25, 6, 0.03, 2.5, False, "30m Aggressive"),
        ('30m', 5, 30, 5, 0.025, 2.0, False, "30m Balanced"),
        ('1h', 5, 30, 5, 0.03, 3.0, False, "1H Swing"),
        ('1h', 7, 40, 4, 0.025, 2.5, True, "1H Conservative"),
    ]
    
    results = []
    
    for interval, swing, lookback, lev, risk, rr, zone_filter, name in configs:
        print(f"📊 Testing: {name}")
        print(f"   Config: {interval} | swing={swing} | lookback={lookback} | {lev}x leverage | {risk*100:.1f}% risk | {rr}:1 RR")
        
        try:
            df = await fetch_data(interval, hours=168)
            df = add_indicators(df, swing, lookback, zone_filter)
            result = backtest(df, lev, risk, rr)
            
            if result and not result['stopped_out']:
                result['name'] = name
                result['config'] = f"{interval} | swing={swing} | lookback={lookback} | {lev}x | {risk*100:.1f}% | {rr}:1 | zones={zone_filter}"
                results.append(result)
                
                emoji = "✅" if result['pnl'] > 0 else "❌"
                print(f"   {emoji} {result['total_trades']} trades | {result['win_rate']*100:.1f}% WR | {result['tp_rate']*100:.1f}% TP rate")
                print(f"   💰 P&L: ${result['pnl']:+.2f} ({result['pnl_pct']:+.2f}%) | Max DD: {result['max_dd']:.1f}%\n")
            else:
                reason = "hit max DD" if result and result['stopped_out'] else "no trades"
                print(f"   ❌ Failed: {reason}\n")
                
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
    
    print("="*90)
    print("📊 FINAL RESULTS - RANKED BY PROFITABILITY")
    print("="*90)
    
    results.sort(key=lambda x: x['pnl'], reverse=True)
    
    for i, r in enumerate(results, 1):
        print(f"\n#{i} 🏆 {r['name']}")
        print(f"   {r['config']}")
        print(f"   💰 Profit: ${r['pnl']:+.2f} ({r['pnl_pct']:+.2f}%) over 7 days")
        print(f"   📈 {r['total_trades']} trades | {r['wins']} wins ({r['win_rate']*100:.1f}%) | {r['tps']} TPs ({r['tp_rate']*100:.1f}%)")
        print(f"   📉 Max Drawdown: {r['max_dd']:.1f}%")
        print(f"   📊 Avg trades/day: {r['total_trades']/7:.1f}")
    
    if results:
        print(f"\n{'='*90}")
        print("🎯 RECOMMENDED CONFIGURATION")
        print(f"{'='*90}")
        
        # Find best balance of profit and risk
        scored = []
        for r in results:
            # Score: profit - drawdown penalty
            if r['pnl'] > 0:
                score = r['pnl_pct'] - r['max_dd'] * 0.5
                scored.append((score, r))
        
        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            best = scored[0][1]
            
            print(f"\n✨ {best['name']}")
            print(f"   {best['config']}")
            print(f"\n   Expected Performance:")
            print(f"      - Profit: ${best['pnl']:+.2f} ({best['pnl_pct']:+.2f}%) over 7 days")
            print(f"      - Win Rate: {best['win_rate']*100:.1f}%")
            print(f"      - TP Hit Rate: {best['tp_rate']*100:.1f}%")
            print(f"      - Max Drawdown: {best['max_dd']:.1f}%")
            print(f"      - Trade Frequency: ~{best['total_trades']/7:.1f} trades per day")
            print(f"\n   With $10 starting capital:")
            print(f"      - Expected ending: ${best['final_capital']:.2f}")
            print(f"      - Worst case DD: ${best['max_dd']/100 * 10:.2f}")
            
        else:
            print("\n⚠️  No profitable configurations found. Strategy needs more work.")

if __name__ == "__main__":
    asyncio.run(main())

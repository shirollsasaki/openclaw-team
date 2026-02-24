#!/usr/bin/env python3
"""
Multi-Asset Strategy Test
Tests 15m aggressive strategy across major crypto pairs to find best performers
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta

# Pairs available on Avantis (Base chain)
PAIRS = {
    'BTC': 'BTCUSDT',
    'ETH': 'ETHUSDT',
    'SOL': 'SOLUSDT',
    'BNB': 'BNBUSDT',
    'MATIC': 'MATICUSDT',
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
    except Exception as e:
        print(f"   ❌ Error fetching {symbol}: {e}")
        return None

def calculate_volatility(df):
    """Calculate average true range (ATR) as volatility measure"""
    df = df.copy()
    df['tr'] = df[['high', 'low', 'close']].apply(
        lambda x: max(x['high'] - x['low'], 
                     abs(x['high'] - x['close']), 
                     abs(x['low'] - x['close'])), 
        axis=1
    )
    atr = df['tr'].rolling(14).mean().iloc[-1]
    atr_pct = (atr / df['close'].iloc[-1]) * 100
    return atr_pct

def add_indicators(df, swing_len=3, lookback=20):
    """Add indicators - optimized 15m aggressive config"""
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
    
    # Signals (aggressive - no zone filter)
    df['signal'] = 0
    for i in range(lookback, len(df)):
        if df['bos_bull'].iloc[i]:
            df.loc[df.index[i], 'signal'] = 1
        elif df['bos_bear'].iloc[i]:
            df.loc[df.index[i], 'signal'] = -1
    
    return df

def backtest(df, leverage=7, risk_pct=0.03, rr=2.0):
    """Backtest with 15m aggressive config"""
    capital = 10.0
    peak_capital = capital
    trades = []
    positions = []
    
    for i in range(len(df)):
        # Check drawdown
        current_dd = (peak_capital - capital) / peak_capital * 100
        if current_dd > 30:  # 30% max DD
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
            if 0.005 <= sl_dist <= 0.05:
                size = min(capital * risk_pct / sl_dist, capital * 0.5)
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
    
    # Calculate max drawdown
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
        'win_rate': len(wins) / len(trades),
        'final_capital': capital,
        'pnl': capital - 10,
        'pnl_pct': (capital / 10 - 1) * 100,
        'max_dd': max_dd,
        'avg_trade': (capital - 10) / len(trades)
    }

async def test_asset(name, symbol):
    """Test single asset"""
    print(f"📊 Testing {name}...")
    
    df = await fetch_data(symbol, '15m', 168)
    if df is None or len(df) < 50:
        print(f"   ❌ Insufficient data\n")
        return None
    
    # Calculate volatility
    volatility = calculate_volatility(df)
    
    # Run backtest
    df = add_indicators(df, swing_len=3, lookback=20)
    result = backtest(df, leverage=7, risk_pct=0.03, rr=2.0)
    
    if result:
        result['asset'] = name
        result['symbol'] = symbol
        result['volatility'] = volatility
        result['price'] = df['close'].iloc[-1]
        
        emoji = "✅" if result['pnl'] > 0 else "❌"
        print(f"   {emoji} {result['total_trades']} trades | {result['win_rate']*100:.1f}% WR | ATR: {volatility:.2f}%")
        print(f"   💰 P&L: ${result['pnl']:+.2f} ({result['pnl_pct']:+.2f}%) | Max DD: {result['max_dd']:.1f}%\n")
    else:
        print(f"   ❌ No trades generated\n")
    
    return result

async def main():
    print("🔄 Multi-Asset Strategy Test - 15m Aggressive Config\n")
    print("Testing across major crypto pairs to find best performers...")
    print("="*90 + "\n")
    
    results = []
    
    # Test all pairs
    for name, symbol in PAIRS.items():
        result = await test_asset(name, symbol)
        if result:
            results.append(result)
        await asyncio.sleep(0.5)  # Rate limit
    
    if not results:
        print("❌ No results")
        return
    
    print("="*90)
    print("📊 RESULTS - RANKED BY PROFITABILITY")
    print("="*90)
    
    # Sort by profit
    results.sort(key=lambda x: x['pnl'], reverse=True)
    
    for i, r in enumerate(results, 1):
        stars = "🏆" if i <= 3 else "📈"
        print(f"\n#{i} {stars} {r['asset']} ({r['symbol']})")
        print(f"   💰 Profit: ${r['pnl']:+.2f} ({r['pnl_pct']:+.2f}%) over 7 days")
        print(f"   📈 {r['total_trades']} trades | {r['wins']} wins | {r['win_rate']*100:.1f}% WR")
        print(f"   📉 Max DD: {r['max_dd']:.1f}% | Volatility (ATR): {r['volatility']:.2f}%")
        print(f"   💵 Avg/trade: ${r['avg_trade']:+.2f} | Price: ${r['price']:.2f}")
    
    # Analyze results
    print(f"\n{'='*90}")
    print("🔍 ANALYSIS")
    print("="*90)
    
    profitable = [r for r in results if r['pnl'] > 0]
    print(f"\n✅ Profitable Assets: {len(profitable)}/{len(results)}")
    
    if profitable:
        avg_profit = sum(r['pnl_pct'] for r in profitable) / len(profitable)
        avg_wr = sum(r['win_rate'] for r in profitable) / len(profitable)
        avg_vol = sum(r['volatility'] for r in profitable) / len(profitable)
        
        print(f"   Average Profit: {avg_profit:.2f}%")
        print(f"   Average Win Rate: {avg_wr*100:.1f}%")
        print(f"   Average Volatility: {avg_vol:.2f}%")
    
    # Best volatility pairs
    print(f"\n📊 Highest Volatility Assets:")
    by_vol = sorted(results, key=lambda x: x['volatility'], reverse=True)
    for r in by_vol[:3]:
        print(f"   {r['asset']}: {r['volatility']:.2f}% ATR | P&L: ${r['pnl']:+.2f}")
    
    # Best performers
    if profitable:
        print(f"\n{'='*90}")
        print("🏆 TOP 3 RECOMMENDED ASSETS")
        print("="*90)
        
        for i, r in enumerate(profitable[:3], 1):
            print(f"\n#{i} {r['asset']}")
            print(f"   Expected: {r['pnl_pct']:+.2f}% return over 7 days")
            print(f"   Win Rate: {r['win_rate']*100:.1f}%")
            print(f"   Max Drawdown: {r['max_dd']:.1f}%")
            print(f"   Volatility: {r['volatility']:.2f}% (higher = more opportunities)")
            print(f"   Trade Frequency: ~{r['total_trades']/7:.1f} trades/day")
        
        # Multi-asset strategy
        print(f"\n{'='*90}")
        print("💡 MULTI-ASSET STRATEGY")
        print("="*90)
        
        top3 = profitable[:3]
        total_pnl = sum(r['pnl'] for r in top3)
        total_pnl_pct = (total_pnl / (10 * len(top3))) * 100
        avg_dd = sum(r['max_dd'] for r in top3) / len(top3)
        total_trades = sum(r['total_trades'] for r in top3)
        
        print(f"\n💰 Trading Top 3 Assets with $10 Each ($30 total):")
        print(f"   Combined Profit: ${total_pnl:+.2f} ({total_pnl_pct:+.2f}%)")
        print(f"   Total Trades: {total_trades} ({total_trades/7:.1f}/day across all assets)")
        print(f"   Average Max DD: {avg_dd:.1f}%")
        print(f"   Diversification: Reduces risk, smooths returns")
        
        print(f"\n📋 Allocation:")
        for r in top3:
            print(f"   - {r['asset']}: $10 → ${r['final_capital']:.2f} ({r['pnl_pct']:+.2f}%)")

if __name__ == "__main__":
    asyncio.run(main())

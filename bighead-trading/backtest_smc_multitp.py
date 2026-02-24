#!/usr/bin/env python3
"""
Backtest: V2 vs SMC Multi-TP Strategy
1. 7-day backtest comparison
2. Today's live sim performance check
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime
from smc_multitp_strategy import SMCMultiTPStrategy

# V2 trades from today
V2_TRADES_TODAY = [
    {
        'asset': 'ETH',
        'entry_time': '2026-02-21 15:08:37',
        'direction': 'LONG',
        'entry': 1971.77,
        'exit': 1971.77,
        'pnl': -0.003
    },
    {
        'asset': 'OP',
        'entry_time': '2026-02-21 14:59:43',
        'direction': 'LONG',
        'entry': 0.1344,
        'exit': 0.1298,
        'pnl': -2.59
    }
]

SYMBOL_MAP = {
    'ETH': 'ETHUSDT',
    'OP': 'OPUSDT',
    'ARB': 'ARBUSDT'
}

async def fetch_candles(asset, days=7):
    """Fetch historical candles"""
    symbol = SYMBOL_MAP[asset]
    
    candles_per_day = 96
    limit = candles_per_day * days + 100
    
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': '15m',
        'limit': min(limit, 1000)
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as resp:
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
        print(f"Error fetching {asset}: {e}")
        return None

async def fetch_candles_at_time(asset, target_time, limit=100):
    """Fetch candles around a specific time"""
    symbol = SYMBOL_MAP[asset]
    
    target_dt = datetime.strptime(target_time, '%Y-%m-%d %H:%M:%S')
    end_ms = int(target_dt.timestamp() * 1000)
    
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': '15m',
        'endTime': end_ms,
        'limit': limit
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as resp:
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
        print(f"Error fetching {asset}: {e}")
        return None

async def run_backtest():
    """Run complete backtest"""
    print("="*70)
    print("BACKTEST: V2 vs SMC Multi-TP Strategy")
    print("="*70)
    print("Period: Last 7 days")
    print("Assets: ARB, OP, ETH")
    print("="*70)
    
    # Fetch data
    print("\n📥 Fetching data...")
    data = {}
    for asset in ['ARB', 'OP', 'ETH']:
        df = await fetch_candles(asset, days=7)
        if df is not None:
            data[asset] = df
            print(f"   {asset}: {len(df)} candles")
    
    # Run backtests
    print("\n🔬 Running 7-day backtest...")
    
    strategy = SMCMultiTPStrategy()
    
    results = {}
    for asset in ['ARB', 'OP', 'ETH']:
        if asset not in data:
            continue
        
        df = data[asset]
        trades, equity = strategy.backtest(df, capital=10.0)
        
        results[asset] = {
            'trades': trades,
            'final_equity': equity,
            'total_trades': len(trades),
            'winners': len([t for t in trades if t['pnl'] > 0]),
            'total_pnl': sum([t['pnl'] for t in trades])
        }
    
    # Print 7-day results
    print("\n" + "="*70)
    print("7-DAY BACKTEST RESULTS")
    print("="*70)
    
    for asset in ['ARB', 'OP', 'ETH']:
        if asset not in results:
            continue
        
        r = results[asset]
        wr = (r['winners'] / r['total_trades'] * 100) if r['total_trades'] > 0 else 0
        roi = ((r['final_equity'] - 10) / 10 * 100)
        
        print(f"\n📊 {asset}")
        print("-"*70)
        print(f"  Trades: {r['total_trades']}")
        print(f"  Win Rate: {wr:.1f}%")
        print(f"  Total P&L: ${r['total_pnl']:+.2f}")
        print(f"  Final Equity: ${r['final_equity']:.2f}")
        print(f"  ROI: {roi:+.1f}%")
    
    # Overall summary
    total_pnl = sum([r['total_pnl'] for r in results.values()])
    total_trades = sum([r['total_trades'] for r in results.values()])
    total_winners = sum([r['winners'] for r in results.values()])
    overall_wr = (total_winners / total_trades * 100) if total_trades > 0 else 0
    
    print("\n" + "="*70)
    print("OVERALL (All Assets)")
    print("="*70)
    print(f"Total Trades: {total_trades}")
    print(f"Win Rate: {overall_wr:.1f}%")
    print(f"Total P&L: ${total_pnl:+.2f}")
    print(f"ROI: {(total_pnl / 30 * 100):+.1f}%")
    
    # Now check today's trades
    print("\n" + "="*70)
    print("TODAY'S LIVE SIM ANALYSIS")
    print("="*70)
    print(f"\nV2 took 2 trades today. What if it used SMC Multi-TP?")
    
    for trade in V2_TRADES_TODAY:
        print(f"\n{'='*70}")
        print(f"Checking: {trade['direction']} {trade['asset']} @ {trade['entry_time']}")
        print(f"V2 Result: Entry ${trade['entry']:.4f} → Exit ${trade['exit']:.4f} | P&L: ${trade['pnl']:.2f}")
        print('='*70)
        
        # Fetch data at that time
        df = await fetch_candles_at_time(trade['asset'], trade['entry_time'], limit=150)
        if df is None:
            print("❌ Could not fetch data")
            continue
        
        print(f"Fetched {len(df)} candles")
        
        # Add indicators
        df = strategy.add_indicators(df)
        
        # Check if signal would fire
        signal_row = df.iloc[-1]
        
        print(f"\nAt entry time ({signal_row['timestamp']}):")
        print(f"  Close: ${signal_row['close']:.4f}")
        print(f"  ALMA Close: ${signal_row['alma_close']:.4f}")
        print(f"  ALMA Open: ${signal_row['alma_open']:.4f}")
        print(f"  Signal: {signal_row['signal']}")
        
        would_enter = False
        if trade['direction'] == 'LONG' and signal_row['signal'] == 1:
            would_enter = True
        elif trade['direction'] == 'SHORT' and signal_row['signal'] == -1:
            would_enter = True
        
        if would_enter:
            print(f"\n✅ SMC Multi-TP WOULD TAKE THIS TRADE")
            
            # Calculate what would have happened
            entry = signal_row['close']
            tp1, tp2, tp3, sl = strategy.calculate_tp_sl(entry, trade['direction'])
            
            print(f"\nTP/SL Levels:")
            print(f"  Entry: ${entry:.4f}")
            print(f"  TP1 (1%): ${tp1:.4f}")
            print(f"  TP2 (1.5%): ${tp2:.4f}")
            print(f"  TP3 (2%): ${tp3:.4f}")
            print(f"  SL (0.5%): ${sl:.4f}")
            
            # Simulate what would happen
            # For now, just show the levels
            # In reality, we'd need to check subsequent candles
            
            print(f"\nV2 actual result: ${trade['pnl']:.2f}")
            print(f"SMC Multi-TP: Would manage position with 3 TPs")
            
        else:
            print(f"\n❌ SMC Multi-TP WOULD NOT TAKE THIS TRADE")
            print(f"   (Signal mismatch)")
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\n7-Day Backtest:")
    print(f"  SMC Multi-TP: {total_trades} trades, ${total_pnl:+.2f} ({(total_pnl/30*100):+.1f}% ROI)")
    print(f"  Win Rate: {overall_wr:.1f}%")
    
    print(f"\nToday's Live Sim:")
    print(f"  V2: -$2.59")
    print(f"  SMC Multi-TP: Would need to simulate to compare")

if __name__ == "__main__":
    asyncio.run(run_backtest())

#!/usr/bin/env python3
"""
Check if V2's actual trades today would have passed Squeeze filter
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime
from squeeze_momentum import SqueezeMomentumIndicator

# V2's actual trades today
TRADES = [
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

async def fetch_candles_at_time(asset, target_time, limit=100):
    """Fetch candles around a specific time"""
    symbol = SYMBOL_MAP[asset]
    
    # Parse target time
    target_dt = datetime.strptime(target_time, '%Y-%m-%d %H:%M:%S')
    
    # Get end time (target + buffer)
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

async def check_trade(trade):
    """Check if a trade would pass Squeeze filter"""
    print(f"\n{'='*70}")
    print(f"Checking: {trade['direction']} {trade['asset']} @ {trade['entry_time']}")
    print(f"Entry: ${trade['entry']:.4f} | P&L: ${trade['pnl']:.2f}")
    print('='*70)
    
    # Fetch data
    df = await fetch_candles_at_time(trade['asset'], trade['entry_time'], limit=100)
    if df is None:
        print("❌ Could not fetch data")
        return None
    
    print(f"Fetched {len(df)} candles")
    
    # Calculate Squeeze Momentum
    sqz = SqueezeMomentumIndicator()
    df = sqz.calculate(df)
    
    # Get the signal candle (last one before entry)
    signal_row = df.iloc[-1]
    
    print(f"\nAt entry time ({signal_row['timestamp']}):")
    print(f"  Close: ${signal_row['close']:.4f}")
    print(f"  Squeeze On: {signal_row['sqz_on']}")
    print(f"  Squeeze Off: {signal_row['sqz_off']}")
    print(f"  No Squeeze: {signal_row['no_sqz']}")
    print(f"  Momentum: {signal_row['sqz_mom']:.6f}")
    print(f"  Mom Color: {signal_row['sqz_mom_color']}")
    
    # Check if trade would pass filter
    passed = False
    reason = ""
    
    if not signal_row['sqz_off']:
        reason = "❌ FILTERED: Squeeze not OFF (no breakout signal)"
    elif trade['direction'] == 'LONG' and signal_row['sqz_mom'] <= 0:
        reason = "❌ FILTERED: LONG trade but momentum is negative/zero"
    elif trade['direction'] == 'SHORT' and signal_row['sqz_mom'] >= 0:
        reason = "❌ FILTERED: SHORT trade but momentum is positive/zero"
    else:
        reason = "✅ PASSED: Squeeze OFF + momentum aligned"
        passed = True
    
    print(f"\n{reason}")
    
    return {
        'trade': trade,
        'passed': passed,
        'reason': reason,
        'sqz_on': signal_row['sqz_on'],
        'sqz_off': signal_row['sqz_off'],
        'sqz_mom': signal_row['sqz_mom']
    }

async def main():
    print("="*70)
    print("V2 TRADE ANALYSIS: Would Squeeze Filter Have Helped?")
    print("="*70)
    print(f"\nAnalyzing {len(TRADES)} trades from today's live sim...")
    
    results = []
    for trade in TRADES:
        result = await check_trade(trade)
        if result:
            results.append(result)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed_trades = [r for r in results if r['passed']]
    filtered_trades = [r for r in results if not r['passed']]
    
    print(f"\nTotal trades: {len(results)}")
    print(f"Would PASS filter: {len(passed_trades)}")
    print(f"Would be FILTERED: {len(filtered_trades)}")
    
    # Calculate P&L if filter was active
    original_pnl = sum([t['pnl'] for t in TRADES])
    filtered_pnl = sum([r['trade']['pnl'] for r in passed_trades])
    
    print(f"\nP&L Comparison:")
    print(f"  Without Squeeze: ${original_pnl:.2f}")
    print(f"  With Squeeze: ${filtered_pnl:.2f}")
    print(f"  Difference: ${filtered_pnl - original_pnl:+.2f}")
    
    if len(filtered_trades) > 0:
        print(f"\n🎯 Trades that would have been AVOIDED:")
        for r in filtered_trades:
            t = r['trade']
            print(f"  - {t['direction']} {t['asset']} @ ${t['entry']:.4f} | P&L: ${t['pnl']:.2f}")
            print(f"    Reason: {r['reason']}")
    
    if filtered_pnl > original_pnl:
        print(f"\n✅ Squeeze filter would have IMPROVED V2 by ${filtered_pnl - original_pnl:+.2f}")
    elif filtered_pnl == original_pnl:
        print(f"\n➖ Squeeze filter would have had NO EFFECT on V2")
    else:
        print(f"\n❌ Squeeze filter would have made V2 WORSE by ${filtered_pnl - original_pnl:.2f}")

if __name__ == "__main__":
    asyncio.run(main())

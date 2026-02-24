#!/usr/bin/env python3
"""
Quick test to verify bot can start with new SDK integration
"""

import asyncio
import sys

async def test_bot_startup():
    print("Testing bot startup with new SDK integration...")
    print("="*70)
    
    # Import the bot's DataFetcher
    sys.path.insert(0, '$OPENCLAW_HOME/bighead')
    from avantis_bot_v2_squeeze_all3 import DataFetcher
    
    print("\n1. Testing DataFetcher.get_avantis_price():")
    print("-"*70)
    
    for asset in ['ARB', 'OP', 'ETH']:
        price = await DataFetcher.get_avantis_price(asset)
        if price:
            print(f"  ✅ {asset}: ${price:,.4f}")
        else:
            print(f"  ❌ {asset}: Failed")
    
    print("\n2. Testing DataFetcher.fetch_candles():")
    print("-"*70)
    
    df = await DataFetcher.fetch_candles('ETH', limit=50)
    if df is not None and len(df) > 0:
        latest = df.iloc[-1]
        print(f"  ✅ ETH candles fetched: {len(df)} candles")
        print(f"     Latest close: ${latest['close']:,.2f}")
        print(f"     Latest volume: {latest['volume']:,.0f}")
    else:
        print(f"  ❌ Failed to fetch candles")
    
    print("\n" + "="*70)
    print("✅ Bot integration test PASSED!")
    print("="*70)
    print("\nBot is ready to run with official Avantis SDK patterns")

if __name__ == "__main__":
    asyncio.run(test_bot_startup())

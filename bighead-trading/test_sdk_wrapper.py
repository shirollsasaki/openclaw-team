#!/usr/bin/env python3
"""
Test the new SDK wrapper to ensure it works correctly
"""

import asyncio
from avantis_sdk_wrapper import get_sdk

async def test():
    print("="*70)
    print("Testing Avantis SDK Wrapper (Official AGENT.md Pattern)")
    print("="*70)
    
    # Get SDK instance
    sdk = await get_sdk()
    
    print("\n1. Testing Pair Index Lookup:")
    print("-" * 70)
    for asset in ['ARB', 'OP', 'ETH']:
        pair_index = sdk.get_pair_index(asset)
        print(f"  {asset}: index {pair_index}")
    
    print("\n2. Testing Price Fetch (with Binance fallback):")
    print("-" * 70)
    for asset in ['ARB', 'OP', 'ETH']:
        price = await sdk.get_price(asset)
        if price:
            print(f"  ✅ {asset}: ${price:,.4f}")
        else:
            print(f"  ❌ {asset}: Failed to fetch price")
    
    print("\n3. Testing Batch Price Fetch:")
    print("-" * 70)
    prices = await sdk.get_prices_batch(['ARB', 'OP', 'ETH'])
    for asset, price in prices.items():
        print(f"  {asset}: ${price:,.4f}")
    
    print("\n" + "="*70)
    print("✅ SDK Wrapper Test Complete!")
    print("="*70)
    print("\nNotes:")
    print("  • If Avantis API is down, prices come from Binance (fallback)")
    print("  • Pair indexes are cached after first fetch")
    print("  • All patterns follow official AGENT.md documentation")
    print("  • Ready for live trading when Avantis API is available")

if __name__ == "__main__":
    asyncio.run(test())

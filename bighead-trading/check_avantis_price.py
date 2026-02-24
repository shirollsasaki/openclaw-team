#!/usr/bin/env python3
"""Check ARB price on Avantis vs Binance"""

import asyncio
from avantis_trader_sdk import FeedClient
import aiohttp

async def main():
    print("🔍 Comparing ARB prices\n")
    
    # Get Avantis price
    print("1️⃣ Avantis Feed (Pyth):")
    try:
        feed_client = FeedClient()
        price_data = await feed_client.get_price_update_data(pair_index=4)  # ARB
        
        # Try different conversions
        raw_price = price_data.pro.price
        
        # Pyth prices are typically in 8 decimals or already formatted
        avantis_price_v1 = raw_price / 1e10
        avantis_price_v2 = raw_price / 1e8
        avantis_price_v3 = raw_price  # Already formatted
        
        print(f"   Raw: {raw_price}")
        print(f"   ÷ 1e10: ${avantis_price_v1:.6f}")
        print(f"   ÷ 1e8: ${avantis_price_v2:.6f}")
        print(f"   Direct: ${avantis_price_v3:.6f}\n")
        
        # Use the one that makes sense
        avantis_price = avantis_price_v3 if avantis_price_v3 > 0.01 else avantis_price_v2
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    # Get Binance price
    print("2️⃣ Binance:")
    url = "https://api.binance.com/api/v3/ticker/price"
    params = {'symbol': 'ARBUSDT'}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            binance_price = float(data['price'])
            print(f"   ARB/USDT: ${binance_price:.6f}\n")
    
    # Compare
    try:
        diff = abs(avantis_price - binance_price)
        diff_pct = (diff / binance_price) * 100
        
        print(f"3️⃣ Comparison:")
        print(f"   Difference: ${diff:.6f} ({diff_pct:.2f}%)")
        
        if diff_pct > 1:
            print(f"   ⚠️  Significant difference! Should use Avantis price for trading.")
        else:
            print(f"   ✅ Prices are close enough")
    except:
        pass

asyncio.run(main())

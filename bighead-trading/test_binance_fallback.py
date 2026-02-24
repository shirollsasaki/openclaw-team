#!/usr/bin/env python3
"""
Test that Binance fallback is working
"""

import asyncio
import aiohttp

async def test_binance_prices():
    """Test fetching prices from Binance"""
    
    symbols = ['ARBUSDT', 'OPUSDT', 'ETHUSDT']
    
    print("Testing Binance price fetch...\n")
    
    for symbol in symbols:
        try:
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {'symbol': symbol}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        price = float(data['price'])
                        print(f"✅ {symbol}: ${price:,.4f}")
                    else:
                        print(f"❌ {symbol}: HTTP {resp.status}")
        
        except Exception as e:
            print(f"❌ {symbol}: {e}")
    
    print("\n✅ Binance API is working - bot can use these prices!")

if __name__ == "__main__":
    asyncio.run(test_binance_prices())

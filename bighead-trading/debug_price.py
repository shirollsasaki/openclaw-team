#!/usr/bin/env python3
"""Debug ARB price fetching"""

import asyncio
import aiohttp

async def test_binance():
    print("🔍 Testing Binance API for ARB price\n")
    
    # Test current price
    url = "https://api.binance.com/api/v3/ticker/price"
    params = {'symbol': 'ARBUSDT'}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            print(f"Current ARB price (ticker):")
            print(f"   {data}")
            print(f"   Price: ${float(data['price']):.4f}\n")
    
    # Test 15m candles
    url2 = "https://api.binance.com/api/v3/klines"
    params2 = {
        'symbol': 'ARBUSDT',
        'interval': '15m',
        'limit': 5
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url2, params=params2) as resp:
            data = await resp.json()
            print(f"Last 5 candles (15m):")
            for candle in data:
                timestamp = candle[0]
                open_p = float(candle[1])
                high = float(candle[2])
                low = float(candle[3])
                close = float(candle[4])
                
                from datetime import datetime
                dt = datetime.fromtimestamp(timestamp/1000)
                
                print(f"   {dt} | O: ${open_p:.4f} H: ${high:.4f} L: ${low:.4f} C: ${close:.4f}")

asyncio.run(test_binance())

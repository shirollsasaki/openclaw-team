"""
Quick check: Is the market suitable for grid trading?
"""
import asyncio
import aiohttp

async def check():
    print("Checking if market is suitable for grid trading...")
    print()
    
    # Check ARB
    async with aiohttp.ClientSession() as session:
        url = "https://api.binance.com/api/v3/klines?symbol=ARBUSDT&interval=1h&limit=24"
        async with session.get(url) as resp:
            candles = await resp.json()
    
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    closes = [float(c[4]) for c in candles]
    
    range_high = max(highs)
    range_low = min(lows)
    range_size = (range_high - range_low) / range_low
    current = closes[-1]
    
    print(f"ARB 24h Analysis:")
    print(f"  Range: ${range_low:.4f} - ${range_high:.4f}")
    print(f"  Size: {range_size*100:.2f}%")
    print(f"  Current: ${current:.4f}")
    print()
    
    # Check if ranging
    in_range = sum(1 for c in closes if range_low <= c <= range_high)
    range_pct = in_range / len(closes) * 100
    
    print(f"  Price stayed in range: {range_pct:.1f}% of time")
    print()
    
    if range_pct >= 95 and 2 <= range_size*100 <= 8:
        print("✅ SUITABLE FOR GRID TRADING")
        print(f"   Recommended grid: {int(range_size*100/0.5)} levels (0.5% spacing)")
        print(f"   Entry capital per level: ${30/10:.2f}")
    else:
        print("❌ NOT SUITABLE FOR GRID TRADING")
        if range_pct < 95:
            print(f"   Reason: Not ranging enough ({range_pct:.1f}% < 95%)")
        if range_size*100 < 2:
            print(f"   Reason: Range too tight ({range_size*100:.2f}% < 2%)")
        if range_size*100 > 8:
            print(f"   Reason: Range too wide ({range_size*100:.2f}% > 8%)")
        print()
        print("RECOMMENDATION: Wait for ranging market or use different strategy")

asyncio.run(check())

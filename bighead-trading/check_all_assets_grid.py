"""
Check all major assets for grid trading suitability
"""
import asyncio
import aiohttp

async def check_asset(symbol):
    async with aiohttp.ClientSession() as session:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=24"
        async with session.get(url) as resp:
            candles = await resp.json()
    
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    closes = [float(c[4]) for c in candles]
    
    range_high = max(highs)
    range_low = min(lows)
    range_size = (range_high - range_low) / range_low
    current = closes[-1]
    
    in_range = sum(1 for c in closes if range_low <= c <= range_high)
    range_pct = in_range / len(closes) * 100
    
    suitable = range_pct >= 95 and 0.02 <= range_size <= 0.08
    
    return {
        'symbol': symbol,
        'range_low': range_low,
        'range_high': range_high,
        'range_size': range_size * 100,
        'current': current,
        'range_pct': range_pct,
        'suitable': suitable
    }

async def main():
    assets = ['ETH', 'BTC', 'SOL', 'ARB', 'OP']
    
    print("="*70)
    print("GRID TRADING SUITABILITY CHECK - ALL ASSETS")
    print("="*70)
    print()
    
    results = []
    for asset in assets:
        try:
            result = await check_asset(asset)
            results.append(result)
        except:
            pass
    
    # Sort by suitability
    results.sort(key=lambda x: x['suitable'], reverse=True)
    
    for r in results:
        symbol = r['symbol']
        status = "✅ SUITABLE" if r['suitable'] else "❌ NOT SUITABLE"
        
        print(f"{symbol}:")
        print(f"  Range: ${r['range_low']:.4f} - ${r['range_high']:.4f}")
        print(f"  Size: {r['range_size']:.2f}%")
        print(f"  Current: ${r['current']:.4f}")
        print(f"  In-range: {r['range_pct']:.1f}%")
        print(f"  {status}")
        
        if not r['suitable']:
            if r['range_pct'] < 95:
                print(f"    (Not ranging: {r['range_pct']:.1f}% < 95%)")
            elif r['range_size'] < 2:
                print(f"    (Too tight: {r['range_size']:.2f}% < 2%)")
            elif r['range_size'] > 8:
                print(f"    (Too wide: {r['range_size']:.2f}% > 8%)")
        
        print()
    
    # Recommendation
    suitable_assets = [r for r in results if r['suitable']]
    
    print("="*70)
    if suitable_assets:
        print(f"✅ FOUND {len(suitable_assets)} SUITABLE ASSET(S) FOR GRID TRADING")
        print()
        for r in suitable_assets:
            print(f"  {r['symbol']}: {r['range_size']:.2f}% range")
    else:
        print("❌ NO ASSETS CURRENTLY SUITABLE FOR GRID TRADING")
        print()
        print("ALTERNATIVES:")
        print("  1. Wait 12-24h for market to settle into range")
        print("  2. Use mean reversion (works in trending markets)")
        print("  3. Use funding rate arbitrage (always works)")
        print("  4. Manual trading with tight SL")
    print("="*70)

asyncio.run(main())

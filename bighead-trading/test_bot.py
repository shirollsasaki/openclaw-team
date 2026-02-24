#!/usr/bin/env python3
"""Quick test to verify Strategy 1 setup"""

import asyncio
import sys

async def test():
    print("🧪 Testing Strategy 1 Setup...\n")
    
    # Test 1: Imports
    print("1️⃣  Testing imports...")
    try:
        import aiohttp
        import pandas as pd
        import numpy as np
        from dotenv import load_dotenv
        print("   ✅ All dependencies installed\n")
    except ImportError as e:
        print(f"   ❌ Missing dependency: {e}")
        print("   Run: pip3 install -r requirements.txt\n")
        return False
    
    # Test 2: Data fetching
    print("2️⃣  Testing data fetch (Binance API)...")
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {'symbol': 'ETHUSDT', 'interval': '15m', 'limit': 5}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ Fetched {len(data)} candles\n")
                else:
                    print(f"   ❌ API returned {resp.status}\n")
                    return False
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False
    
    # Test 3: Configuration
    print("3️⃣  Testing configuration...")
    load_dotenv()
    import os
    
    private_key = os.getenv('PRIVATE_KEY')
    if private_key:
        print(f"   ✅ Private key loaded ({private_key[:10]}...)\n")
    else:
        print("   ⚠️  No private key in .env (simulation mode only)\n")
    
    # Test 4: Bot module
    print("4️⃣  Testing bot module...")
    try:
        # Just import to check syntax
        import avantis_bot
        print("   ✅ Bot module loads correctly\n")
    except Exception as e:
        print(f"   ❌ Bot module error: {e}\n")
        return False
    
    print("="*60)
    print("✅ ALL TESTS PASSED - STRATEGY 1 READY")
    print("="*60)
    print("\n🚀 Ready to run: python3 avantis_bot.py")
    print("\n⚠️  Remember:")
    print("   - Strategy 1: Static 15x ARB/OP/ETH")
    print("   - Bot starts in SIMULATION mode (safe)")
    print("   - Run for 24h to test signals")
    print("   - Check logs: tail -f strategy1_bot.log")
    print("   - See SETUP.md for live trading")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test())
    sys.exit(0 if result else 1)

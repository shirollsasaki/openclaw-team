#!/usr/bin/env python3
"""
Fix Avantis SDK usage to match official AGENT.md patterns
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def get_correct_pair_indexes():
    """Get correct pair indexes from Avantis SDK"""
    from avantis_trader_sdk import TraderClient
    
    print("Connecting to Avantis SDK...")
    
    try:
        # Initialize TraderClient (required for pair lookups)
        provider_url = "https://mainnet.base.org"
        trader_client = TraderClient(provider_url)
        
        print("✅ Connected to Avantis SDK\n")
        
        # Get pair indexes for our assets
        pairs_to_check = ["ARB/USD", "OP/USD", "ETH/USD"]
        pair_indexes = {}
        
        for pair_name in pairs_to_check:
            try:
                pair_index = await trader_client.pairs_cache.get_pair_index(pair_name)
                pair_indexes[pair_name] = pair_index
                print(f"✅ {pair_name}: index {pair_index}")
            except Exception as e:
                print(f"❌ {pair_name}: {e}")
        
        print(f"\n{'='*60}")
        print("CORRECT PAIR_INDEX_MAP:")
        print("{'='*60}")
        print("PAIR_INDEX_MAP = {")
        
        if "ARB/USD" in pair_indexes:
            print(f"    'ARB': {pair_indexes['ARB/USD']},")
        if "OP/USD" in pair_indexes:
            print(f"    'OP': {pair_indexes['OP/USD']},")
        if "ETH/USD" in pair_indexes:
            print(f"    'ETH': {pair_indexes['ETH/USD']},")
        
        print("}")
        print("="*60)
        
        # Test price fetch
        print("\nTesting price fetch...")
        from avantis_trader_sdk import FeedClient
        
        feed_client = FeedClient()
        
        for pair_name, pair_index in pair_indexes.items():
            try:
                price_data = await feed_client.get_price_update_data(pair_index=pair_index)
                price = price_data.pro.price
                print(f"✅ {pair_name}: ${price:,.2f}")
            except Exception as e:
                print(f"❌ {pair_name} price fetch: {e}")
        
        return pair_indexes
        
    except Exception as e:
        print(f"❌ Failed to connect to Avantis: {e}")
        print("\nThis is likely because:")
        print("1. Avantis API is down")
        print("2. Network/firewall blocking connection")
        print("3. SDK version mismatch")
        print("\n💡 Recommendation: Use Binance prices until Avantis is reachable")
        return None

if __name__ == "__main__":
    asyncio.run(get_correct_pair_indexes())

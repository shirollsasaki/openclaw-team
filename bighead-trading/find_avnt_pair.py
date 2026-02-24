#!/usr/bin/env python3
"""Find AVNT pair index on Avantis"""

import asyncio
from avantis_trader_sdk import TraderClient
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    trader_client = TraderClient("https://mainnet.base.org")
    trader_client.set_local_signer(os.getenv('PRIVATE_KEY'))
    
    print("🔍 Searching for AVNT on Avantis...\n")
    
    pairs_info = await trader_client.pairs_cache.get_pairs_info()
    
    print("Available pairs:")
    for index, pair in pairs_info.items():
        pair_name = f"{pair.from_}/{pair.to}"
        print(f"   {index}: {pair_name}")
        
        if 'AVNT' in pair.from_.upper():
            print(f"   ✅ FOUND AVNT at pair_index: {index}")

asyncio.run(main())

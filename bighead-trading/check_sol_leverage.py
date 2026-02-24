"""
Check what leverage SOL actually supports on Avantis
"""
import asyncio
from avantis_sdk_wrapper import get_sdk

async def check_leverage():
    sdk = await get_sdk()
    trader_client = sdk.trader_client
    
    # Get pair info for SOL (pair_index 9)
    try:
        pair_info = await trader_client.pair.get_pair_info(9)
        print("SOL Pair Info:")
        print(pair_info)
        print()
        
        if 'maxLeverage' in pair_info:
            print(f"Max Leverage: {pair_info['maxLeverage']}")
        
        # Also check other pairs
        print("\nChecking all pairs:")
        for i in [0, 4, 7, 9]:  # ETH, ARB, OP, SOL
            try:
                info = await trader_client.pair.get_pair_info(i)
                name = info.get('name', f'Pair {i}')
                max_lev = info.get('maxLeverage', 'unknown')
                print(f"  {name}: max leverage = {max_lev}")
            except Exception as e:
                print(f"  Pair {i}: error - {e}")
        
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(check_leverage())

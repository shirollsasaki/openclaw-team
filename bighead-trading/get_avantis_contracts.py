#!/usr/bin/env python3
"""
Get Avantis contract addresses from the SDK
"""

import asyncio
from avantis_trader_sdk import TraderClient

async def get_contracts():
    print("Fetching Avantis contract addresses from SDK...")
    print("="*70)
    
    try:
        # Initialize TraderClient
        trader_client = TraderClient("https://mainnet.base.org")
        
        # Try to get contract addresses
        print("\n1. Checking TraderClient internals...")
        
        # The SDK should have contract addresses stored internally
        if hasattr(trader_client, 'trading'):
            print(f"   Trading module: {trader_client.trading}")
        
        if hasattr(trader_client, 'trade'):
            print(f"   Trade module: {trader_client.trade}")
            
            # Try to get contract from trade module
            if hasattr(trader_client.trade, 'contract_address'):
                print(f"   ✅ Contract address: {trader_client.trade.contract_address}")
            
            if hasattr(trader_client.trade, 'trading_contract'):
                print(f"   ✅ Trading contract: {trader_client.trade.trading_contract}")
        
        # Check for USDC contract
        print("\n2. Checking USDC contract...")
        if hasattr(trader_client, 'usdc_contract'):
            print(f"   ✅ USDC contract: {trader_client.usdc_contract}")
        
        # Try to inspect the module
        print("\n3. Inspecting SDK modules...")
        print(f"   TraderClient attributes: {[attr for attr in dir(trader_client) if not attr.startswith('_')]}")
        
        # Check if we can get it from a transaction
        print("\n4. Checking from SDK source...")
        try:
            import avantis_trader_sdk
            import inspect
            
            # Get SDK location
            sdk_file = inspect.getfile(avantis_trader_sdk)
            print(f"   SDK location: {sdk_file}")
            
            # Try to find contract addresses in SDK code
            import os
            sdk_dir = os.path.dirname(sdk_file)
            
            # Look for contract addresses in files
            for root, dirs, files in os.walk(sdk_dir):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r') as f:
                                content = f.read()
                                if '0x' in content and 'contract' in content.lower():
                                    # Look for Base contract addresses (start with 0x)
                                    import re
                                    addresses = re.findall(r'0x[a-fA-F0-9]{40}', content)
                                    if addresses:
                                        print(f"\n   Found addresses in {file}:")
                                        for addr in set(addresses):
                                            print(f"     {addr}")
                        except:
                            pass
        except Exception as e:
            print(f"   Error inspecting SDK: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(get_contracts())

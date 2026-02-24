#!/usr/bin/env python3
"""
Setup Avantis Integration
1. Get pair indexes for ARB, OP, ETH
2. Approve USDC for trading
3. Verify everything ready
"""

import asyncio
from avantis_trader_sdk import TraderClient
from dotenv import load_dotenv
import os

load_dotenv()

PRIVATE_KEY = os.getenv('PRIVATE_KEY')
WALLET = os.getenv('WALLET_ADDRESS')
BASE_RPC = "https://mainnet.base.org"

async def main():
    print("🔧 Setting up Avantis Integration\n")
    print("="*70)
    
    # Initialize client
    trader_client = TraderClient(BASE_RPC)
    trader_client.set_local_signer(PRIVATE_KEY)
    trader = trader_client.get_signer().get_ethereum_address()
    
    print(f"✅ Connected to Base")
    print(f"   Wallet: {trader}\n")
    
    # Step 1: Get pair indexes
    print("📊 Step 1: Getting pair indexes...")
    
    try:
        pairs_info = await trader_client.pairs_cache.get_pairs_info()
        
        pair_map = {}
        for index, pair in pairs_info.items():
            pair_name = f"{pair.from_}/{pair.to}"
            pair_map[pair_name] = index
            
            # Print relevant pairs
            if pair.from_ in ['BTC', 'ETH', 'ARB', 'OP', 'SOL', 'LINK']:
                print(f"   {pair_name}: {index}")
        
        # Get our assets
        eth_index = pair_map.get('ETH/USD')
        arb_index = pair_map.get('ARB/USD')
        op_index = pair_map.get('OP/USD')
        
        print(f"\n✅ Found pair indexes:")
        print(f"   ETH/USD: {eth_index}")
        print(f"   ARB/USD: {arb_index}")
        print(f"   OP/USD: {op_index}\n")
        
    except Exception as e:
        print(f"❌ Error getting pairs: {e}")
        return
    
    # Step 2: Check USDC balance
    print("💵 Step 2: Checking USDC balance...")
    
    try:
        usdc_balance = await trader_client.get_usdc_balance(trader)
        print(f"   Balance: {usdc_balance:.2f} USDC")
        
        if usdc_balance < 30:
            print(f"   ⚠️  Warning: Only {usdc_balance:.2f} USDC (need 30)")
        else:
            print(f"   ✅ Sufficient balance\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    # Step 3: Check/set USDC allowance
    print("🔐 Step 3: Checking USDC allowance...")
    
    try:
        allowance = await trader_client.get_usdc_allowance_for_trading(trader)
        print(f"   Current allowance: {allowance:.2f} USDC")
        
        if allowance < 30:
            print(f"   ⚠️  Need to approve USDC for trading")
            print(f"   Approving unlimited USDC...")
            
            # Approve unlimited (safe, standard practice)
            await trader_client.approve_usdc_for_trading(999999)
            
            print(f"   ⏳ Waiting for approval confirmation...")
            await asyncio.sleep(5)
            
            # Verify
            new_allowance = await trader_client.get_usdc_allowance_for_trading(trader)
            print(f"   ✅ New allowance: {new_allowance:.2f} USDC\n")
        else:
            print(f"   ✅ Already approved\n")
            
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    # Step 4: Get current trades
    print("📈 Step 4: Checking current positions...")
    
    try:
        trades, pending_orders = await trader_client.trade.get_trades(trader)
        
        print(f"   Open trades: {len(trades)}")
        print(f"   Pending orders: {len(pending_orders)}")
        
        if trades:
            for trade in trades:
                pair_name = await trader_client.pairs_cache.get_pair_name_from_index(trade.trade.pair_index)
                print(f"   - {pair_name}: {'LONG' if trade.trade.is_long else 'SHORT'} ${trade.trade.collateral_in_trade} @ {trade.trade.leverage}x")
        else:
            print(f"   ✅ No open positions\n")
            
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    # Summary
    print("="*70)
    print("✅ SETUP COMPLETE\n")
    
    print("📋 Configuration for bot:")
    print(f"""
ASSETS = {{
    'ARB': {{'capital': 10.0, 'pair_index': {arb_index}}},
    'OP': {{'capital': 10.0, 'pair_index': {op_index}}},
    'ETH': {{'capital': 10.0, 'pair_index': {eth_index}}}
}}
""")
    
    print("🚀 Ready to trade!")
    print("   Run: python3 avantis_bot_live.py")

if __name__ == "__main__":
    asyncio.run(main())

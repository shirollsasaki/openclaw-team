#!/usr/bin/env python3
"""
EMERGENCY CLOSE ALL POSITIONS
Use this to instantly close all open positions on Avantis
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def emergency_close_all():
    """Close all open positions on Avantis immediately"""
    
    print("="*70)
    print("🚨 EMERGENCY POSITION CLOSER")
    print("="*70)
    print()
    print("⚠️  THIS WILL CLOSE ALL OPEN POSITIONS ON AVANTIS")
    print("⚠️  YOU WILL REALIZE ANY UNREALIZED P&L (GAINS OR LOSSES)")
    print()
    
    # Get confirmation
    confirm = input("Type 'CLOSE ALL' to proceed: ")
    if confirm.strip() != 'CLOSE ALL':
        print("❌ Cancelled")
        return
    
    print()
    print("🔴 Closing all positions...")
    print()
    
    try:
        from avantis_trader_sdk import TraderClient
        
        # Initialize client
        provider_url = "https://mainnet.base.org"
        trader_client = TraderClient(provider_url)
        
        # Set signer
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            print("❌ PRIVATE_KEY not found in .env")
            return
        
        trader_client.set_local_signer(private_key)
        trader = trader_client.get_signer().get_ethereum_address()
        
        print(f"✅ Wallet: {trader}")
        print()
        
        # Get all open trades
        print("📊 Fetching open positions from Avantis...")
        trades, pending_orders = await trader_client.trade.get_trades(trader)
        
        if not trades and not pending_orders:
            print("✅ No open positions found!")
            return
        
        print(f"Found: {len(trades)} open positions, {len(pending_orders)} pending orders")
        print()
        
        # Close all open trades
        closed_count = 0
        for trade in trades:
            try:
                pair_name = await trader_client.pairs_cache.get_pair_name_from_index(
                    trade.trade.pair_index
                )
                
                print(f"🔴 Closing: {pair_name} (index {trade.trade.trade_index})")
                print(f"   Type: {'LONG' if trade.trade.is_long else 'SHORT'}")
                print(f"   Size: ${trade.trade.collateral_in_trade:.2f}")
                print(f"   Entry: ${trade.trade.open_price:.4f}")
                
                # Build close transaction
                close_tx = await trader_client.trade.build_trade_close_tx(
                    pair_index=trade.trade.pair_index,
                    trade_index=trade.trade.trade_index,
                    collateral_to_close=trade.trade.collateral_in_trade,  # Close full position
                    trader=trader,
                )
                
                # Execute
                receipt = await trader_client.sign_and_get_receipt(close_tx)
                
                print(f"   ✅ CLOSED: TX {receipt.transactionHash.hex()[:10]}...")
                print()
                
                closed_count += 1
                
            except Exception as e:
                print(f"   ❌ Failed to close: {e}")
                print()
        
        # Cancel all pending orders
        cancelled_count = 0
        for order in pending_orders:
            try:
                pair_name = await trader_client.pairs_cache.get_pair_name_from_index(
                    order.pair_index
                )
                
                print(f"🔴 Cancelling: {pair_name} limit order")
                
                cancel_tx = await trader_client.trade.build_order_cancel_tx(
                    pair_index=order.pair_index,
                    trade_index=order.trade_index,
                    trader=trader,
                )
                
                receipt = await trader_client.sign_and_get_receipt(cancel_tx)
                
                print(f"   ✅ CANCELLED: TX {receipt.transactionHash.hex()[:10]}...")
                print()
                
                cancelled_count += 1
                
            except Exception as e:
                print(f"   ❌ Failed to cancel: {e}")
                print()
        
        print("="*70)
        print("SUMMARY")
        print("="*70)
        print(f"✅ Positions closed: {closed_count}/{len(trades)}")
        print(f"✅ Orders cancelled: {cancelled_count}/{len(pending_orders)}")
        print()
        
        if closed_count == len(trades) and cancelled_count == len(pending_orders):
            print("✅ ALL POSITIONS CLOSED SUCCESSFULLY!")
        else:
            print("⚠️  Some positions may still be open. Check Avantis manually.")
        
        print()
        print("🛑 Remember to stop the bot:")
        print("   kill 14703")
        print()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("⚠️  If this failed, close positions manually on avantisfi.com")

if __name__ == "__main__":
    asyncio.run(emergency_close_all())

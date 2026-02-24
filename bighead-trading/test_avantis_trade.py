#!/usr/bin/env python3
"""Test Avantis trade opening"""

import asyncio
from avantis_trader_sdk import TraderClient
from avantis_trader_sdk.types import TradeInput, TradeInputOrderType
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    # Setup
    trader_client = TraderClient("https://mainnet.base.org")
    trader_client.set_local_signer(os.getenv('PRIVATE_KEY'))
    trader = trader_client.get_signer().get_ethereum_address()
    
    print(f"Trader: {trader}")
    
    # Get current ETH price for realistic TP/SL
    from avantis_trader_sdk import FeedClient
    feed_client = FeedClient()
    price_data = await feed_client.get_price_update_data(pair_index=0)  # ETH
    current_price = price_data.pro.price
    print(f"Current ETH price: ${current_price:.2f}")
    
    # Create trade input
    trade_input = TradeInput(
        trader=trader,
        pair_index=0,  # ETH/USD
        index=0,
        collateral_in_trade=1.0,  # $1 USDC test
        is_long=True,
        leverage=5,  # Lower leverage for test
        tp=current_price * 1.1,  # 10% profit target
        sl=current_price * 0.95,  # 5% stop loss
        open_price=None,
    )
    
    print(f"\nTrade Input:")
    print(f"  Pair: ETH/USD (0)")
    print(f"  Collateral: $1.00")
    print(f"  Leverage: 5x")
    print(f"  TP: ${trade_input.tp:.2f}")
    print(f"  SL: ${trade_input.sl:.2f}")
    print(f"  Long: {trade_input.is_long}")
    
    try:
        print(f"\nBuilding transaction...")
        tx = await trader_client.trade.build_trade_open_tx(
            trade_input=trade_input,
            trade_input_order_type=TradeInputOrderType.MARKET,
            slippage_percentage=1.0,
        )
        
        print(f"✅ Transaction built successfully!")
        print(f"   To: {tx['to']}")
        print(f"   Data length: {len(tx['data'])} bytes")
        
        # Don't actually send for this test
        print(f"\n⚠️  Test successful - transaction NOT sent (test mode)")
        
    except Exception as e:
        print(f"\n❌ Error building transaction:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

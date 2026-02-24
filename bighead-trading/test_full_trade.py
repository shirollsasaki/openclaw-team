#!/usr/bin/env python3
"""Test full Avantis trade flow"""

import asyncio
from avantis_trader_sdk import TraderClient, FeedClient
from avantis_trader_sdk.types import TradeInput, TradeInputOrderType
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    # Setup
    trader_client = TraderClient("https://mainnet.base.org")
    trader_client.set_local_signer(os.getenv('PRIVATE_KEY'))
    trader = trader_client.get_signer().get_ethereum_address()
    
    print(f"Trader: {trader}\n")
    
    # Get ETH price
    feed_client = FeedClient()
    price_data = await feed_client.get_price_update_data(pair_index=0)
    current_price = price_data.pro.price / 1e10  # Convert from 10 decimals
    print(f"Current ETH price: ${current_price:.2f}\n")
    
    # Create trade input
    trade_input = TradeInput(
        trader=trader,
        pair_index=0,  # ETH/USD
        collateral_in_trade=1.0,  # $1 test
        is_long=True,
        leverage=5,
        tp=current_price * 1.05,  # 5% up
        sl=current_price * 0.98,  # 2% down
    )
    
    print(f"Trade Parameters:")
    print(f"  Collateral: $1.00")
    print(f"  Leverage: 5x")
    print(f"  Direction: LONG")
    print(f"  TP: ${current_price * 1.05:.2f}")
    print(f"  SL: ${current_price * 0.98:.2f}\n")
    
    try:
        print("Building transaction...")
        tx = await trader_client.trade.build_trade_open_tx(
            trade_input=trade_input,
            trade_input_order_type=TradeInputOrderType.MARKET,
            slippage_percentage=1.0,
        )
        
        print("✅ Transaction built successfully!")
        print(f"   To: {tx.get('to', 'N/A')}")
        print(f"   Value: {tx.get('value', 0)}")
        print(f"   Gas estimate: {tx.get('gas', 'N/A')}")
        
        # Estimate cost
        if 'gasPrice' in tx and 'gas' in tx:
            gas_cost_eth = (tx['gasPrice'] * tx['gas']) / 1e18
            print(f"   Gas cost: ~${gas_cost_eth * 3000:.2f} (at $3000/ETH)")
        
        print(f"\n⚠️  Test mode - NOT sending transaction")
        print(f"   To send, uncomment: await trader_client.sign_and_get_receipt(tx)")
        
    except Exception as e:
        print(f"❌ Error:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

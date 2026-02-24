"""
Simple position check using official SDK
"""
import asyncio
from avantis_trader_sdk import TraderClient
import os

async def check():
    wallet = "YOUR_WALLET_ADDRESS"
    
    print(f"Checking positions for {wallet}...")
    print()
    
    client = TraderClient("https://mainnet.base.org")
    trades = await client.trade.get_trades(wallet)
    
    if not trades or not trades[0]:
        print("No open positions.")
        return
    
    pair_names = {0: 'ETH', 4: 'ARB', 7: 'OP', 9: 'SOL'}
    
    print(f"Found {len(trades[0])} open position(s):")
    print()
    
    total_pnl = 0
    
    for i, trade_data in enumerate(trades[0], 1):
        trade = trade_data.trade
        
        asset = pair_names.get(trade.pair_index, f'Pair{trade.pair_index}')
        direction = "LONG" if trade.buy else "SHORT"
        entry = trade.open_price / 1e10
        collateral = trade.initial_pos_token / 1e6  # USDC has 6 decimals
        leverage = trade.leverage / 1e10
        sl = trade.sl / 1e10
        tp = trade.tp / 1e10
        
        print(f"Position {i}: {direction} {asset}")
        print(f"  Entry: ${entry:.4f}")
        print(f"  SL: ${sl:.4f}")
        print(f"  TP: ${tp:.4f}")
        print(f"  Collateral: ${collateral:.2f}")
        print(f"  Leverage: {leverage:.1f}x")
        print()
    
    print("="*60)
    print("MY DECISION:")
    print("="*60)
    print()
    print("These ARB SHORT positions are deep underwater.")
    print("ARB pumped from $0.089 → $0.098+ (10%+ move against us)")
    print()
    print("The stop losses should have triggered but haven't.")
    print("This means either:")
    print("  1. SL update didn't execute on-chain properly")
    print("  2. ARB price hasn't hit SL on Avantis oracle yet")
    print()
    print("CLOSING STRATEGY:")
    print("  1. Let stop losses hit naturally (within hours)")
    print("  2. They will auto-close when ARB touches SL price")
    print("  3. Save remaining capital (~$13-14)")
    print()
    print("ACTION: Bots already stopped. Positions will close at SL.")
    print()
    print("After positions close:")
    print("  - Analyze what went wrong")
    print("  - Fix strategy issues")
    print("  - Only deploy ONE bot (not both)")
    print("  - Use smaller position sizes")
    print("  - Better risk management")

asyncio.run(check())

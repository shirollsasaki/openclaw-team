"""
Check current positions and close them if needed
"""
import asyncio
from avantis_sdk_wrapper import get_sdk
import os
from dotenv import load_dotenv

load_dotenv()

async def check_and_close():
    print("Checking positions on Avantis...")
    
    sdk = await get_sdk()
    trader_client = sdk.trader_client
    feed_client = sdk.feed_client
    
    wallet = os.getenv('WALLET_ADDRESS', 'YOUR_WALLET_ADDRESS')
    
    # Get open positions
    try:
        trades = await trader_client.get_trades(wallet)
        
        if not trades:
            print("No open positions found.")
            return
        
        print(f"\nFound {len(trades)} open position(s):")
        print()
        
        for i, trade in enumerate(trades, 1):
            pair_index = trade.get('pairIndex')
            direction = "LONG" if trade.get('buy') else "SHORT"
            entry = float(trade.get('openPrice', 0)) / 1e10
            collateral = float(trade.get('initialPosToken', 0)) / 1e18
            leverage = float(trade.get('leverage', 0)) / 1e10
            
            # Get current price
            price_data = feed_client.get_price(pair_index)
            current_price = float(price_data.get('price', 0)) / 1e10 if price_data else 0
            
            # Calculate P&L
            if direction == "LONG":
                pnl_pct = ((current_price - entry) / entry) * leverage if entry > 0 else 0
            else:
                pnl_pct = ((entry - current_price) / entry) * leverage if entry > 0 else 0
            
            pnl_usd = collateral * pnl_pct
            
            asset_names = {0: 'ETH', 4: 'ARB', 7: 'OP', 9: 'SOL'}
            asset = asset_names.get(pair_index, f'Pair{pair_index}')
            
            print(f"Position {i}:")
            print(f"  Asset: {asset}")
            print(f"  Direction: {direction}")
            print(f"  Entry: ${entry:.4f}")
            print(f"  Current: ${current_price:.4f}")
            print(f"  Collateral: ${collateral:.2f}")
            print(f"  Leverage: {leverage}x")
            print(f"  P&L: ${pnl_usd:+.2f} ({pnl_pct*100:+.1f}%)")
            
            # Check if should close
            if pnl_pct < -0.50:  # More than -50% loss
                print(f"  ⚠️  CRITICAL LOSS - Should close immediately!")
            elif pnl_pct < -0.30:  # More than -30% loss
                print(f"  ⚠️  Heavy loss - Recommend closing")
            
            print()
        
        # Decision
        print("="*60)
        print("RECOMMENDATION:")
        print("="*60)
        
        total_pnl = sum([
            (collateral * (
                ((float(feed_client.get_price(t.get('pairIndex')).get('price', 0)) / 1e10 - float(t.get('openPrice', 0)) / 1e10) / (float(t.get('openPrice', 0)) / 1e10)) * (float(t.get('leverage', 0)) / 1e10)
                if t.get('buy') else
                ((float(t.get('openPrice', 0)) / 1e10 - float(feed_client.get_price(t.get('pairIndex')).get('price', 0)) / 1e10) / (float(t.get('openPrice', 0)) / 1e10)) * (float(t.get('leverage', 0)) / 1e10)
            ))
            for t in trades
            for collateral in [float(t.get('initialPosToken', 0)) / 1e18]
        ])
        
        if total_pnl < -10:
            print(f"Total unrealized loss: ${total_pnl:.2f}")
            print()
            print("DECISION: Close all positions immediately")
            print("Reason: Heavy losses, prevent further damage")
            print()
            print("To close manually:")
            print("  1. Go to https://avantisfi.com")
            print("  2. Connect wallet")
            print("  3. Close each position")
            print()
            print("OR let them hit stop loss naturally")
        else:
            print("Positions are manageable, can let them ride")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(check_and_close())

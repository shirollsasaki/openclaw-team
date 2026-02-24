"""
Check current wallet balance and P&L summary
"""
import asyncio
from web3 import AsyncWeb3
from avantis_trader_sdk import TraderClient
import os

async def check_status():
    wallet = "YOUR_WALLET_ADDRESS"
    
    print("="*60)
    print("WALLET & P&L SUMMARY")
    print("="*60)
    print()
    
    # Check wallet balance
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider("https://mainnet.base.org"))
    
    # USDC balance (6 decimals)
    usdc_address = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    usdc_abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
    usdc = w3.eth.contract(address=usdc_address, abi=usdc_abi)
    usdc_balance = await usdc.functions.balanceOf(wallet).call()
    usdc_amount = usdc_balance / 1e6
    
    print(f"💰 USDC Balance: ${usdc_amount:.2f}")
    print()
    
    # Check positions
    client = TraderClient("https://mainnet.base.org")
    trades = await client.trade.get_trades(wallet)
    
    if not trades or not trades[0]:
        print("📊 Open Positions: 0")
        print()
        print(f"✅ Total Capital Available: ${usdc_amount:.2f}")
        print()
        print("="*60)
        return
    
    # Calculate P&L for open positions
    pair_names = {0: 'ETH', 4: 'ARB', 7: 'OP', 9: 'SOL'}
    
    print(f"📊 Open Positions: {len(trades[0])}")
    print()
    
    total_collateral = 0
    total_pnl = 0
    
    for i, trade_data in enumerate(trades[0], 1):
        trade = trade_data.trade
        
        asset = pair_names.get(trade.pair_index, f'Pair{trade.pair_index}')
        direction = "LONG" if trade.buy else "SHORT"
        entry = trade.open_price / 1e10
        collateral = trade.initial_pos_token / 1e6
        leverage = trade.leverage / 1e10
        sl = trade.sl / 1e10
        tp = trade.tp / 1e10
        
        # Get current price from Pyth (via trade data if available)
        # For now, we'll show entry data
        
        total_collateral += collateral
        
        print(f"  Position {i}: {direction} {asset}")
        print(f"    Entry: ${entry:.4f}")
        print(f"    SL: ${sl:.4f} | TP: ${tp:.4f}")
        print(f"    Collateral: ${collateral:.2f} @ {leverage:.1f}x")
        print()
    
    print(f"💼 Total in Positions: ${total_collateral:.2f}")
    print(f"💰 Free Capital: ${usdc_amount:.2f}")
    print(f"📈 Total Capital: ${usdc_amount + total_collateral:.2f}")
    print()
    print("="*60)
    print()
    
    # Historical summary
    print("📊 HISTORICAL P&L (from start):")
    print()
    print("  Starting capital: $60.00")
    print(f"  Current total: ${usdc_amount + total_collateral:.2f}")
    print(f"  Realized P&L: ${(usdc_amount + total_collateral) - 60:.2f}")
    print(f"  Return: {((usdc_amount + total_collateral) / 60 - 1) * 100:+.1f}%")
    print()
    print("="*60)

asyncio.run(check_status())

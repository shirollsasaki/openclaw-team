"""
Check if bot is in sync with Avantis
"""
import asyncio
from avantis_trader_sdk import TraderClient

async def check():
    client = TraderClient("https://mainnet.base.org")
    wallet = 'YOUR_WALLET_ADDRESS'
    
    trades = await client.trade.get_trades(wallet)
    
    print("="*70)
    print("AVANTIS REALITY CHECK")
    print("="*70)
    print()
    
    if trades and trades[0]:
        print(f"✅ Avantis shows: {len(trades[0])} open positions")
        print()
        for i, trade_data in enumerate(trades[0], 1):
            trade = trade_data.trade
            print(f"Position {i}:")
            print(f"  Trade Index: {trade.trade_index}")
            print(f"  Entry: ${trade.open_price:.6f}")
            print(f"  SL: ${trade.sl:.6f}")
            print(f"  TP: ${trade.tp:.6f}")
            print()
    else:
        print("❌ No positions on Avantis")
    
    print()
    print("Bot thinks it has 1 position (from logs)")
    print()
    if len(trades[0]) != 1:
        print("⚠️  BOT OUT OF SYNC!")
        print(f"  Avantis: {len(trades[0])} positions")
        print(f"  Bot: 1 position")
        print()
        print("Solution: Restart bot to force reload from Avantis")

asyncio.run(check())

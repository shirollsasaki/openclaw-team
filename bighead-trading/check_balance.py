#!/usr/bin/env python3
"""Check wallet balance on Base network"""

import asyncio
import aiohttp
import json

WALLET = "YOUR_WALLET_ADDRESS"
BASE_RPC = "https://mainnet.base.org"

async def check_balance():
    print(f"🔍 Checking balance for: {WALLET}\n")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Check ETH balance
            eth_payload = {
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [WALLET, "latest"],
                "id": 1
            }
            
            async with session.post(BASE_RPC, json=eth_payload) as resp:
                result = await resp.json()
                eth_wei = int(result['result'], 16)
                eth_balance = eth_wei / 1e18
                
                print(f"💎 ETH Balance: {eth_balance:.4f} ETH (${eth_balance*3000:.2f} @ $3000/ETH)")
                
                if eth_balance < 0.001:
                    print("   ⚠️  Low ETH! Need at least 0.001 for gas")
                else:
                    print("   ✅ ETH sufficient for gas fees")
        
        print("\n📊 Full details:")
        print(f"   https://basescan.org/address/{WALLET}")
        
        print("\n💡 To check USDC balance:")
        print(f"   Visit BaseScan link above and look for USDC token")
        
    except Exception as e:
        print(f"❌ Error checking balance: {e}")
        print(f"\n📊 Check manually:")
        print(f"   https://basescan.org/address/{WALLET}")

if __name__ == "__main__":
    asyncio.run(check_balance())

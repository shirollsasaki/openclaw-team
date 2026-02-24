#!/usr/bin/env python3
"""Check USDC balance on Base"""

from web3 import Web3

WALLET = "YOUR_WALLET_ADDRESS"
BASE_RPC = "https://mainnet.base.org"
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # USDC on Base

USDC_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

w3 = Web3(Web3.HTTPProvider(BASE_RPC))
usdc = w3.eth.contract(address=USDC_ADDRESS, abi=USDC_ABI)

balance_wei = usdc.functions.balanceOf(WALLET).call()
balance = balance_wei / 1e6  # USDC has 6 decimals

print(f"💵 USDC Balance: {balance:.2f} USDC")

if balance >= 30:
    print("   ✅ Sufficient for trading ($30 required)")
elif balance > 0:
    print(f"   ⚠️  Only ${balance:.2f} available (need $30)")
else:
    print("   ❌ No USDC found. Check transaction status.")

print(f"\n📊 Verify: https://basescan.org/address/{WALLET}")

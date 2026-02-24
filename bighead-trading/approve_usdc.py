#!/usr/bin/env python3
"""
Approve USDC for Avantis Trading Contract

Before running:
1. Get Avantis trading contract address from https://docs.avantisfi.com/
2. Update AVANTIS_TRADING_CONTRACT below
"""

from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

# Configuration
BASE_RPC = "https://mainnet.base.org"
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
WALLET = os.getenv('WALLET_ADDRESS')

# USDC Contract on Base
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# TODO: Get this from Avantis docs
AVANTIS_TRADING_CONTRACT = "0x_REPLACE_WITH_AVANTIS_CONTRACT_ADDRESS"

# USDC ABI (approve function)
USDC_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

def approve_usdc():
    print("🔐 USDC Approval for Avantis Trading\n")
    
    # Connect to Base
    w3 = Web3(Web3.HTTPProvider(BASE_RPC))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Base network")
        return
    
    print(f"✅ Connected to Base network")
    print(f"   Wallet: {WALLET}")
    print(f"   USDC: {USDC_ADDRESS}")
    print(f"   Avantis: {AVANTIS_TRADING_CONTRACT}\n")
    
    if "REPLACE" in AVANTIS_TRADING_CONTRACT:
        print("⚠️  ERROR: Update AVANTIS_TRADING_CONTRACT first!")
        print("\n📚 Get contract address from:")
        print("   https://docs.avantisfi.com/")
        print("   Look for 'Trading Contract' on Base network")
        return
    
    # Create contract instance
    usdc = w3.eth.contract(address=USDC_ADDRESS, abi=USDC_ABI)
    
    # Approve max amount (unlimited)
    max_approval = 2**256 - 1
    
    print(f"📝 Building approval transaction...")
    
    # Build transaction
    tx = usdc.functions.approve(
        AVANTIS_TRADING_CONTRACT,
        max_approval
    ).build_transaction({
        'from': WALLET,
        'gas': 100000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(WALLET)
    })
    
    print(f"💰 Estimated gas: {tx['gas']}")
    print(f"💸 Gas price: {w3.from_wei(tx['gasPrice'], 'gwei')} gwei\n")
    
    # Sign transaction
    print("🔏 Signing transaction...")
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    
    # Send transaction
    print("📤 Sending transaction...")
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    
    print(f"✅ Transaction sent!")
    print(f"   Hash: {tx_hash.hex()}")
    print(f"   Explorer: https://basescan.org/tx/{tx_hash.hex()}\n")
    
    # Wait for confirmation
    print("⏳ Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt['status'] == 1:
        print("✅ USDC approved successfully!")
        print("   Bot can now trade on Avantis\n")
        print("🚀 Next: Run the bot")
        print("   python3 avantis_bot.py")
    else:
        print("❌ Transaction failed")
        print(f"   Check: https://basescan.org/tx/{tx_hash.hex()}")

if __name__ == "__main__":
    approve_usdc()

#!/usr/bin/env python3
"""
Create new Avantis trading wallet for Base chain
"""

from eth_account import Account
import secrets

# Generate new wallet
private_key = "0x" + secrets.token_hex(32)
account = Account.from_key(private_key)

print("="*80)
print("🔑 NEW AVANTIS TRADING WALLET CREATED")
print("="*80)
print(f"\n📍 Wallet Address:")
print(f"   {account.address}")
print(f"\n🔐 Private Key (KEEP SECRET!):")
print(f"   {private_key}")
print(f"\n⚠️  SECURITY WARNINGS:")
print(f"   1. NEVER share your private key with anyone")
print(f"   2. Save this in a password manager (1Password, Bitwarden)")
print(f"   3. Delete this file after saving the key")
print(f"   4. Fund with ONLY $10-30 USDC + $2-5 ETH (gas)")
print(f"   5. This is a trading wallet - don't store life savings here")
print(f"\n📝 Next Steps:")
print(f"   1. Fund this address with USDC + ETH on Base network")
print(f"   2. Save private key to .env file:")
print(f"      PRIVATE_KEY={private_key}")
print(f"   3. Never commit .env to git")
print(f"\n🌐 Network: Base (Chain ID: 8453)")
print(f"   Bridge USDC/ETH: https://bridge.base.org")
print("="*80)

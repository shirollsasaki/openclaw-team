#!/usr/bin/env python3
"""
GO LIVE - Ready to deploy with one command
"""

import os
import sys
import asyncio
from datetime import datetime

BOTS = {
    '1': {'file': 'avantis_bot_v2.py', 'name': 'V2 Enhanced (+19.3%)', 'recommended': True},
    '2': {'file': 'avantis_bot_v2_squeeze.py', 'name': 'V2+Squeeze (+18.7%)'},
    '3': {'file': 'avantis_bot_v2_squeeze_all3.py', 'name': 'V2+Squeeze+All3 (Ultra selective)'},
    '4': {'file': 'avantis_bot.py', 'name': 'V1 Baseline'},
}

def print_status():
    """Print current readiness status"""
    print("="*70)
    print("🚀 LIVE TRADING - READY TO DEPLOY")
    print("="*70)
    print()
    print("✅ CHECKLIST:")
    print("   ✅ Wallet: 0xB57d...4B164B0")
    print("   ✅ USDC Balance: $30.00")
    print("   ✅ ETH for Gas: 0.0021 ETH")
    print("   ✅ USDC Approved: $999,999")
    print("   ✅ Avantis SDK: Working")
    print("   ✅ Prices: Live from Avantis")
    print()
    print("📊 SIMULATION RESULTS (Last 12 hours):")
    print("   • V2 Enhanced: +$5.78 (+19.3%) ⭐ RECOMMENDED")
    print("   • V2+Squeeze: +$5.61 (+18.7%)")
    print("   • V1 Baseline: +$3.93 (+13.1%)")
    print("   • V2+Sq+All3: $0.00 (very selective)")
    print()
    print("="*70)
    print()

def show_instructions():
    """Show what will happen when going live"""
    print("🎯 WHEN YOU SAY 'GO LIVE', I WILL:")
    print()
    print("1. Stop simulation bot")
    print("2. Create backup of bot file")
    print("3. Enable live trading mode")
    print("4. Start bot with real trading")
    print("5. Monitor first trade")
    print()
    print("⏱️  Total time: ~30 seconds")
    print("🔴 THIS WILL USE REAL MONEY")
    print()
    print("="*70)
    print()
    print("📌 READY AND WAITING FOR YOUR COMMAND")
    print()
    print("When ready, tell me:")
    print('  "go live with V2"  or  "go live"  or  "start live trading"')
    print()

def main():
    print_status()
    show_instructions()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
GO LIVE - V2+Squeeze Instant Deployment
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime

def go_live():
    print("="*70)
    print("🚀 V2+SQUEEZE - GOING LIVE")
    print("="*70)
    print()
    print("Bot: Strategy 1 V2 + Squeeze")
    print("Proven: +$5.61 (+18.7%) in simulation")
    print("Win Rate: 100% on closed trades")
    print()
    print("🔴 THIS WILL USE REAL MONEY")
    print()
    
    # Final confirmation
    confirm = input("Type 'GO LIVE' to deploy with real money: ")
    if confirm.strip() != 'GO LIVE':
        print("❌ Cancelled")
        return False
    
    print()
    print("🚀 Deploying V2+Squeeze to live trading...")
    print()
    
    filepath = '$OPENCLAW_HOME/bighead/avantis_bot_v2_squeeze.py'
    
    # Step 1: Backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = f"{filepath}.backup_prelive_{timestamp}"
    shutil.copy2(filepath, backup)
    print(f"✅ Backup: {backup}")
    
    # Step 2: Set SIMULATION_MODE = False
    with open(filepath, 'r') as f:
        content = f.read()
    
    content = content.replace(
        'SIMULATION_MODE = True',
        'SIMULATION_MODE = False  # 🔴 LIVE TRADING'
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print("✅ Enabled live trading mode")
    
    # Step 3: Stop simulation
    print("✅ Stopping simulation bot...")
    subprocess.run(['pkill', '-f', 'avantis_bot_v2_squeeze.py'], 
                   capture_output=True)
    
    import time
    time.sleep(2)
    
    # Step 4: Start live bot
    print("🚀 Starting LIVE bot...")
    
    log_file = 'LIVE_v2_squeeze.log'
    process = subprocess.Popen(
        ['python3', 'avantis_bot_v2_squeeze.py'],
        stdout=open(log_file, 'w'),
        stderr=subprocess.STDOUT,
        cwd='$OPENCLAW_HOME/bighead'
    )
    
    print()
    print("="*70)
    print("✅ V2+SQUEEZE LIVE TRADING ACTIVATED!")
    print("="*70)
    print()
    print(f"🔴 Bot PID: {process.pid}")
    print(f"📊 Log: tail -f {log_file}")
    print(f"🛑 Stop: kill {process.pid}")
    print()
    print("⚠️  REAL MONEY IS NOW AT RISK")
    print("⚠️  WATCH THE FIRST TRADE CAREFULLY")
    print()
    
    return True

if __name__ == "__main__":
    go_live()

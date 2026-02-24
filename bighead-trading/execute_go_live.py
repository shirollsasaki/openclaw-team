#!/usr/bin/env python3
"""
EXECUTE GO LIVE - Actually flips to live trading
RUN ONLY WHEN USER CONFIRMS
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
import re

def backup_file(filepath):
    """Create backup of bot file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{filepath}.backup_{timestamp}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def enable_live_trading(filepath):
    """
    Enable live trading in bot file
    This is the critical step that flips from simulation to real trading
    """
    print(f"🔧 Enabling live trading in {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Method 1: Look for SIMULATION_MODE flag
    if 'SIMULATION_MODE' in content:
        # Replace SIMULATION_MODE = True with False
        new_content = re.sub(
            r'SIMULATION_MODE\s*=\s*True',
            'SIMULATION_MODE = False',
            content
        )
        
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            print("✅ Set SIMULATION_MODE = False")
            return True
    
    # Method 2: Look for simulation check in code
    if '⚠️  SIMULATION MODE' in content or 'simulation mode' in content.lower():
        # Add a LIVE_TRADING flag at the top of Config
        if 'class Config:' in content:
            new_content = content.replace(
                'class Config:',
                'class Config:\n    LIVE_TRADING = True  # 🔴 REAL MONEY MODE'
            )
            
            with open(filepath, 'w') as f:
                f.write(new_content)
            print("✅ Added LIVE_TRADING = True")
            return True
    
    print("⚠️  Could not automatically enable live trading")
    print("⚠️  Manual verification needed")
    return False

def stop_simulation_bot(bot_filename):
    """Stop running simulation instance"""
    print(f"🛑 Stopping simulation bot ({bot_filename})...")
    try:
        result = subprocess.run(
            ['pkill', '-f', bot_filename],
            capture_output=True,
            text=True
        )
        print("✅ Simulation bot stopped")
        return True
    except Exception as e:
        print(f"⚠️  Could not stop bot: {e}")
        return False

def start_live_bot(bot_filename):
    """Start bot in live trading mode"""
    print(f"🚀 Starting LIVE bot ({bot_filename})...")
    
    log_filename = f"LIVE_{bot_filename.replace('.py', '.log')}"
    
    try:
        # Start bot in background
        process = subprocess.Popen(
            ['python3', bot_filename],
            stdout=open(log_filename, 'w'),
            stderr=subprocess.STDOUT,
            cwd='$OPENCLAW_HOME/bighead'
        )
        
        print(f"✅ Live bot started (PID: {process.pid})")
        print(f"📊 Log file: {log_filename}")
        print(f"📊 Monitor: tail -f {log_filename}")
        print(f"🛑 Stop: kill {process.pid}")
        
        return process.pid
    
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        return None

def go_live(bot_choice='2'):
    """
    Main go-live function
    bot_choice: '1'=V2 Enhanced, '2'=V2+Squeeze, '3'=V2+Sq+All3, '4'=V1
    """
    
    bots = {
        '1': 'avantis_bot_v2.py',
        '2': 'avantis_bot_v2_squeeze.py',
        '3': 'avantis_bot_v2_squeeze_all3.py',
        '4': 'avantis_bot.py'
    }
    
    bot_names = {
        '1': 'V2 Enhanced (+19.3%)',
        '2': 'V2+Squeeze (+18.7%)',
        '3': 'V2+Squeeze+All3',
        '4': 'V1 Baseline'
    }
    
    if bot_choice not in bots:
        print(f"❌ Invalid bot choice: {bot_choice}")
        return False
    
    bot_file = bots[bot_choice]
    bot_name = bot_names[bot_choice]
    filepath = f'$OPENCLAW_HOME/bighead/{bot_file}'
    
    print("="*70)
    print("🔴 GOING LIVE WITH REAL MONEY")
    print("="*70)
    print()
    print(f"Bot: {bot_name}")
    print(f"File: {bot_file}")
    print()
    print("THIS WILL:")
    print("  1. Stop simulation")
    print("  2. Enable live trading")
    print("  3. Start real trading with $30 USDC")
    print()
    
    # Final confirmation
    confirm = input("Type 'GO LIVE' to confirm: ")
    if confirm.strip() != 'GO LIVE':
        print("❌ Cancelled")
        return False
    
    print()
    print("🚀 Deploying to live trading...")
    print()
    
    # Step 1: Backup
    backup_path = backup_file(filepath)
    
    # Step 2: Enable live trading
    success = enable_live_trading(filepath)
    if not success:
        print()
        print("⚠️  MANUAL STEP REQUIRED:")
        print(f"   1. Open {bot_file}")
        print("   2. Find: SIMULATION_MODE = True")
        print("   3. Change to: SIMULATION_MODE = False")
        print("   4. Save file")
        print()
        input("Press ENTER when done...")
    
    # Step 3: Stop simulation
    stop_simulation_bot(bot_file)
    
    import time
    time.sleep(2)
    
    # Step 4: Start live
    pid = start_live_bot(bot_file)
    
    if pid:
        print()
        print("="*70)
        print("✅ LIVE TRADING ACTIVATED!")
        print("="*70)
        print()
        print(f"🔴 Bot: {bot_name}")
        print(f"🔴 PID: {pid}")
        print(f"🔴 THIS IS REAL MONEY NOW")
        print()
        print(f"📊 Monitor: tail -f LIVE_{bot_file.replace('.py', '.log')}")
        print(f"🛑 Emergency stop: kill {pid}")
        print()
        print("⚠️  WATCH THE FIRST TRADE CAREFULLY!")
        print()
        
        return True
    else:
        print()
        print("❌ Failed to start live bot")
        print("Restoring backup...")
        shutil.copy2(backup_path, filepath)
        print("✅ Backup restored")
        return False

if __name__ == "__main__":
    # Default to V2 Enhanced (best performer)
    bot = sys.argv[1] if len(sys.argv) > 1 else '1'
    go_live(bot)

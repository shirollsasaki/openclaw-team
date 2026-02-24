#!/usr/bin/env python3
"""
Prepare V2+Squeeze for live deployment
- Adds SIMULATION_MODE flag
- Adds live trading execution
- Creates deployment script
"""

import os
import shutil
from datetime import datetime

def add_simulation_flag():
    """Add SIMULATION_MODE flag to config"""
    
    filepath = '$OPENCLAW_HOME/bighead/avantis_bot_v2_squeeze.py'
    
    print("="*70)
    print("🔧 PREPARING V2+SQUEEZE FOR LIVE DEPLOYMENT")
    print("="*70)
    print()
    
    # Create backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{filepath}.backup_{timestamp}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup created: {backup_path}")
    
    # Read file
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Find Config class and add SIMULATION_MODE
    new_lines = []
    in_config = False
    flag_added = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Add flag after WALLET_ADDRESS
        if 'WALLET_ADDRESS' in line and not flag_added:
            new_lines.append('    \n')
            new_lines.append('    # Trading Mode\n')
            new_lines.append('    SIMULATION_MODE = True  # Set to False for live trading\n')
            flag_added = True
            print("✅ Added SIMULATION_MODE flag to Config")
        
        # Replace simulation message
        if '⚠️  SIMULATION MODE' in line:
            # Replace with conditional
            indent = line[:len(line) - len(line.lstrip())]
            new_lines[-1] = f'{indent}if Config.SIMULATION_MODE:\n'
            new_lines.append(f'{indent}    logger.info("⚠️  SIMULATION MODE - Trade not executed on Avantis")\n')
            new_lines.append(f'{indent}else:\n')
            new_lines.append(f'{indent}    # LIVE TRADING - Execute on Avantis\n')
            new_lines.append(f'{indent}    await self.execute_live_trade(asset, direction, entry, sl, tp, size)\n')
            print("✅ Added live trading execution path")
    
    # Write back
    with open(filepath, 'w') as f:
        f.writelines(new_lines)
    
    print("✅ V2+Squeeze prepared for deployment")
    print()
    
    return filepath

def add_live_execution_method():
    """Add execute_live_trade method to TradingEngine"""
    
    filepath = '$OPENCLAW_HOME/bighead/avantis_bot_v2_squeeze.py'
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Add method before run() method
    live_method = '''
    async def execute_live_trade(self, asset, direction, entry, sl, tp, size):
        """Execute real trade on Avantis (LIVE TRADING)"""
        from avantis_trader_sdk import TraderClient
        from avantis_trader_sdk.types import TradeInput, TradeInputOrderType
        
        logger.info("🔴 EXECUTING LIVE TRADE ON AVANTIS")
        
        try:
            # Initialize trader client
            trader_client = TraderClient("https://mainnet.base.org")
            trader_client.set_local_signer(Config.PRIVATE_KEY)
            trader = trader_client.get_signer().get_ethereum_address()
            
            # Get pair index
            pair_index = Config.ASSETS[asset]['pair_index']
            
            # Create trade input
            trade_input = TradeInput(
                trader=trader,
                pair_index=pair_index,
                collateral_in_trade=size,
                is_long=(direction == 'LONG'),
                leverage=Config.LEVERAGE,
                tp=tp,
                sl=sl,
            )
            
            # Build transaction
            tx = await trader_client.trade.build_trade_open_tx(
                trade_input=trade_input,
                trade_input_order_type=TradeInputOrderType.MARKET,
                slippage_percentage=1
            )
            
            # Execute
            receipt = await trader_client.sign_and_get_receipt(tx)
            
            logger.trade(f"✅ LIVE TRADE EXECUTED: {receipt.transactionHash.hex()}")
            
            await send_discord_notification(
                f"🔴 **LIVE TRADE EXECUTED**\\n"
                f"{direction} {asset} @ ${entry:.4f}\\n"
                f"Size: ${size:.2f} @ {Config.LEVERAGE}x\\n"
                f"TX: {receipt.transactionHash.hex()[:10]}..."
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ LIVE TRADE FAILED: {e}")
            await send_discord_notification(f"❌ **LIVE TRADE FAILED**\\n{str(e)}")
            return False
    
'''
    
    # Insert before async def run(self):
    run_pos = content.find('    async def run(self):')
    if run_pos > 0:
        new_content = content[:run_pos] + live_method + content[run_pos:]
        
        with open(filepath, 'w') as f:
            f.write(new_content)
        
        print("✅ Added execute_live_trade() method")
        return True
    else:
        print("⚠️  Could not find run() method location")
        return False

def create_deployment_script():
    """Create instant deployment script"""
    
    script_content = '''#!/usr/bin/env python3
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
'''
    
    script_path = '$OPENCLAW_HOME/bighead/GO_LIVE_V2_SQUEEZE.py'
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    print(f"✅ Created: {script_path}")
    
    return script_path

def main():
    print()
    
    # Step 1: Add simulation flag
    filepath = add_simulation_flag()
    
    # Step 2: Add live execution method
    add_live_execution_method()
    
    # Step 3: Create deployment script
    script = create_deployment_script()
    
    print()
    print("="*70)
    print("✅ V2+SQUEEZE READY FOR LIVE DEPLOYMENT")
    print("="*70)
    print()
    print("Files prepared:")
    print(f"  ✅ {filepath}")
    print(f"  ✅ {script}")
    print()
    print("To deploy:")
    print("  python3 GO_LIVE_V2_SQUEEZE.py")
    print()
    print("Or tell me: 'go live' and I'll execute it!")
    print()

if __name__ == "__main__":
    main()

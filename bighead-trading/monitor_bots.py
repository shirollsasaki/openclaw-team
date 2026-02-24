#!/usr/bin/env python3
"""
Monitor both bots and post updates to Discord
Shows table format in chat
"""

import time
import os
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', '')
UPDATE_INTERVAL = 300  # 5 minutes

async def send_discord_update(message):
    """Send formatted update to Discord"""
    if not DISCORD_WEBHOOK:
        print("No Discord webhook configured")
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(DISCORD_WEBHOOK, json={'content': message})
        print(f"✅ Sent update to Discord")
    except Exception as e:
        print(f"❌ Failed to send Discord update: {e}")

def parse_log_table(log_file):
    """Parse the latest table from log file"""
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Find the last table
        table_lines = []
        in_table = False
        
        for line in reversed(lines):
            if '====' in line and table_lines:
                # Found start of table
                table_lines.append(line.strip())
                break
            elif '====' in line:
                # Found end of table
                in_table = True
                table_lines.append(line.strip())
            elif in_table:
                table_lines.append(line.strip())
        
        if table_lines:
            table_lines.reverse()
            return '\n'.join(table_lines)
        
        return None
    
    except Exception as e:
        print(f"Error parsing {log_file}: {e}")
        return None

async def monitor_loop():
    """Main monitoring loop"""
    print("🔍 Bot Monitor Started")
    print(f"📊 Posting updates to Discord every {UPDATE_INTERVAL} seconds")
    print("="*70)
    
    while True:
        try:
            # Parse both logs
            v1_table = parse_log_table('strategy1_bot.log')
            v2_table = parse_log_table('strategy1_v2.log')
            
            if v1_table or v2_table:
                message = "📊 **Bot Status Update**\n\n"
                
                if v1_table:
                    message += "**V1 (Original Strategy):**\n```\n"
                    message += v1_table
                    message += "\n```\n\n"
                
                if v2_table:
                    message += "**V2 (Enhanced Strategy):**\n```\n"
                    message += v2_table
                    message += "\n```"
                
                await send_discord_update(message)
            
            else:
                print("⏳ Waiting for data...")
            
            await asyncio.sleep(UPDATE_INTERVAL)
        
        except KeyboardInterrupt:
            print("\n👋 Monitor stopped")
            break
        except Exception as e:
            print(f"❌ Error in monitor loop: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(monitor_loop())

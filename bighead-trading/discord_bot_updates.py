#!/usr/bin/env python3
"""
Send bot status updates to Discord every 5 minutes
"""

import asyncio
import aiohttp
import os
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', '')
UPDATE_INTERVAL = 300  # 5 minutes

BOTS = {
    'V1': {'name': 'V1 Baseline', 'log': 'strategy1_bot.log', 'emoji': '📊'},
    'V2': {'name': 'V2 Enhanced', 'log': 'strategy1_v2.log', 'emoji': '📈'},
    'V2+Sq': {'name': 'V2+Squeeze', 'log': 'strategy1_v2_squeeze.log', 'emoji': '🎯'},
    'V2+All': {'name': 'V2+Sq+All3', 'log': 'strategy1_v2_squeeze_all3.log', 'emoji': '⭐'}
}

def get_latest_stats(log_file):
    """Extract latest stats from log file"""
    if not os.path.exists(log_file):
        return None
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        recent = lines[-50:] if len(lines) > 50 else lines
        
        stats = {
            'equity': 30.0,
            'unrealized': 0.0,
            'total': 30.0,
            'open': 0,
            'long': 0,
            'short': 0,
            'last_update': 'Unknown',
            'running': False
        }
        
        for line in reversed(recent):
            if 'Equity:' in line:
                equity_match = re.search(r'Equity: \$(\d+\.\d+)', line)
                unrealized_match = re.search(r'Unrealized: \$([+-]?\d+\.\d+)', line)
                total_match = re.search(r'Total: \$(\d+\.\d+)', line)
                open_match = re.search(r'Open: (\d+)', line)
                ls_match = re.search(r'\(L:(\d+)/S:(\d+)\)', line)
                
                if equity_match:
                    stats['equity'] = float(equity_match.group(1))
                if unrealized_match:
                    stats['unrealized'] = float(unrealized_match.group(1))
                if total_match:
                    stats['total'] = float(total_match.group(1))
                if open_match:
                    stats['open'] = int(open_match.group(1))
                if ls_match:
                    stats['long'] = int(ls_match.group(1))
                    stats['short'] = int(ls_match.group(2))
                
                ts_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
                if ts_match:
                    stats['last_update'] = ts_match.group(1)
                
                stats['running'] = True
                break
        
        return stats
    except:
        return None

async def send_discord_update():
    """Generate and send Discord update"""
    if not DISCORD_WEBHOOK:
        print("❌ No Discord webhook configured")
        return
    
    # Collect stats
    all_stats = {}
    for bot_id, config in BOTS.items():
        stats = get_latest_stats(config['log'])
        if stats:
            all_stats[bot_id] = stats
    
    if not all_stats:
        print("❌ No bot stats found")
        return
    
    # Build message
    lines = []
    lines.append(f"🤖 **BOT UPDATE** - {datetime.now().strftime('%H:%M:%S')}")
    lines.append("")
    
    # Individual stats
    for bot_id, config in BOTS.items():
        if bot_id not in all_stats:
            continue
        
        stats = all_stats[bot_id]
        emoji = config['emoji']
        name = config['name']
        
        pnl = stats['total'] - 30.0
        pnl_pct = (pnl / 30.0) * 100
        pnl_emoji = "📈" if pnl > 0 else "📉" if pnl < 0 else "➡️"
        
        status = "🟢" if stats['running'] else "🔴"
        
        lines.append(f"{status} {emoji} **{name}**")
        lines.append(f"  💰 ${stats['total']:.2f} {pnl_emoji} {pnl:+.2f} ({pnl_pct:+.1f}%)")
        
        if stats['open'] > 0:
            lines.append(f"  📊 {stats['open']} open (L:{stats['long']}/S:{stats['short']})")
        
        lines.append("")
    
    # Leaderboard
    sorted_bots = sorted(
        [(bot_id, stats) for bot_id, stats in all_stats.items()],
        key=lambda x: x[1]['total'],
        reverse=True
    )
    
    lines.append("**📊 LEADERBOARD**")
    for i, (bot_id, stats) in enumerate(sorted_bots, 1):
        name = BOTS[bot_id]['name']
        pnl = stats['total'] - 30.0
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        lines.append(f"{medal} {i}. {name}: ${stats['total']:.2f} ({pnl:+.2f})")
    
    message = "\n".join(lines)
    
    # Send to Discord
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(DISCORD_WEBHOOK, json={'content': message})
        print(f"✅ Update sent to Discord at {datetime.now().strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"❌ Failed to send Discord update: {e}")

async def main():
    print("🤖 Discord Bot Monitor Started")
    print(f"📢 Sending updates every {UPDATE_INTERVAL//60} minutes")
    print(f"🔗 Webhook: {'✅ Configured' if DISCORD_WEBHOOK else '❌ Not configured'}")
    print("")
    
    if not DISCORD_WEBHOOK:
        print("⚠️  Set DISCORD_WEBHOOK in .env to enable updates")
        return
    
    # Send initial update
    await send_discord_update()
    
    # Continuous loop
    while True:
        await asyncio.sleep(UPDATE_INTERVAL)
        await send_discord_update()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Discord monitor stopped")

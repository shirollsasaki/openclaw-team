#!/usr/bin/env python3
"""
Monitor all 4 trading bots and send periodic updates
"""

import asyncio
import aiohttp
import os
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', '')

BOTS = {
    'V1': {
        'name': 'Strategy 1 V1 (Baseline)',
        'log': 'strategy1_bot.log',
        'trades': 'strategy1_trades.csv',
        'emoji': '📊'
    },
    'V2': {
        'name': 'Strategy 1 V2 (10 Improvements)',
        'log': 'strategy1_v2.log',
        'trades': 'strategy1_v2_trades.csv',
        'emoji': '📈'
    },
    'V2+Squeeze': {
        'name': 'Strategy 1 V2 + Squeeze',
        'log': 'strategy1_v2_squeeze.log',
        'trades': 'strategy1_v2_squeeze_trades.csv',
        'emoji': '🎯'
    },
    'V2+Squeeze+All3': {
        'name': 'Strategy 1 V2 Squeeze + All 3 (Ultimate)',
        'log': 'strategy1_v2_squeeze_all3.log',
        'trades': 'strategy1_v2_squeeze_all3_trades.csv',
        'emoji': '⭐'
    }
}

class BotMonitor:
    def __init__(self):
        self.last_lines = {bot: 0 for bot in BOTS.keys()}
        self.last_update = datetime.now()
        self.stats = {bot: self._init_stats() for bot in BOTS.keys()}
    
    def _init_stats(self):
        return {
            'running': False,
            'equity': 30.0,
            'realized_pnl': 0.0,
            'unrealized_pnl': 0.0,
            'total_equity': 30.0,
            'open_positions': 0,
            'long_positions': 0,
            'short_positions': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'consecutive_losses': 0,
            'last_activity': None,
            'signals_detected': 0,
            'trades_opened': 0,
            'trades_closed': 0
        }
    
    def parse_log_line(self, bot, line):
        """Extract info from log line"""
        stats = self.stats[bot]
        
        # Check if bot is running
        if 'started' in line.lower() or 'running' in line.lower():
            stats['running'] = True
            stats['last_activity'] = datetime.now()
        
        # Extract equity info
        equity_match = re.search(r'Equity: \$(\d+\.\d+)', line)
        if equity_match:
            stats['equity'] = float(equity_match.group(1))
            stats['last_activity'] = datetime.now()
        
        unrealized_match = re.search(r'Unrealized: \$([+-]?\d+\.\d+)', line)
        if unrealized_match:
            stats['unrealized_pnl'] = float(unrealized_match.group(1))
        
        realized_match = re.search(r'Realized: \$([+-]?\d+\.\d+)', line)
        if realized_match:
            stats['realized_pnl'] = float(realized_match.group(1))
        
        total_match = re.search(r'Total: \$(\d+\.\d+)', line)
        if total_match:
            stats['total_equity'] = float(total_match.group(1))
        
        # Extract position counts
        open_match = re.search(r'Open: (\d+)', line)
        if open_match:
            stats['open_positions'] = int(open_match.group(1))
        
        long_short_match = re.search(r'\(L:(\d+)/S:(\d+)\)', line)
        if long_short_match:
            stats['long_positions'] = int(long_short_match.group(1))
            stats['short_positions'] = int(long_short_match.group(2))
        
        # Track trade events
        if 'OPENED LONG' in line or 'OPENED SHORT' in line:
            stats['trades_opened'] += 1
            stats['total_trades'] += 1
            stats['last_activity'] = datetime.now()
        
        if 'CLOSED LONG' in line or 'CLOSED SHORT' in line:
            stats['trades_closed'] += 1
            stats['last_activity'] = datetime.now()
            
            # Check if win/loss
            if 'TP' in line:
                stats['winning_trades'] += 1
                stats['consecutive_losses'] = 0
            elif 'SL' in line:
                stats['losing_trades'] += 1
                stats['consecutive_losses'] += 1
        
        # Track signals
        if 'signal' in line.lower() and ('long' in line.lower() or 'short' in line.lower()):
            stats['signals_detected'] += 1
    
    def read_new_lines(self, bot):
        """Read new lines from log file"""
        log_file = f'$OPENCLAW_HOME/bighead/{BOTS[bot]["log"]}'
        
        if not os.path.exists(log_file):
            return []
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            new_lines = lines[self.last_lines[bot]:]
            self.last_lines[bot] = len(lines)
            
            return new_lines
        except:
            return []
    
    def update_stats(self):
        """Update stats for all bots"""
        for bot in BOTS.keys():
            new_lines = self.read_new_lines(bot)
            for line in new_lines:
                self.parse_log_line(bot, line)
    
    def generate_summary(self):
        """Generate summary report"""
        lines = []
        lines.append("=" * 70)
        lines.append(f"🤖 BOT MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 70)
        lines.append("")
        
        # Individual bot stats
        for bot, config in BOTS.items():
            stats = self.stats[bot]
            emoji = config['emoji']
            name = bot
            
            status = "🟢 RUNNING" if stats['running'] else "🔴 STOPPED"
            
            lines.append(f"{emoji} **{name}** - {status}")
            lines.append("-" * 70)
            
            # Equity
            equity_change = stats['total_equity'] - 30.0
            equity_pct = (equity_change / 30.0) * 100
            equity_emoji = "📈" if equity_change > 0 else "📉" if equity_change < 0 else "➡️"
            
            lines.append(f"  Equity: ${stats['equity']:.2f} | Unrealized: ${stats['unrealized_pnl']:+.2f} | Total: ${stats['total_equity']:.2f}")
            lines.append(f"  {equity_emoji} P&L: ${equity_change:+.2f} ({equity_pct:+.1f}%)")
            
            # Positions
            lines.append(f"  Positions: {stats['open_positions']} open (L:{stats['long_positions']}/S:{stats['short_positions']})")
            
            # Trades
            if stats['total_trades'] > 0:
                win_rate = (stats['winning_trades'] / stats['total_trades']) * 100
                lines.append(f"  Trades: {stats['total_trades']} total | Wins: {stats['winning_trades']} | Losses: {stats['losing_trades']} | WR: {win_rate:.1f}%")
            else:
                lines.append(f"  Trades: {stats['total_trades']} total | No trades yet")
            
            # Activity
            if stats['last_activity']:
                time_since = (datetime.now() - stats['last_activity']).seconds
                if time_since < 120:
                    lines.append(f"  Last activity: {time_since}s ago")
                else:
                    lines.append(f"  Last activity: {time_since // 60}m ago")
            
            lines.append("")
        
        # Comparison
        lines.append("=" * 70)
        lines.append("📊 COMPARISON (Sorted by P&L)")
        lines.append("=" * 70)
        
        # Sort by total equity
        sorted_bots = sorted(BOTS.keys(), key=lambda b: self.stats[b]['total_equity'], reverse=True)
        
        for i, bot in enumerate(sorted_bots, 1):
            stats = self.stats[bot]
            pnl = stats['total_equity'] - 30.0
            pnl_pct = (pnl / 30.0) * 100
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            
            wr = 0
            if stats['total_trades'] > 0:
                wr = (stats['winning_trades'] / stats['total_trades']) * 100
            
            lines.append(f"{medal} {i}. {bot:<20} ${stats['total_equity']:.2f} ({pnl:+.2f} / {pnl_pct:+.1f}%) | {stats['total_trades']} trades | {wr:.0f}% WR")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    async def send_discord(self, message):
        """Send Discord notification"""
        if not DISCORD_WEBHOOK:
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(DISCORD_WEBHOOK, json={'content': f"```\n{message}\n```"})
        except Exception as e:
            print(f"Discord notification failed: {e}")
    
    async def run(self, update_interval=300):
        """Run monitoring loop"""
        print("🤖 Bot Monitor Started")
        print(f"📊 Monitoring {len(BOTS)} bots")
        print(f"⏱️  Update interval: {update_interval}s ({update_interval//60}min)")
        print(f"📢 Discord notifications: {'✅ Enabled' if DISCORD_WEBHOOK else '❌ Disabled'}")
        print("")
        
        iteration = 0
        
        while True:
            iteration += 1
            
            # Update stats
            self.update_stats()
            
            # Generate summary
            summary = self.generate_summary()
            
            # Print to console
            print("\033[2J\033[H")  # Clear screen
            print(summary)
            
            # Send to Discord every update
            if DISCORD_WEBHOOK:
                await self.send_discord(summary)
                print(f"\n✅ Update #{iteration} sent to Discord")
            
            # Wait
            await asyncio.sleep(update_interval)

async def main():
    monitor = BotMonitor()
    
    # Initial quick update
    monitor.update_stats()
    summary = monitor.generate_summary()
    print(summary)
    
    if DISCORD_WEBHOOK:
        await monitor.send_discord(summary)
        print("\n✅ Initial update sent to Discord")
    
    print(f"\nStarting continuous monitoring (updates every 5 minutes)...")
    print("Press Ctrl+C to stop\n")
    
    await asyncio.sleep(3)
    
    # Run continuous monitoring
    await monitor.run(update_interval=300)  # 5 minutes

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped by user")

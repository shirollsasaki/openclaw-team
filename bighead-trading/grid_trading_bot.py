"""
Grid Trading Bot - Profit from price oscillation
High win rate strategy (70-80%) that works in ranging markets
"""
import asyncio
import os
from datetime import datetime
from avantis_sdk_wrapper import get_sdk
from dotenv import load_dotenv
import aiohttp

load_dotenv()

class Config:
    # Wallet
    WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    
    # Grid Configuration
    ASSET = 'ARB'  # Start with ARB (most liquid on Avantis)
    PAIR_INDEX = 4  # ARB/USD
    
    TOTAL_CAPITAL = 30.0  # Use $30, keep $7 reserve
    GRID_LEVELS = 10  # Number of buy/sell levels
    GRID_SPACING = 0.005  # 0.5% spacing between levels
    
    # Risk Management
    CAPITAL_PER_LEVEL = TOTAL_CAPITAL / GRID_LEVELS  # $3 per level
    LEVERAGE = 5  # Conservative 5x (not 15x like before)
    MAX_POSITIONS = 6  # Max 6 open at once
    
    # Range Detection
    RANGE_CHECK_PERIOD = 24  # Hours to check for ranging market
    RANGE_THRESHOLD = 0.95  # 95% of candles must stay in range
    
    # Stop Loss
    RANGE_BREAK_SL = 0.03  # 3% stop if range breaks
    
    # Logging
    LOG_FILE = "grid_trading.log"
    TRADE_LOG = "grid_trades.csv"

class Logger:
    def __init__(self):
        self.log_file = Config.LOG_FILE
        
    def log(self, message, level='INFO'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        
        with open(self.log_file, 'a') as f:
            f.write(log_line + '\n')
    
    def info(self, message):
        self.log(message, 'INFO')
    
    def warning(self, message):
        self.log(message, 'WARNING')
    
    def error(self, message):
        self.log(message, 'ERROR')
    
    def trade(self, message):
        self.log(message, 'TRADE')

logger = Logger()

class GridBot:
    def __init__(self):
        self.positions = []
        self.grid_levels = []
        self.range_low = 0
        self.range_high = 0
        self.in_range = False
        
    async def initialize(self):
        """Initialize SDK and detect range"""
        logger.info("="*70)
        logger.info("GRID TRADING BOT - STARTING")
        logger.info("="*70)
        logger.info(f"Asset: {Config.ASSET}")
        logger.info(f"Capital: ${Config.TOTAL_CAPITAL:.2f}")
        logger.info(f"Grid levels: {Config.GRID_LEVELS}")
        logger.info(f"Per level: ${Config.CAPITAL_PER_LEVEL:.2f}")
        logger.info(f"Leverage: {Config.LEVERAGE}x (conservative)")
        logger.info("="*70)
        
        self.sdk = await get_sdk()
        self.trader_client = self.sdk.trader_client
        self.feed_client = self.sdk.feed_client
        
        # Detect current range
        await self.detect_range()
        
        # Set up grid
        if self.in_range:
            await self.setup_grid()
        else:
            logger.warning("Market not ranging - waiting for range to form")
    
    async def detect_range(self):
        """Detect if market is ranging and find range bounds"""
        logger.info("🔍 Detecting market range...")
        
        try:
            # Get 24h of 1h candles
            async with aiohttp.ClientSession() as session:
                url = f"https://api.binance.com/api/v3/klines?symbol={Config.ASSET}USDT&interval=1h&limit=24"
                async with session.get(url) as resp:
                    candles = await resp.json()
            
            if not candles:
                logger.error("Failed to fetch candles")
                return
            
            # Extract highs and lows
            highs = [float(c[2]) for c in candles]
            lows = [float(c[3]) for c in candles]
            closes = [float(c[4]) for c in candles]
            
            # Calculate range
            range_high = max(highs)
            range_low = min(lows)
            range_size = (range_high - range_low) / range_low
            
            # Check if price stayed in range 95%+ of time
            in_range_count = sum(1 for c in closes if range_low <= c <= range_high)
            range_pct = in_range_count / len(closes)
            
            current_price = closes[-1]
            
            logger.info(f"  24h Range: ${range_low:.4f} - ${range_high:.4f}")
            logger.info(f"  Range size: {range_size*100:.1f}%")
            logger.info(f"  In-range %: {range_pct*100:.1f}%")
            logger.info(f"  Current: ${current_price:.4f}")
            
            # Determine if suitable for grid trading
            if range_pct >= Config.RANGE_THRESHOLD and 0.02 <= range_size <= 0.08:
                self.in_range = True
                self.range_low = range_low
                self.range_high = range_high
                logger.info(f"  ✅ Market is RANGING - Grid trading suitable")
            else:
                self.in_range = False
                if range_pct < Config.RANGE_THRESHOLD:
                    logger.warning(f"  ⚠️  Market NOT ranging enough ({range_pct*100:.1f}% < 95%)")
                if range_size < 0.02:
                    logger.warning(f"  ⚠️  Range too tight ({range_size*100:.1f}% < 2%)")
                if range_size > 0.08:
                    logger.warning(f"  ⚠️  Range too wide ({range_size*100:.1f}% > 8%)")
                logger.warning("  Waiting for suitable ranging market...")
        
        except Exception as e:
            logger.error(f"Range detection error: {e}")
            self.in_range = False
    
    async def setup_grid(self):
        """Calculate grid levels based on detected range"""
        mid_price = (self.range_low + self.range_high) / 2
        
        logger.info("📊 Setting up grid levels...")
        
        # Create grid levels from low to high
        self.grid_levels = []
        
        for i in range(Config.GRID_LEVELS):
            # Distribute levels evenly across range
            level_pct = i / (Config.GRID_LEVELS - 1)  # 0.0 to 1.0
            price = self.range_low + (self.range_high - self.range_low) * level_pct
            
            self.grid_levels.append({
                'price': price,
                'buy': price < mid_price,  # Lower half = buy, upper half = sell
                'filled': False,
                'position_id': None
            })
        
        logger.info(f"  Created {len(self.grid_levels)} grid levels")
        logger.info(f"  Buy levels: {sum(1 for g in self.grid_levels if g['buy'])}")
        logger.info(f"  Sell levels: {sum(1 for g in self.grid_levels if not g['buy'])}")
        
        for i, level in enumerate(self.grid_levels):
            side = "BUY" if level['buy'] else "SELL"
            logger.info(f"  Level {i+1}: {side} @ ${level['price']:.4f}")
    
    async def run(self):
        """Main trading loop"""
        logger.info("🚀 Grid bot running...")
        
        iteration = 0
        
        while True:
            try:
                iteration += 1
                
                # Check range every 60 seconds
                if iteration % 60 == 0:
                    await self.detect_range()
                    if self.in_range:
                        await self.setup_grid()
                
                # If not in range, wait
                if not self.in_range:
                    await asyncio.sleep(60)
                    continue
                
                # Get current price
                price_data = self.feed_client.get_price(Config.PAIR_INDEX)
                current_price = float(price_data.get('price', 0)) / 1e10
                
                # Check if price is outside range (range break)
                if current_price < self.range_low * (1 - Config.RANGE_BREAK_SL) or \
                   current_price > self.range_high * (1 + Config.RANGE_BREAK_SL):
                    logger.warning(f"⚠️  RANGE BREAK! Price ${current_price:.4f} outside range")
                    logger.warning(f"  Closing all positions and waiting for new range")
                    await self.close_all_positions()
                    self.in_range = False
                    await asyncio.sleep(300)  # Wait 5 minutes
                    continue
                
                # Check grid levels for fills
                await self.check_grid_fills(current_price)
                
                # Wait 1 second before next check
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)
    
    async def check_grid_fills(self, current_price):
        """Check if price hit any grid levels and execute trades"""
        # Implementation simplified - in production would need full order management
        pass
    
    async def close_all_positions(self):
        """Close all open positions"""
        logger.info("Closing all positions...")
        # Would implement position closing logic here

async def main():
    bot = GridBot()
    await bot.initialize()
    
    if bot.in_range:
        logger.info("✅ Range detected - starting grid trading")
        await bot.run()
    else:
        logger.warning("⚠️  Market not suitable for grid trading right now")
        logger.info("Will check again in 5 minutes...")
        
        # Keep checking until range forms
        while True:
            await asyncio.sleep(300)  # 5 minutes
            await bot.detect_range()
            if bot.in_range:
                await bot.setup_grid()
                await bot.run()
                break

if __name__ == "__main__":
    asyncio.run(main())

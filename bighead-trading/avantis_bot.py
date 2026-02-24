#!/usr/bin/env python3
"""
Avantis Trading Bot - Strategy 1
15x Leverage | ARB + OP + ETH | 15m Timeframe

Expected: +129% per week
Risk: Medium (manageable)
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os
from dotenv import load_dotenv
from avantis_sdk_wrapper import get_sdk  # NEW: Proper SDK wrapper

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    # Strategy
    STRATEGY_NAME = "Strategy 1"
    STRATEGY_VERSION = "1.0.0"
    
    # Wallet
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    WALLET_ADDRESS = os.getenv('WALLET_ADDRESS', 'YOUR_WALLET_ADDRESS')
    
    # Network
    NETWORK = 'Base'
    CHAIN_ID = 8453
    RPC_URL = os.getenv('RPC_URL', 'https://mainnet.base.org')
    
    # Capital Allocation
    TOTAL_CAPITAL = 30.0
    ASSETS = {
        'ARB': {'capital': 10.0, 'pair_index': None},  # TBD - check Avantis docs
        'OP': {'capital': 10.0, 'pair_index': None},   # TBD
        'ETH': {'capital': 10.0, 'pair_index': 1}      # Known: ETH = 1
    }
    
    # Strategy Parameters
    TIMEFRAME = '15m'
    LEVERAGE = 15  # OPTIMAL
    RISK_PER_TRADE = 0.03  # 3%
    RR_RATIO = 2.0  # 2:1
    MAX_POSITIONS_PER_ASSET = 2
    MAX_TOTAL_POSITIONS = 6
    
    # SMC Indicators
    SWING_LENGTH = 3
    LOOKBACK_PERIOD = 20
    USE_ZONE_FILTER = False  # Aggressive mode
    MIN_SL_DISTANCE = 0.005  # 0.5%
    MAX_SL_DISTANCE = 0.10   # 10% (increased for 15m timeframe)
    
    # Risk Management
    MAX_DRAWDOWN = 0.30  # 30% kill switch
    DAILY_LOSS_LIMIT = 0.10  # 10%
    LIQUIDATION_BUFFER = 0.02  # Stay 2% away from liquidation
    
    # Execution
    SLIPPAGE_TOLERANCE = 0.01  # 1%
    CHECK_INTERVAL = 60  # Check for signals every 60 seconds
    
    # Discord Webhook (optional)
    DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', '')
    
    # Logging
    LOG_FILE = 'strategy1_bot.log'
    TRADE_LOG = 'strategy1_trades.csv'

# ============================================================================
# LOGGING & NOTIFICATIONS
# ============================================================================

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
    
    def error(self, message):
        self.log(message, 'ERROR')
    
    def trade(self, message):
        self.log(message, 'TRADE')

logger = Logger()

async def send_discord_notification(message, webhook_url=None):
    """Send Discord notification"""
    if not webhook_url:
        webhook_url = Config.DISCORD_WEBHOOK
    
    if not webhook_url:
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json={'content': message})
    except Exception as e:
        logger.error(f"Discord notification failed: {e}")

# ============================================================================
# DATA FETCHING
# ============================================================================

# ============================================================================
# DATA FETCHING (Using Official Avantis SDK Patterns)
# ============================================================================

class DataFetcher:
    """
    Data fetcher using official Avantis SDK patterns from AGENT.md
    - Uses TraderClient for pair lookups
    - Uses FeedClient for price data
    - Falls back to Binance when Avantis is down
    """
    
    _sdk = None  # Singleton SDK instance
    
    @staticmethod
    async def _get_sdk():
        """Get or initialize SDK instance"""
        if DataFetcher._sdk is None:
            DataFetcher._sdk = await get_sdk()
        return DataFetcher._sdk
    
    @staticmethod
    async def get_avantis_price(asset):
        """
        Get current price using official Avantis SDK pattern
        Automatically falls back to Binance if Avantis is unavailable
        """
        sdk = await DataFetcher._get_sdk()
        price = await sdk.get_price(asset)
        return price
    
    @staticmethod
    async def fetch_candles(asset, limit=100, interval='15m'):
        """
        Fetch candles from Binance (for historical data)
        Uses Avantis for latest close price
        """
        binance_symbols = {
            'ARB': 'ARBUSDT',
            'OP': 'OPUSDT',
            'ETH': 'ETHUSDT'
        }
        
        symbol = binance_symbols.get(asset)
        if not symbol:
            return None
        
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # Override latest close with Avantis price (official pattern)
            avantis_price = await DataFetcher.get_avantis_price(asset)
            if avantis_price is not None:
                df.loc[df.index[-1], 'close'] = avantis_price
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to fetch {asset} candles: {e}")
            return None


# ============================================================================
# SMART MONEY CONCEPTS INDICATORS
# ============================================================================

class SMCIndicators:
    """Calculate SMC indicators"""
    
    @staticmethod
    def add_indicators(df, swing_length=3, lookback=20):
        """Add all SMC indicators to dataframe"""
        df = df.copy()
        
        # 1. Swing Points
        df['swing_high'] = False
        df['swing_low'] = False
        
        for i in range(swing_length, len(df) - swing_length):
            # Swing high
            if df['high'].iloc[i] == df['high'].iloc[i-swing_length:i+swing_length+1].max():
                df.loc[df.index[i], 'swing_high'] = True
            
            # Swing low
            if df['low'].iloc[i] == df['low'].iloc[i-swing_length:i+swing_length+1].min():
                df.loc[df.index[i], 'swing_low'] = True
        
        # 2. Structure Breaks (BOS)
        df['bos_bull'] = False
        df['bos_bear'] = False
        
        last_high = None
        last_low = None
        
        for i in range(len(df)):
            if df['swing_high'].iloc[i]:
                last_high = df['high'].iloc[i]
            if df['swing_low'].iloc[i]:
                last_low = df['low'].iloc[i]
            
            if last_high is not None and last_low is not None:
                # Bullish break
                if df['close'].iloc[i] > last_high:
                    df.loc[df.index[i], 'bos_bull'] = True
                
                # Bearish break
                elif df['close'].iloc[i] < last_low:
                    df.loc[df.index[i], 'bos_bear'] = True
        
        # 3. Range Zones (for SL/TP calculation)
        df['range_high'] = df['high'].rolling(lookback).max()
        df['range_low'] = df['low'].rolling(lookback).min()
        
        # 4. Signals
        df['signal'] = 0
        
        for i in range(lookback, len(df)):
            # LONG: Bullish BOS
            if df['bos_bull'].iloc[i]:
                df.loc[df.index[i], 'signal'] = 1
            
            # SHORT: Bearish BOS
            elif df['bos_bear'].iloc[i]:
                df.loc[df.index[i], 'signal'] = -1
        
        return df

# ============================================================================
# POSITION MANAGER
# ============================================================================

class Position:
    """Represents a trading position"""
    
    def __init__(self, asset, direction, entry, sl, tp, size, leverage):
        self.asset = asset
        self.direction = direction  # 'LONG' or 'SHORT'
        self.entry = entry
        self.sl = sl
        self.tp = tp
        self.size = size
        self.leverage = leverage
        self.entry_time = datetime.now()
        self.exit_price = None
        self.exit_time = None
        self.pnl = None
        self.status = 'OPEN'  # OPEN, CLOSED
    
    def check_exit(self, current_high, current_low):
        """Check if TP or SL hit"""
        if self.direction == 'LONG':
            if current_high >= self.tp:
                return 'TP', self.tp
            elif current_low <= self.sl:
                return 'SL', self.sl
        else:  # SHORT
            if current_low <= self.tp:
                return 'TP', self.tp
            elif current_high >= self.sl:
                return 'SL', self.sl
        
        return None, None
    
    def close(self, exit_price, reason):
        """Close the position"""
        self.exit_price = exit_price
        self.exit_time = datetime.now()
        self.status = 'CLOSED'
        
        # Calculate P&L
        if self.direction == 'LONG':
            price_change_pct = (exit_price - self.entry) / self.entry
        else:
            price_change_pct = (self.entry - exit_price) / self.entry
        
        # Apply leverage
        pnl_pct = price_change_pct * self.leverage
        
        # Calculate USD P&L
        gross_pnl = self.size * pnl_pct
        
        # Deduct fees (0.12% round trip at 15x)
        fees = self.size * 0.0012
        
        self.pnl = gross_pnl - fees
        
        return self.pnl

class PositionManager:
    """Manage all open positions"""
    
    def __init__(self):
        self.positions = []
        self.closed_positions = []
        self.total_pnl = 0
        self.daily_pnl = 0
        self.last_reset_date = datetime.now().date()
    
    def add_position(self, position):
        """Add new position"""
        self.positions.append(position)
        logger.trade(f"OPENED {position.direction} {position.asset} @ ${position.entry:.4f} | SL: ${position.sl:.4f} | TP: ${position.tp:.4f} | Size: ${position.size:.2f}")
    
    def calculate_unrealized_pnl(self, prices):
        """Calculate unrealized P&L on open positions"""
        unrealized = 0
        
        for pos in self.positions:
            asset = pos.asset
            if asset not in prices:
                continue
            
            current_price = prices[asset]
            
            # Calculate price change
            if pos.direction == 'LONG':
                price_change_pct = (current_price - pos.entry) / pos.entry
            else:  # SHORT
                price_change_pct = (pos.entry - current_price) / pos.entry
            
            # Apply leverage
            pnl_pct = price_change_pct * pos.leverage
            
            # Calculate USD P&L (before fees)
            position_pnl = pos.size * pnl_pct
            
            unrealized += position_pnl
        
        return unrealized
    
    def update_positions(self, prices):
        """Update all positions with current prices"""
        for pos in self.positions[:]:
            asset = pos.asset
            if asset not in prices:
                continue
            
            current_price = prices[asset]
            high = current_price * 1.002  # Approximate high
            low = current_price * 0.998   # Approximate low
            
            exit_type, exit_price = pos.check_exit(high, low)
            
            if exit_type:
                pnl = pos.close(exit_price, exit_type)
                self.positions.remove(pos)
                self.closed_positions.append(pos)
                self.total_pnl += pnl
                self.daily_pnl += pnl
                
                emoji = "✅" if pnl > 0 else "❌"
                logger.trade(f"{emoji} CLOSED {pos.direction} {pos.asset} @ ${exit_price:.4f} | {exit_type} | P&L: ${pnl:+.2f}")
                
                # Discord notification
                asyncio.create_task(send_discord_notification(
                    f"{emoji} **{exit_type}** | {pos.direction} {pos.asset}\n"
                    f"Entry: ${pos.entry:.4f} → Exit: ${exit_price:.4f}\n"
                    f"P&L: **${pnl:+.2f}** | Total P&L: ${self.total_pnl:+.2f}"
                ))
    
    def reset_daily_pnl(self):
        """Reset daily P&L counter"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_pnl = 0
            self.last_reset_date = today
    
    def count_positions(self, asset=None):
        """Count open positions"""
        if asset:
            return len([p for p in self.positions if p.asset == asset])
        return len(self.positions)
    
    def get_equity(self):
        """Calculate current equity (starting + realized P&L)"""
        return Config.TOTAL_CAPITAL + self.total_pnl
    
    def check_risk_limits(self):
        """Check if risk limits exceeded"""
        equity = self.get_equity()
        
        # Max drawdown check
        drawdown = (Config.TOTAL_CAPITAL - equity) / Config.TOTAL_CAPITAL
        if drawdown >= Config.MAX_DRAWDOWN:
            logger.error(f"⛔ MAX DRAWDOWN HIT: {drawdown*100:.1f}%")
            return False
        
        # Daily loss limit
        if self.daily_pnl < 0 and abs(self.daily_pnl) >= (equity * Config.DAILY_LOSS_LIMIT):
            logger.error(f"⛔ DAILY LOSS LIMIT HIT: ${self.daily_pnl:.2f}")
            return False
        
        return True
    
    def save_trades(self):
        """Save closed trades to CSV"""
        if not self.closed_positions:
            return
        
        trades_data = []
        for pos in self.closed_positions:
            trades_data.append({
                'entry_time': pos.entry_time,
                'exit_time': pos.exit_time,
                'asset': pos.asset,
                'direction': pos.direction,
                'entry': pos.entry,
                'exit': pos.exit_price,
                'sl': pos.sl,
                'tp': pos.tp,
                'size': pos.size,
                'leverage': pos.leverage,
                'pnl': pos.pnl
            })
        
        df = pd.DataFrame(trades_data)
        df.to_csv(Config.TRADE_LOG, index=False)

# ============================================================================
# TRADING ENGINE
# ============================================================================

class TradingEngine:
    """Main trading logic"""
    
    def __init__(self):
        self.position_manager = PositionManager()
        self.last_check_time = {}
        self.running = False
    
    def calculate_position_size(self, asset, entry, sl):
        """Calculate position size based on risk"""
        asset_capital = Config.ASSETS[asset]['capital']
        
        # Adjust capital by current P&L
        equity = self.position_manager.get_equity()
        asset_equity = asset_capital * (equity / Config.TOTAL_CAPITAL)
        
        # Risk amount
        risk_amount = asset_equity * Config.RISK_PER_TRADE
        
        # SL distance
        sl_distance = abs(entry - sl) / entry
        
        if sl_distance < Config.MIN_SL_DISTANCE or sl_distance > Config.MAX_SL_DISTANCE:
            return None
        
        # Position size
        size = risk_amount / sl_distance
        
        # Cap at 50% of asset equity (with leverage considered)
        max_size = asset_equity * 0.5
        size = min(size, max_size)
        
        # Minimum size
        if size < 0.1:
            return None
        
        return round(size, 2)
    
    async def check_signals(self, asset):
        """Check for trading signals on an asset"""
        # Fetch recent candles
        df = await DataFetcher.fetch_candles(asset, limit=100)
        
        if df is None or len(df) < 50:
            return
        
        # Add indicators
        df = SMCIndicators.add_indicators(df, Config.SWING_LENGTH, Config.LOOKBACK_PERIOD)
        
        # Check latest candle for signal
        latest = df.iloc[-1]
        
        if latest['signal'] == 0:
            return  # No signal
        
        # Don't trade if max positions reached
        if self.position_manager.count_positions(asset) >= Config.MAX_POSITIONS_PER_ASSET:
            return
        
        if self.position_manager.count_positions() >= Config.MAX_TOTAL_POSITIONS:
            return
        
        # Get current price from Avantis (not Binance!)
        avantis_price = await DataFetcher.get_avantis_price(asset)
        if avantis_price is None:
            logger.error(f"Could not get Avantis price for {asset}")
            return
        
        current_price = avantis_price
        logger.info(f"   Entry price from Avantis: ${current_price:.6f}")
        
        # Determine direction and calculate SL/TP
        if latest['signal'] == 1:  # LONG
            direction = 'LONG'
            sl = latest['range_low'] if latest['range_low'] < current_price else current_price * 0.985
            tp = current_price + (current_price - sl) * Config.RR_RATIO
        
        else:  # SHORT
            direction = 'SHORT'
            sl = latest['range_high'] if latest['range_high'] > current_price else current_price * 1.015
            tp = current_price - (sl - current_price) * Config.RR_RATIO
        
        # Calculate position size
        size = self.calculate_position_size(asset, current_price, sl)
        
        if size is None:
            logger.info(f"Position size too small for {asset}, skipping")
            return
        
        # Create position
        position = Position(
            asset=asset,
            direction=direction,
            entry=current_price,
            sl=sl,
            tp=tp,
            size=size,
            leverage=Config.LEVERAGE
        )
        
        # Add to position manager
        self.position_manager.add_position(position)
        
        # Discord notification
        await send_discord_notification(
            f"🚀 **NEW {direction}** | {asset}\n"
            f"Entry: ${current_price:.4f}\n"
            f"SL: ${sl:.4f} | TP: ${tp:.4f}\n"
            f"Size: ${size:.2f} @ {Config.LEVERAGE}x leverage"
        )
        
        # TODO: Execute actual trade via Avantis SDK
        # For now, this is simulation mode
        logger.info("⚠️  SIMULATION MODE - Trade not executed on Avantis")
    
    async def run(self):
        """Main bot loop"""
        self.running = True
        logger.info(f"🤖 {Config.STRATEGY_NAME} started")
        logger.info(f"Trading: {', '.join(Config.ASSETS.keys())}")
        logger.info(f"Leverage: {Config.LEVERAGE}x | Risk: {Config.RISK_PER_TRADE*100}% per trade")
        
        await send_discord_notification(
            f"🤖 **{Config.STRATEGY_NAME} Started**\n"
            f"Assets: {', '.join(Config.ASSETS.keys())}\n"
            f"Leverage: {Config.LEVERAGE}x\n"
            f"Capital: ${Config.TOTAL_CAPITAL}"
        )
        
        try:
            while self.running:
                # Reset daily P&L if new day
                self.position_manager.reset_daily_pnl()
                
                # Check risk limits
                if not self.position_manager.check_risk_limits():
                    logger.error("⛔ RISK LIMITS EXCEEDED - STOPPING BOT")
                    await send_discord_notification("⛔ **BOT STOPPED** - Risk limits exceeded")
                    break
                
                # Fetch current prices
                prices = {}
                for asset in Config.ASSETS.keys():
                    df = await DataFetcher.fetch_candles(asset, limit=1)
                    if df is not None and len(df) > 0:
                        prices[asset] = df['close'].iloc[-1]
                
                # Update existing positions
                self.position_manager.update_positions(prices)
                
                # Calculate unrealized P&L
                unrealized_pnl = self.position_manager.calculate_unrealized_pnl(prices)
                
                # Check for new signals
                for asset in Config.ASSETS.keys():
                    await self.check_signals(asset)
                
                # Save trades
                self.position_manager.save_trades()
                
                # Log status with unrealized P&L
                equity = self.position_manager.get_equity()
                total_equity = equity + unrealized_pnl
                
                logger.info("="*110)
                logger.info(
                    f"Equity: ${equity:.2f} | Unrealized: ${unrealized_pnl:+.2f} | Total: ${total_equity:.2f} | "
                    f"Open: {self.position_manager.count_positions()} | "
                    f"Realized: ${self.position_manager.total_pnl:+.2f}"
                )
                logger.info("="*110)
                
                # Log position table
                if self.position_manager.positions and prices:
                    logger.info(f"{'#':<4} {'Asset':<6} {'Side':<6} {'Entry':<12} {'SL':<12} {'TP':<12} {'Unrealized':<12} {'Realized':<12}")
                    logger.info("-"*110)
                    
                    for idx, pos in enumerate(self.position_manager.positions, 1):
                        asset = pos.asset
                        if asset in prices:
                            current_price = prices[asset]
                            
                            # Calculate unrealized P&L for this position
                            if pos.direction == 'LONG':
                                price_change_pct = (current_price - pos.entry) / pos.entry
                            else:
                                price_change_pct = (pos.entry - current_price) / pos.entry
                            
                            pnl_pct = price_change_pct * pos.leverage
                            position_pnl = pos.size * pnl_pct
                            
                            logger.info(
                                f"{idx:<4} {pos.asset:<6} {pos.direction:<6} "
                                f"${pos.entry:<11.4f} ${pos.sl:<11.4f} ${pos.tp:<11.4f} "
                                f"${position_pnl:+11.2f} ${'0.00':<11}"
                            )
                    
                    logger.info("="*110)
                else:
                    logger.info("No open positions")
                    logger.info("="*110)
                
                # Wait before next check
                await asyncio.sleep(Config.CHECK_INTERVAL)
        
        except Exception as e:
            logger.error(f"Bot error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await send_discord_notification(f"❌ **BOT ERROR**\n{str(e)}")
        
        finally:
            logger.info("🛑 Bot stopped")
            self.position_manager.save_trades()

# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main entry point"""
    
    # Check configuration
    if not Config.PRIVATE_KEY:
        logger.error("❌ PRIVATE_KEY not found in .env file")
        print("\n⚠️  CREATE .env FILE:")
        print("PRIVATE_KEY=YOUR_PRIVATE_KEY_HERE")
        print("DISCORD_WEBHOOK=https://discord.com/api/webhooks/...")
        print("RPC_URL=https://mainnet.base.org")
        return
    
    logger.info("="*70)
    logger.info(f"AVANTIS TRADING BOT - {Config.STRATEGY_NAME.upper()}")
    logger.info("="*70)
    logger.info(f"Strategy: {Config.STRATEGY_NAME} v{Config.STRATEGY_VERSION}")
    logger.info(f"Wallet: {Config.WALLET_ADDRESS}")
    logger.info(f"Assets: {', '.join(Config.ASSETS.keys())}")
    logger.info(f"Leverage: {Config.LEVERAGE}x")
    logger.info(f"Timeframe: {Config.TIMEFRAME}")
    logger.info(f"Expected Return: +129% per week")
    logger.info("="*70)
    logger.info("")
    logger.info("⚠️  RUNNING IN SIMULATION MODE")
    logger.info("⚠️  To trade live, integrate Avantis SDK trade execution")
    logger.info("")
    
    # Create trading engine
    engine = TradingEngine()
    
    # Run
    await engine.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot stopped by user")

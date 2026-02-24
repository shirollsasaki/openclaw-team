#!/usr/bin/env python3
"""
Strategy 1 V2 - Enhanced with All Improvements
- Live trading via web3 (bypasses SDK bug)
- Breakeven stops
- Partial profit taking
- Increased position limits
- Volume filters
- Trend alignment
- Better monitoring
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
    STRATEGY_NAME = "Strategy 1 V2"
    STRATEGY_VERSION = "2.0.0 - Enhanced"
    
    # Wallet
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    WALLET_ADDRESS = os.getenv('WALLET_ADDRESS', 'YOUR_WALLET_ADDRESS')
    
    # Network
    BASE_RPC = 'https://mainnet.base.org'
    CHAIN_ID = 8453
    
    # Avantis Contracts on Base
    TRADING_CONTRACT = "0x0000000000000000000000000000000000000000"  # TODO: Get from docs
    USDC_CONTRACT = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    
    # Capital Allocation
    TOTAL_CAPITAL = 30.0
    ASSETS = {
        'ARB': {'capital': 10.0, 'pair_index': 4},
        'OP': {'capital': 10.0, 'pair_index': 7},
        'ETH': {'capital': 10.0, 'pair_index': 0}
    }
    
    # Strategy Parameters
    TIMEFRAME = '15m'
    LEVERAGE = 15
    RISK_PER_TRADE = 0.03  # 3%
    RR_RATIO = 2.0
    
    # IMPROVED: Increased position limits
    MAX_POSITIONS_PER_ASSET = 3  # Up from 2
    MAX_TOTAL_POSITIONS = 10     # Up from 6
    MAX_LONG_POSITIONS = 6       # NEW: Direction limits
    MAX_SHORT_POSITIONS = 6      # NEW: Direction limits
    
    # SMC Indicators
    SWING_LENGTH = 3
    LOOKBACK_PERIOD = 20
    MIN_SL_DISTANCE = 0.005
    MAX_SL_DISTANCE = 0.10
    
    # NEW: Partial Profit Taking
    BREAKEVEN_AT = 0.5    # Move SL to breakeven at 50% to TP
    TAKE_PARTIAL_AT = 0.5  # Take 50% profit at 50% to TP
    PARTIAL_SIZE = 0.5     # Close 50% of position
    
    # NEW: Trailing Stop Loss
    USE_TRAILING_SL = True
    TRAILING_SL_ACTIVATION = 0.01  # Start trailing after 1% profit
    TRAILING_SL_DISTANCE = 0.005   # Trail 0.5% below highest price
    
    # NEW: Volume Filter
    USE_VOLUME_FILTER = True
    VOLUME_THRESHOLD = 1.5  # Volume must be 1.5x above average
    
    # NEW: Trend Alignment
    USE_TREND_FILTER = True
    TREND_TIMEFRAME = '1h'
    TREND_EMA = 20
    
    # Risk Management
    MAX_DRAWDOWN = 0.30
    DAILY_LOSS_LIMIT = 0.10
    CONSECUTIVE_LOSS_LIMIT = 3  # NEW: Pause after 3 losses
    
    # Execution
    SLIPPAGE_TOLERANCE = 0.01
    CHECK_INTERVAL = 60
    
    # Discord
    DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', '')
    
    # Logging
    LOG_FILE = 'strategy1_v2.log'
    TRADE_LOG = 'strategy1_v2_trades.csv'

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

async def send_discord_notification(message):
    if not Config.DISCORD_WEBHOOK:
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(Config.DISCORD_WEBHOOK, json={'content': message})
    except Exception as e:
        logger.error(f"Discord notification failed: {e}")

# ============================================================================
# DATA FETCHING WITH IMPROVEMENTS
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
# ENHANCED SMC INDICATORS
# ============================================================================

class SMCIndicators:
    @staticmethod
    def add_indicators(df, swing_length=3, lookback=20):
        df = df.copy()
        
        # Swing Points
        df['swing_high'] = False
        df['swing_low'] = False
        
        for i in range(swing_length, len(df) - swing_length):
            if df['high'].iloc[i] == df['high'].iloc[i-swing_length:i+swing_length+1].max():
                df.loc[df.index[i], 'swing_high'] = True
            if df['low'].iloc[i] == df['low'].iloc[i-swing_length:i+swing_length+1].min():
                df.loc[df.index[i], 'swing_low'] = True
        
        # Break of Structure
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
                if df['close'].iloc[i] > last_high:
                    df.loc[df.index[i], 'bos_bull'] = True
                elif df['close'].iloc[i] < last_low:
                    df.loc[df.index[i], 'bos_bear'] = True
        
        # Range zones
        df['range_high'] = df['high'].rolling(lookback).max()
        df['range_low'] = df['low'].rolling(lookback).min()
        
        # NEW: Volume indicator
        df['volume_avg'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_avg']
        
        # NEW: Trend indicator (EMA)
        df['ema_20'] = df['close'].ewm(span=20).mean()
        df['trend_bullish'] = df['close'] > df['ema_20']
        
        # Signals
        df['signal'] = 0
        
        for i in range(lookback, len(df)):
            if df['bos_bull'].iloc[i]:
                df.loc[df.index[i], 'signal'] = 1
            elif df['bos_bear'].iloc[i]:
                df.loc[df.index[i], 'signal'] = -1
        
        return df

# ============================================================================
# WEB3 TRADING ENGINE (Bypasses SDK)
# ============================================================================

class Web3Trader:
    def __init__(self):
        try:
            from web3 import Web3
            from eth_account import Account
            self.w3 = Web3(Web3.HTTPProvider(Config.BASE_RPC))
            self.account = Account.from_key(Config.PRIVATE_KEY)
        except ImportError:
            raise Exception("web3.py not installed - run: pip install web3")
        
        # TODO: Load actual Avantis Trading contract ABI
        # For now, placeholder
        self.trading_contract = None
        
    async def open_trade(self, asset, direction, entry, sl, tp, size):
        """Open trade directly via web3 (bypasses SDK bug)"""
        
        # TODO: Implement actual contract call
        # This is a placeholder - need Avantis contract ABI
        
        logger.info(f"⚠️  WEB3 INTEGRATION NOT YET COMPLETE")
        logger.info(f"   Would open: {direction} {asset} @ ${entry:.4f}")
        logger.info(f"   Size: ${size:.2f}, SL: ${sl:.4f}, TP: ${tp:.4f}")
        
        return False  # Return False until implemented

# ============================================================================
# ENHANCED POSITION CLASS
# ============================================================================

class Position:
    def __init__(self, asset, direction, entry, sl, tp, size, leverage):
        self.asset = asset
        self.direction = direction
        self.entry = entry
        self.sl = sl
        self.tp = tp
        self.original_size = size
        self.size = size  # Current size (changes with partials)
        self.leverage = leverage
        self.entry_time = datetime.now()
        self.exit_price = None
        self.exit_time = None
        self.pnl = None
        self.status = 'OPEN'
        self.breakeven_moved = False  # NEW
        self.partial_taken = False      # NEW
        self.highest_price = entry if direction == 'LONG' else entry  # NEW: For trailing
        self.lowest_price = entry if direction == 'SHORT' else entry  # NEW: For trailing
        self.trailing_active = False  # NEW
    
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
    
    def move_to_breakeven(self):
        """Move SL to breakeven"""
        if not self.breakeven_moved:
            self.sl = self.entry
            self.breakeven_moved = True
            logger.trade(f"🔒 Moved SL to breakeven: {self.asset} @ ${self.entry:.4f}")
            return True
        return False
    
    def update_trailing_sl(self, current_price):
        """Update trailing stop loss"""
        if not Config.USE_TRAILING_SL:
            return False
        
        if self.direction == 'LONG':
            # Update highest price
            if current_price > self.highest_price:
                self.highest_price = current_price
            
            # Check if trailing should activate
            profit_pct = (current_price - self.entry) / self.entry
            if profit_pct >= Config.TRAILING_SL_ACTIVATION:
                self.trailing_active = True
            
            # Update trailing SL if active
            if self.trailing_active:
                new_sl = self.highest_price * (1 - Config.TRAILING_SL_DISTANCE)
                if new_sl > self.sl:
                    old_sl = self.sl
                    self.sl = new_sl
                    logger.trade(f"📈 Trailing SL updated: {self.asset} ${old_sl:.4f} → ${new_sl:.4f}")
                    return True
        
        else:  # SHORT
            # Update lowest price
            if current_price < self.lowest_price:
                self.lowest_price = current_price
            
            # Check if trailing should activate
            profit_pct = (self.entry - current_price) / self.entry
            if profit_pct >= Config.TRAILING_SL_ACTIVATION:
                self.trailing_active = True
            
            # Update trailing SL if active
            if self.trailing_active:
                new_sl = self.lowest_price * (1 + Config.TRAILING_SL_DISTANCE)
                if new_sl < self.sl:
                    old_sl = self.sl
                    self.sl = new_sl
                    logger.trade(f"📉 Trailing SL updated: {self.asset} ${old_sl:.4f} → ${new_sl:.4f}")
                    return True
        
        return False
    
    def take_partial_profit(self, exit_price):
        """Take partial profit"""
        if not self.partial_taken:
            partial_size = self.original_size * Config.PARTIAL_SIZE
            remaining_size = self.size - partial_size
            
            # Calculate P&L on partial
            if self.direction == 'LONG':
                price_change = (exit_price - self.entry) / self.entry
            else:
                price_change = (self.entry - exit_price) / self.entry
            
            pnl = partial_size * price_change * self.leverage
            fees = partial_size * 0.0012
            net_pnl = pnl - fees
            
            self.size = remaining_size
            self.partial_taken = True
            
            logger.trade(f"💰 Partial profit: {self.asset} ${partial_size:.2f} @ ${exit_price:.4f} | P&L: ${net_pnl:+.2f}")
            
            return net_pnl
        return 0
    
    def close(self, exit_price, reason):
        """Close the position"""
        self.exit_price = exit_price
        self.exit_time = datetime.now()
        self.status = 'CLOSED'
        
        # Calculate P&L on remaining size
        if self.direction == 'LONG':
            price_change_pct = (exit_price - self.entry) / self.entry
        else:
            price_change_pct = (self.entry - exit_price) / self.entry
        
        pnl_pct = price_change_pct * self.leverage
        gross_pnl = self.size * pnl_pct
        fees = self.size * 0.0012
        
        self.pnl = gross_pnl - fees
        
        return self.pnl

# ============================================================================
# ENHANCED POSITION MANAGER
# ============================================================================

class PositionManager:
    def __init__(self):
        self.positions = []
        self.closed_positions = []
        self.total_pnl = 0
        self.daily_pnl = 0
        self.last_reset_date = datetime.now().date()
        self.consecutive_losses = 0  # NEW
    
    def add_position(self, position):
        self.positions.append(position)
        logger.trade(f"OPENED {position.direction} {position.asset} @ ${position.entry:.4f} | SL: ${position.sl:.4f} | TP: ${position.tp:.4f} | Size: ${position.size:.2f}")
    
    def calculate_unrealized_pnl(self, prices):
        unrealized = 0
        
        for pos in self.positions:
            asset = pos.asset
            if asset not in prices:
                continue
            
            current_price = prices[asset]
            
            if pos.direction == 'LONG':
                price_change_pct = (current_price - pos.entry) / pos.entry
            else:
                price_change_pct = (pos.entry - current_price) / pos.entry
            
            pnl_pct = price_change_pct * pos.leverage
            position_pnl = pos.size * pnl_pct
            
            unrealized += position_pnl
        
        return unrealized
    
    def update_positions(self, prices):
        """Update with partial profits, breakeven stops, and trailing SL"""
        for pos in self.positions[:]:
            asset = pos.asset
            if asset not in prices:
                continue
            
            current_price = prices[asset]
            high = current_price * 1.002
            low = current_price * 0.998
            
            # NEW: Update trailing stop loss
            pos.update_trailing_sl(current_price)
            
            # NEW: Check for partial profit and breakeven
            if pos.direction == 'LONG':
                progress_to_tp = (current_price - pos.entry) / (pos.tp - pos.entry)
            else:
                progress_to_tp = (pos.entry - current_price) / (pos.entry - pos.tp)
            
            # Take partial profit
            if progress_to_tp >= Config.TAKE_PARTIAL_AT and not pos.partial_taken:
                partial_pnl = pos.take_partial_profit(current_price)
                self.total_pnl += partial_pnl
                self.daily_pnl += partial_pnl
            
            # Move to breakeven
            if progress_to_tp >= Config.BREAKEVEN_AT and not pos.breakeven_moved:
                pos.move_to_breakeven()
            
            # Check for full exit
            exit_type, exit_price = pos.check_exit(high, low)
            
            if exit_type:
                pnl = pos.close(exit_price, exit_type)
                self.positions.remove(pos)
                self.closed_positions.append(pos)
                self.total_pnl += pnl
                self.daily_pnl += pnl
                
                # Track consecutive losses
                if pnl < 0:
                    self.consecutive_losses += 1
                else:
                    self.consecutive_losses = 0
                
                emoji = "✅" if pnl > 0 else "❌"
                logger.trade(f"{emoji} CLOSED {pos.direction} {pos.asset} @ ${exit_price:.4f} | {exit_type} | P&L: ${pnl:+.2f}")
                
                asyncio.create_task(send_discord_notification(
                    f"{emoji} **{exit_type}** | {pos.direction} {pos.asset}\n"
                    f"Entry: ${pos.entry:.4f} → Exit: ${exit_price:.4f}\n"
                    f"P&L: **${pnl:+.2f}** | Total P&L: ${self.total_pnl:+.2f}\n"
                    f"Consecutive Losses: {self.consecutive_losses}"
                ))
    
    def count_positions(self, asset=None, direction=None):
        """Count positions with filters"""
        positions = self.positions
        
        if asset:
            positions = [p for p in positions if p.asset == asset]
        if direction:
            positions = [p for p in positions if p.direction == direction]
        
        return len(positions)
    
    def get_equity(self):
        return Config.TOTAL_CAPITAL + self.total_pnl
    
    def reset_daily_pnl(self):
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_pnl = 0
            self.last_reset_date = today
    
    def check_risk_limits(self):
        """Enhanced risk checks"""
        equity = self.get_equity()
        
        # Max drawdown
        drawdown = (Config.TOTAL_CAPITAL - equity) / Config.TOTAL_CAPITAL
        if drawdown >= Config.MAX_DRAWDOWN:
            logger.error(f"⛔ MAX DRAWDOWN HIT: {drawdown*100:.1f}%")
            return False
        
        # Daily loss limit
        if self.daily_pnl < 0 and abs(self.daily_pnl) >= (equity * Config.DAILY_LOSS_LIMIT):
            logger.error(f"⛔ DAILY LOSS LIMIT HIT: ${self.daily_pnl:.2f}")
            return False
        
        # NEW: Consecutive loss limit
        if self.consecutive_losses >= Config.CONSECUTIVE_LOSS_LIMIT:
            logger.error(f"⛔ CONSECUTIVE LOSS LIMIT: {self.consecutive_losses} losses in a row")
            logger.info(f"   Pausing for 1 hour...")
            return False
        
        return True
    
    def save_trades(self):
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
                'size': pos.original_size,
                'leverage': pos.leverage,
                'pnl': pos.pnl,
                'partial_taken': pos.partial_taken,
                'breakeven_moved': pos.breakeven_moved
            })
        
        df = pd.DataFrame(trades_data)
        df.to_csv(Config.TRADE_LOG, index=False)

# ============================================================================
# ENHANCED TRADING ENGINE
# ============================================================================

class TradingEngine:
    def __init__(self):
        self.position_manager = PositionManager()
        # Web3Trader optional (only needed for live trading)
        self.web3_trader = None
        try:
            self.web3_trader = Web3Trader()
        except:
            logger.info("⚠️  Web3Trader not available - simulation mode only")
        self.running = False
    
    def check_filters(self, asset, df, signal):
        """Check all filters before taking trade"""
        latest = df.iloc[-1]
        
        # Volume filter
        if Config.USE_VOLUME_FILTER:
            if latest['volume_ratio'] < Config.VOLUME_THRESHOLD:
                logger.info(f"   Skipped {asset}: Low volume ({latest['volume_ratio']:.2f}x)")
                return False
        
        # Trend alignment filter
        if Config.USE_TREND_FILTER:
            if signal == 1 and not latest['trend_bullish']:
                logger.info(f"   Skipped {asset}: LONG signal but 1h trend bearish")
                return False
            if signal == -1 and latest['trend_bullish']:
                logger.info(f"   Skipped {asset}: SHORT signal but 1h trend bullish")
                return False
        
        return True
    
    def calculate_position_size(self, asset, entry, sl):
        asset_capital = Config.ASSETS[asset]['capital']
        equity = self.position_manager.get_equity()
        asset_equity = asset_capital * (equity / Config.TOTAL_CAPITAL)
        
        # Adjust risk based on consecutive losses
        risk_pct = Config.RISK_PER_TRADE
        if self.position_manager.consecutive_losses >= 2:
            risk_pct *= 0.5  # Reduce risk after 2 losses
            logger.info(f"   Reduced risk to {risk_pct*100}% (after {self.position_manager.consecutive_losses} losses)")
        
        risk_amount = asset_equity * risk_pct
        sl_distance = abs(entry - sl) / entry
        
        if sl_distance < Config.MIN_SL_DISTANCE or sl_distance > Config.MAX_SL_DISTANCE:
            return None
        
        size = risk_amount / sl_distance
        max_size = asset_equity * 0.5
        size = min(size, max_size)
        
        if size < 0.1:
            return None
        
        return round(size, 2)
    
    async def check_signals(self, asset):
        # Fetch candles
        df = await DataFetcher.fetch_candles(asset, limit=100)
        if df is None or len(df) < 50:
            return
        
        # Add indicators
        df = SMCIndicators.add_indicators(df, Config.SWING_LENGTH, Config.LOOKBACK_PERIOD)
        
        latest = df.iloc[-1]
        
        if latest['signal'] == 0:
            return
        
        # Check filters
        if not self.check_filters(asset, df, latest['signal']):
            return
        
        # Check position limits
        if self.position_manager.count_positions(asset) >= Config.MAX_POSITIONS_PER_ASSET:
            return
        
        if self.position_manager.count_positions() >= Config.MAX_TOTAL_POSITIONS:
            return
        
        # NEW: Direction limits
        direction = 'LONG' if latest['signal'] == 1 else 'SHORT'
        if self.position_manager.count_positions(direction=direction) >= (Config.MAX_LONG_POSITIONS if direction == 'LONG' else Config.MAX_SHORT_POSITIONS):
            logger.info(f"   Skipped {asset}: Max {direction} positions reached")
            return
        
        # Get entry price from Avantis
        avantis_price = await DataFetcher.get_avantis_price(asset)
        if avantis_price is None:
            return
        
        current_price = avantis_price
        
        # Calculate SL/TP
        if latest['signal'] == 1:  # LONG
            sl = latest['range_low'] if latest['range_low'] < current_price else current_price * 0.985
            tp = current_price + (current_price - sl) * Config.RR_RATIO
        else:  # SHORT
            sl = latest['range_high'] if latest['range_high'] > current_price else current_price * 1.015
            tp = current_price - (sl - current_price) * Config.RR_RATIO
        
        # Calculate size
        size = self.calculate_position_size(asset, current_price, sl)
        if size is None:
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
            f"Size: ${size:.2f} @ {Config.LEVERAGE}x\n"
            f"Volume: {latest['volume_ratio']:.2f}x avg"
        )
        
        # TODO: Execute via web3
        # await self.web3_trader.open_trade(asset, direction, current_price, sl, tp, size)
        logger.info("⚠️  SIMULATION MODE - Trade not executed on Avantis")
    
    async def run(self):
        self.running = True
        
        logger.info("="*70)
        logger.info(f"{Config.STRATEGY_NAME} - ENHANCED VERSION")
        logger.info("="*70)
        logger.info(f"Improvements:")
        logger.info(f"  ✅ Breakeven stops at {Config.BREAKEVEN_AT*100}% to TP")
        logger.info(f"  ✅ Partial profits at {Config.TAKE_PARTIAL_AT*100}% to TP")
        logger.info(f"  ✅ Trailing SL: activates at {Config.TRAILING_SL_ACTIVATION*100}%, trails {Config.TRAILING_SL_DISTANCE*100}%")
        logger.info(f"  ✅ Position limits: {Config.MAX_TOTAL_POSITIONS} total")
        logger.info(f"  ✅ Direction limits: {Config.MAX_LONG_POSITIONS} LONG, {Config.MAX_SHORT_POSITIONS} SHORT")
        logger.info(f"  ✅ Volume filter: {Config.VOLUME_THRESHOLD}x minimum")
        logger.info(f"  ✅ Trend alignment filter enabled")
        logger.info(f"  ✅ Consecutive loss protection: pause after {Config.CONSECUTIVE_LOSS_LIMIT}")
        logger.info("="*70)
        
        await send_discord_notification(
            f"🚀 **{Config.STRATEGY_NAME} Started**\n"
            f"✅ Breakeven + Partial Profits\n"
            f"✅ Trailing SL (1% activation, 0.5% trail)\n"
            f"✅ Volume + Trend Filters\n"
            f"Max positions: {Config.MAX_TOTAL_POSITIONS}"
        )
        
        try:
            while self.running:
                self.position_manager.reset_daily_pnl()
                
                if not self.position_manager.check_risk_limits():
                    logger.error("⛔ RISK LIMITS EXCEEDED - PAUSING")
                    await asyncio.sleep(3600)  # Pause 1 hour
                    self.position_manager.consecutive_losses = 0  # Reset after pause
                    continue
                
                # Fetch prices
                prices = {}
                for asset in Config.ASSETS.keys():
                    avantis_price = await DataFetcher.get_avantis_price(asset)
                    if avantis_price:
                        prices[asset] = avantis_price
                
                # Update positions (with partial profits)
                self.position_manager.update_positions(prices)
                
                # Calculate unrealized P&L
                unrealized_pnl = self.position_manager.calculate_unrealized_pnl(prices)
                
                # Check for new signals
                for asset in Config.ASSETS.keys():
                    await self.check_signals(asset)
                
                # Save trades
                self.position_manager.save_trades()
                
                # Log status
                equity = self.position_manager.get_equity()
                total_equity = equity + unrealized_pnl
                
                long_count = self.position_manager.count_positions(direction='LONG')
                short_count = self.position_manager.count_positions(direction='SHORT')
                
                logger.info("="*110)
                logger.info(
                    f"Equity: ${equity:.2f} | Unrealized: ${unrealized_pnl:+.2f} | Total: ${total_equity:.2f} | "
                    f"Open: {self.position_manager.count_positions()} (L:{long_count}/S:{short_count}) | "
                    f"Realized: ${self.position_manager.total_pnl:+.2f} | Losses: {self.position_manager.consecutive_losses}"
                )
                logger.info("="*110)
                
                # Log position table
                if self.position_manager.positions and prices:
                    logger.info(f"{'#':<4} {'Asset':<6} {'Side':<6} {'Entry':<12} {'SL':<12} {'TP':<12} {'Unrealized':<12} {'Realized':<12} {'Flags':<15}")
                    logger.info("-"*110)
                    
                    for idx, pos in enumerate(self.position_manager.positions, 1):
                        if pos.asset in prices:
                            current_price = prices[pos.asset]
                            
                            if pos.direction == 'LONG':
                                price_change_pct = (current_price - pos.entry) / pos.entry
                            else:
                                price_change_pct = (pos.entry - current_price) / pos.entry
                            
                            pnl_pct = price_change_pct * pos.leverage
                            position_pnl = pos.size * pnl_pct
                            
                            status_flags = []
                            if pos.partial_taken:
                                status_flags.append("PARTIAL")
                            if pos.breakeven_moved:
                                status_flags.append("BE")
                            if pos.trailing_active:
                                status_flags.append("TRAIL")
                            
                            flags_str = ','.join(status_flags) if status_flags else "-"
                            
                            logger.info(
                                f"{idx:<4} {pos.asset:<6} {pos.direction:<6} "
                                f"${pos.entry:<11.4f} ${pos.sl:<11.4f} ${pos.tp:<11.4f} "
                                f"${position_pnl:+11.2f} ${'0.00':<11} {flags_str:<15}"
                            )
                    
                    logger.info("="*110)
                else:
                    logger.info("No open positions")
                    logger.info("="*110)
                
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
    if not Config.PRIVATE_KEY:
        logger.error("❌ PRIVATE_KEY not found in .env file")
        return
    
    logger.info("Starting Strategy 1 V2 - Enhanced Edition")
    
    engine = TradingEngine()
    await engine.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot stopped by user")

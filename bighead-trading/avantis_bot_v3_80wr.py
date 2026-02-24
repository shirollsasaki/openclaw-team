"""
Strategy V3 - 80% Win Rate Target
All 5 improvements from deep analysis:
1. Multi-timeframe (1H trend check)
2. Momentum confirmation (1-2 bar wait)
3. Immediate breakeven (at 1% favorable)
4. Volume spike filter (2.5x minimum)
5. Time-based filter (trading hours)
"""

import asyncio
import logging
from datetime import datetime
from web3 import Web3
import pandas as pd
import numpy as np
from avantis_sdk_wrapper import TraderClient, FeedClient
from position_manager import Position, PositionManager
from squeeze_momentum import SqueezeMomentumIndicator
import os
from dotenv import load_dotenv

load_dotenv()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('strategy_v3_80wr.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Config:
    # Network
    BASE_RPC = "https://mainnet.base.org"
    WALLET_ADDRESS = "YOUR_WALLET_ADDRESS"
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    
    # Capital
    STARTING_CAPITAL = 61.70
    CAPITAL_PER_ASSET = {'ARB': 30, 'OP': 30}
    
    # Leverage (per asset)
    LEVERAGE = {'ARB': 15, 'OP': 10, 'ETH': 15}
    
    # Risk
    RISK_PER_TRADE = 0.03
    MAX_TOTAL_POSITIONS = 10
    MAX_POSITIONS_PER_ASSET = 2
    MAX_LONG_POSITIONS = 6
    MAX_SHORT_POSITIONS = 6
    MIN_POSITION_SIZE = 12
    
    # Strategy
    TIMEFRAME = '15m'
    SWING_LENGTH = 3
    LOOKBACK_PERIOD = 20
    RR_RATIO = 2.0
    
    # V3 FILTERS (IMPROVED)
    USE_VOLUME_FILTER = True
    VOLUME_THRESHOLD = 2.5  # Increased from 1.5 to 2.5
    
    USE_TREND_FILTER = True
    
    USE_SQUEEZE_FILTER = True
    SQUEEZE_BB_LENGTH = 20
    SQUEEZE_BB_MULT = 2.0
    SQUEEZE_KC_LENGTH = 20
    SQUEEZE_KC_MULT = 1.5
    
    USE_MTF_FILTER = True  # NEW: Multi-timeframe
    MTF_TIMEFRAME = '1h'
    
    USE_MOMENTUM_CONFIRMATION = True  # NEW: Wait for confirmation
    
    USE_TIME_FILTER = True  # NEW: Trading hours
    
    # Risk Management
    USE_TRAILING_SL = True
    TRAILING_SL_ACTIVATION = 0.10  # 10% P&L
    TRAILING_SL_DISTANCE = 0.005
    
    USE_BREAKEVEN = True
    BREAKEVEN_TRIGGER = 0.50
    
    USE_PARTIAL_PROFITS = True
    PARTIAL_TRIGGER = 0.50
    PARTIAL_SIZE = 0.50
    
    USE_IMMEDIATE_BREAKEVEN = True  # NEW: Quick BE at 1%
    IMMEDIATE_BE_TRIGGER = 0.01
    
    SIMULATION_MODE = False

class DataFetcher:
    @staticmethod
    async def fetch_candles(asset, limit=100, timeframe='15m'):
        """Fetch candles from Binance"""
        try:
            import ccxt
            exchange = ccxt.binance()
            
            symbol = f"{asset}/USDT"
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
        except Exception as e:
            logger.error(f"Error fetching {asset} candles: {e}")
            return None
    
    @staticmethod
    async def get_avantis_price(asset):
        """Get price from Avantis"""
        try:
            pair_index = {'ARB': 4, 'OP': 7, 'ETH': 0}.get(asset)
            if pair_index is None:
                return None
            
            feed_client = FeedClient()
            price_data = feed_client.get_price(pair_index)
            
            if price_data and 'price' in price_data:
                return float(price_data['price'])
            
            return None
        except Exception as e:
            logger.error(f"Error getting Avantis price for {asset}: {e}")
            return None

class SMCIndicators:
    @staticmethod
    def add_indicators(df, swing_length=3, lookback=20):
        """Add all SMC indicators"""
        df = df.copy()
        
        # Swing Points
        df['swing_high'] = False
        df['swing_low'] = False
        
        for i in range(swing_length, len(df) - swing_length):
            if df['high'].iloc[i] == df['high'].iloc[i-swing_length:i+swing_length+1].max():
                df.loc[df.index[i], 'swing_high'] = True
            if df['low'].iloc[i] == df['low'].iloc[i-swing_length:i+swing_length+1].min():
                df.loc[df.index[i], 'swing_low'] = True
        
        # BOS
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
        
        # Range
        df['range_high'] = df['high'].rolling(lookback).max()
        df['range_low'] = df['low'].rolling(lookback).min()
        
        # Volume
        df['volume_avg'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_avg']
        
        # Trend
        df['ema_20'] = df['close'].ewm(span=20).mean()
        df['ema_50'] = df['close'].ewm(span=50).mean()
        df['trend_bullish'] = df['close'] > df['ema_20']
        
        # Squeeze
        if Config.USE_SQUEEZE_FILTER:
            sqz = SqueezeMomentumIndicator(
                Config.SQUEEZE_BB_LENGTH,
                Config.SQUEEZE_BB_MULT,
                Config.SQUEEZE_KC_LENGTH,
                Config.SQUEEZE_KC_MULT
            )
            df = sqz.calculate(df)
        
        # Signals
        df['signal'] = 0
        for i in range(lookback, len(df)):
            if df['bos_bull'].iloc[i]:
                df.loc[df.index[i], 'signal'] = 1
            elif df['bos_bear'].iloc[i]:
                df.loc[df.index[i], 'signal'] = -1
        
        return df

class TradingBot:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(Config.BASE_RPC))
        self.position_manager = PositionManager()
        self.starting_equity = Config.STARTING_CAPITAL
        
        logger.info("="*70)
        logger.info("Strategy V3 - 80% Win Rate Target")
        logger.info("="*70)
        logger.info("V3 Improvements:")
        logger.info(f"  ✅ Multi-timeframe filter: {Config.MTF_TIMEFRAME}")
        logger.info(f"  ✅ Momentum confirmation: 1-2 bar wait")
        logger.info(f"  ✅ Immediate breakeven: {Config.IMMEDIATE_BE_TRIGGER*100}%")
        logger.info(f"  ✅ Volume spike filter: {Config.VOLUME_THRESHOLD}x")
        logger.info(f"  ✅ Time-based filter: Trading hours only")
        logger.info(f"  ✅ Trailing SL: {Config.TRAILING_SL_ACTIVATION*100}% activation")
        logger.info("="*70)
    
    def is_valid_trading_time(self):
        """NEW: Check if current time is valid for trading"""
        if not Config.USE_TIME_FILTER:
            return True
        
        now_utc = datetime.utcnow()
        hour = now_utc.hour
        
        # Skip low liquidity periods (12 AM - 6 AM UTC)
        if hour >= 0 and hour < 6:
            return False
        
        return True
    
    async def check_mtf_trend(self, asset, signal):
        """NEW: Check multi-timeframe trend alignment"""
        if not Config.USE_MTF_FILTER:
            return True
        
        try:
            # Fetch 1H candles
            df_1h = await DataFetcher.fetch_candles(asset, limit=50, timeframe=Config.MTF_TIMEFRAME)
            
            if df_1h is None or len(df_1h) < 50:
                logger.warning(f"   MTF check failed for {asset}, allowing trade")
                return True
            
            # Add EMAs
            df_1h['ema_20'] = df_1h['close'].ewm(span=20).mean()
            df_1h['ema_50'] = df_1h['close'].ewm(span=50).mean()
            
            latest = df_1h.iloc[-1]
            
            # Check alignment
            if signal == 1:  # LONG
                aligned = latest['close'] > latest['ema_20'] and latest['ema_20'] > latest['ema_50']
                if not aligned:
                    logger.info(f"   ❌ MTF FILTER: {asset} LONG signal but 1H bearish")
                return aligned
            else:  # SHORT
                aligned = latest['close'] < latest['ema_20'] and latest['ema_20'] < latest['ema_50']
                if not aligned:
                    logger.info(f"   ❌ MTF FILTER: {asset} SHORT signal but 1H bullish")
                return aligned
        
        except Exception as e:
            logger.error(f"MTF check error for {asset}: {e}")
            return True  # Allow trade if check fails
    
    async def check_momentum_confirmation(self, asset, signal):
        """NEW: Wait for momentum confirmation"""
        if not Config.USE_MOMENTUM_CONFIRMATION:
            return True
        
        try:
            # Fetch recent candles
            df = await DataFetcher.fetch_candles(asset, limit=5, timeframe=Config.TIMEFRAME)
            
            if df is None or len(df) < 3:
                return False
            
            signal_bar = df.iloc[-2]  # Bar that fired signal
            confirm_bar = df.iloc[-1]  # Current bar (confirmation)
            
            if signal == 1:  # LONG
                # Require green candle with higher close
                confirmed = (confirm_bar['close'] > signal_bar['close'] and 
                           confirm_bar['close'] > confirm_bar['open'])
                if not confirmed:
                    logger.info(f"   ❌ MOMENTUM: {asset} LONG not confirmed (weak follow-through)")
                return confirmed
            else:  # SHORT
                # Require red candle with lower close
                confirmed = (confirm_bar['close'] < signal_bar['close'] and 
                           confirm_bar['close'] < confirm_bar['open'])
                if not confirmed:
                    logger.info(f"   ❌ MOMENTUM: {asset} SHORT not confirmed (weak follow-through)")
                return confirmed
        
        except Exception as e:
            logger.error(f"Momentum confirmation error for {asset}: {e}")
            return False
    
    def check_filters(self, asset, df, signal):
        """Check all filters"""
        latest = df.iloc[-1]
        
        # Squeeze filter
        if Config.USE_SQUEEZE_FILTER:
            if latest['squeeze_on']:
                logger.info(f"   Skipped {asset}: Squeeze ON (consolidation)")
                return False
            
            if signal == 1 and latest['sqz_mom'] <= 0:
                logger.info(f"   Skipped {asset}: LONG but negative momentum")
                return False
            if signal == -1 and latest['sqz_mom'] >= 0:
                logger.info(f"   Skipped {asset}: SHORT but positive momentum")
                return False
        
        # Volume filter (INCREASED to 2.5x)
        if Config.USE_VOLUME_FILTER:
            if latest['volume_ratio'] < Config.VOLUME_THRESHOLD:
                logger.info(f"   Skipped {asset}: Low volume ({latest['volume_ratio']:.2f}x < {Config.VOLUME_THRESHOLD}x)")
                return False
        
        # Trend filter
        if Config.USE_TREND_FILTER:
            if signal == 1 and not latest['trend_bullish']:
                logger.info(f"   Skipped {asset}: LONG but bearish trend")
                return False
            if signal == -1 and latest['trend_bullish']:
                logger.info(f"   Skipped {asset}: SHORT but bullish trend")
                return False
        
        return True
    
    async def check_signals(self, asset):
        """Check for trading signals"""
        # Time filter
        if not self.is_valid_trading_time():
            return
        
        # Fetch candles
        df = await DataFetcher.fetch_candles(asset, limit=100, timeframe=Config.TIMEFRAME)
        if df is None or len(df) < 50:
            return
        
        # Add indicators
        df = SMCIndicators.add_indicators(df, Config.SWING_LENGTH, Config.LOOKBACK_PERIOD)
        
        latest = df.iloc[-1]
        
        if latest['signal'] == 0:
            return
        
        signal = latest['signal']
        
        # Check basic filters
        if not self.check_filters(asset, df, signal):
            return
        
        # NEW: Multi-timeframe filter
        if not await self.check_mtf_trend(asset, signal):
            return
        
        # NEW: Momentum confirmation
        if not await self.check_momentum_confirmation(asset, signal):
            return
        
        # Check position limits
        if self.position_manager.count_positions(asset) >= Config.MAX_POSITIONS_PER_ASSET:
            return
        
        if self.position_manager.count_positions() >= Config.MAX_TOTAL_POSITIONS:
            return
        
        direction = 'LONG' if signal == 1 else 'SHORT'
        if self.position_manager.count_positions(direction=direction) >= (Config.MAX_LONG_POSITIONS if direction == 'LONG' else Config.MAX_SHORT_POSITIONS):
            logger.info(f"   Skipped {asset}: Max {direction} positions reached")
            return
        
        # Get price
        current_price = await DataFetcher.get_avantis_price(asset)
        if current_price is None:
            return
        
        # Calculate SL/TP
        if signal == 1:
            sl = latest['range_low'] if latest['range_low'] < current_price else current_price * 0.985
            tp = current_price + (current_price - sl) * Config.RR_RATIO
        else:
            sl = latest['range_high'] if latest['range_high'] > current_price else current_price * 1.015
            tp = current_price - (sl - current_price) * Config.RR_RATIO
        
        # Calculate size
        capital = Config.CAPITAL_PER_ASSET.get(asset, 30)
        size = capital
        
        if size < Config.MIN_POSITION_SIZE:
            logger.info(f"   Skipped {asset}: Position too small (${size} < ${Config.MIN_POSITION_SIZE})")
            return
        
        # Create position
        position = Position(
            asset=asset,
            direction=direction,
            entry=current_price,
            sl=sl,
            tp=tp,
            size=size,
            leverage=Config.LEVERAGE[asset]
        )
        
        # Add to manager
        self.position_manager.add_position(position)
        
        logger.info(f"✅ SIGNAL: {direction} {asset} @ ${current_price:.4f}")
        logger.info(f"   SL: ${sl:.4f} | TP: ${tp:.4f} | Size: ${size}")
        logger.info(f"   Volume: {latest['volume_ratio']:.2f}x | MTF: ✅ | Momentum: ✅")
    
    async def update_immediate_breakeven(self, position):
        """NEW: Move SL to breakeven after 1% favorable move"""
        if not Config.USE_IMMEDIATE_BREAKEVEN:
            return
        
        if position.breakeven_moved:
            return
        
        current_price = await DataFetcher.get_avantis_price(position.asset)
        if current_price is None:
            return
        
        # Calculate favorable move
        if position.direction == 'LONG':
            favorable_pct = (current_price - position.entry) / position.entry
        else:
            favorable_pct = (position.entry - current_price) / position.entry
        
        # If 1% favorable and SL not at breakeven
        if favorable_pct >= Config.IMMEDIATE_BE_TRIGGER and position.sl != position.entry:
            position.sl = position.entry
            position.breakeven_moved = True
            
            logger.info(f"🔒 Immediate BE: {position.asset} SL → ${position.entry:.4f} (1% favorable)")
    
    async def update_positions(self):
        """Update all positions"""
        for position in list(self.position_manager.positions):
            current_price = await DataFetcher.get_avantis_price(position.asset)
            if current_price is None:
                continue
            
            # Check immediate breakeven
            await self.update_immediate_breakeven(position)
            
            # Check SL/TP
            if position.direction == 'LONG':
                if current_price <= position.sl:
                    pnl = position.calculate_pnl(current_price)
                    logger.info(f"❌ CLOSED {position.direction} {position.asset} @ ${current_price:.4f} | SL | P&L: ${pnl:.2f}")
                    self.position_manager.remove_position(position)
                elif current_price >= position.tp:
                    pnl = position.calculate_pnl(current_price)
                    logger.info(f"✅ CLOSED {position.direction} {position.asset} @ ${current_price:.4f} | TP | P&L: ${pnl:.2f}")
                    self.position_manager.remove_position(position)
            else:
                if current_price >= position.sl:
                    pnl = position.calculate_pnl(current_price)
                    logger.info(f"❌ CLOSED {position.direction} {position.asset} @ ${current_price:.4f} | SL | P&L: ${pnl:.2f}")
                    self.position_manager.remove_position(position)
                elif current_price <= position.tp:
                    pnl = position.calculate_pnl(current_price)
                    logger.info(f"✅ CLOSED {position.direction} {position.asset} @ ${current_price:.4f} | TP | P&L: ${pnl:.2f}")
                    self.position_manager.remove_position(position)
    
    async def run(self):
        """Main loop"""
        logger.info("🚀 Bot started!")
        
        while True:
            try:
                # Check signals
                for asset in ['ARB', 'OP']:
                    await self.check_signals(asset)
                
                # Update positions
                await self.update_positions()
                
                # Log status
                equity = self.starting_equity + self.position_manager.get_total_realized_pnl()
                unrealized = self.position_manager.get_total_unrealized_pnl(
                    {'ARB': await DataFetcher.get_avantis_price('ARB'),
                     'OP': await DataFetcher.get_avantis_price('OP')}
                )
                
                logger.info(f"Equity: ${equity:.2f} | Unrealized: ${unrealized:+.2f} | Positions: {self.position_manager.count_positions()}")
                
                await asyncio.sleep(60)
            
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)

if __name__ == "__main__":
    bot = TradingBot()
    asyncio.run(bot.run())

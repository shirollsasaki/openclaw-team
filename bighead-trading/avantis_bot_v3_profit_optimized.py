"""
Strategy V3 - PROFIT OPTIMIZED
Focus: Maximum $ returns, not win rate
Based on: SOL/15m (best backtest) + improvements
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
        logging.FileHandler('strategy_v3_profit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Config:
    # Network
    BASE_RPC = "https://mainnet.base.org"
    WALLET_ADDRESS = "YOUR_WALLET_ADDRESS"
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    
    # V3 PROFIT OPTIMIZATION
    # Primary: SOL (best performer in backtest)
    # Secondary: ARB (current live, proven)
    # Disabled: OP (low performance), BTC/ETH (unprofitable)
    
    STARTING_CAPITAL = 61.70
    CAPITAL_ALLOCATION = {
        'SOL': 40,   # 65% on best performer
        'ARB': 20    # 35% on proven secondary
    }
    
    LEVERAGE = {'SOL': 15, 'ARB': 15, 'OP': 10}
    
    # Risk
    RISK_PER_TRADE = 0.03
    MAX_TOTAL_POSITIONS = 6
    MAX_POSITIONS_PER_ASSET = 2
    MAX_LONG_POSITIONS = 4
    MAX_SHORT_POSITIONS = 4
    MIN_POSITION_SIZE = 12
    
    # Strategy
    TIMEFRAME = '15m'  # Best performing timeframe
    SWING_LENGTH = 3
    LOOKBACK_PERIOD = 20
    
    # PROFIT OPTIMIZED RR
    # Backtest showed: Higher TP = better avg profit
    RR_RATIO = 2.5  # Increased from 2.0 for bigger wins
    
    # V3 FILTERS (Profit Focused)
    USE_VOLUME_FILTER = True
    VOLUME_THRESHOLD = 2.0  # Sweet spot (not too strict)
    
    USE_TREND_FILTER = True
    
    USE_SQUEEZE_FILTER = True
    SQUEEZE_BB_LENGTH = 20
    SQUEEZE_BB_MULT = 2.0
    SQUEEZE_KC_LENGTH = 20
    SQUEEZE_KC_MULT = 1.5
    
    USE_MTF_FILTER = True  # NEW
    MTF_TIMEFRAME = '1h'
    
    USE_MOMENTUM_CONFIRMATION = True  # NEW
    CONFIRMATION_BARS = 2  # Wait 2 bars for stronger confirmation
    
    USE_TIME_FILTER = True  # NEW
    
    # Profit Protection (Optimized)
    USE_TRAILING_SL = True
    TRAILING_SL_ACTIVATION = 0.08  # 8% P&L (easier to hit than 10%)
    TRAILING_SL_DISTANCE = 0.005
    
    USE_BREAKEVEN = True
    BREAKEVEN_TRIGGER = 0.40  # Move BE at 40% to TP (earlier)
    
    USE_PARTIAL_PROFITS = True
    PARTIAL_TRIGGER = 0.50
    PARTIAL_SIZE = 0.50
    
    USE_IMMEDIATE_BREAKEVEN = True  # NEW
    IMMEDIATE_BE_TRIGGER = 0.01  # 1% favorable
    
    # NEW: Profit Scaling
    USE_PROFIT_SCALING = True  # Add to winners
    SCALING_TRIGGER = 0.15  # Add at 15% P&L
    SCALING_SIZE = 0.30  # Add 30% more capital
    
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
            pair_index = {'ARB': 4, 'OP': 7, 'ETH': 0, 'SOL': 9}.get(asset)
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
        logger.info("Strategy V3 - PROFIT OPTIMIZED")
        logger.info("="*70)
        logger.info("Focus: Maximum $ returns (not win rate)")
        logger.info(f"Primary asset: SOL (${Config.CAPITAL_ALLOCATION['SOL']})")
        logger.info(f"Secondary asset: ARB (${Config.CAPITAL_ALLOCATION['ARB']})")
        logger.info(f"RR Ratio: {Config.RR_RATIO}:1 (optimized for bigger wins)")
        logger.info("")
        logger.info("V3 Improvements:")
        logger.info(f"  ✅ Multi-timeframe: {Config.MTF_TIMEFRAME} trend check")
        logger.info(f"  ✅ Momentum confirmation: {Config.CONFIRMATION_BARS} bars")
        logger.info(f"  ✅ Immediate BE: {Config.IMMEDIATE_BE_TRIGGER*100}%")
        logger.info(f"  ✅ Volume filter: {Config.VOLUME_THRESHOLD}x")
        logger.info(f"  ✅ Trailing SL: {Config.TRAILING_SL_ACTIVATION*100}% activation")
        logger.info(f"  ✅ Profit scaling: Add {Config.SCALING_SIZE*100}% at {Config.SCALING_TRIGGER*100}% P&L")
        logger.info(f"  ✅ Time-based filter: Trading hours only")
        logger.info("="*70)
    
    def is_valid_trading_time(self):
        """Check if current time is valid for trading"""
        if not Config.USE_TIME_FILTER:
            return True
        
        now_utc = datetime.utcnow()
        hour = now_utc.hour
        
        # Skip low liquidity periods (12 AM - 6 AM UTC)
        if hour >= 0 and hour < 6:
            return False
        
        return True
    
    async def check_mtf_trend(self, asset, signal):
        """Check multi-timeframe trend alignment"""
        if not Config.USE_MTF_FILTER:
            return True
        
        try:
            df_1h = await DataFetcher.fetch_candles(asset, limit=50, timeframe=Config.MTF_TIMEFRAME)
            
            if df_1h is None or len(df_1h) < 50:
                logger.warning(f"   MTF check failed for {asset}, allowing trade")
                return True
            
            df_1h['ema_20'] = df_1h['close'].ewm(span=20).mean()
            df_1h['ema_50'] = df_1h['close'].ewm(span=50).mean()
            
            latest = df_1h.iloc[-1]
            
            if signal == 1:
                aligned = latest['close'] > latest['ema_20'] and latest['ema_20'] > latest['ema_50']
                if not aligned:
                    logger.info(f"   ❌ MTF: {asset} LONG signal but 1H bearish")
                return aligned
            else:
                aligned = latest['close'] < latest['ema_20'] and latest['ema_20'] < latest['ema_50']
                if not aligned:
                    logger.info(f"   ❌ MTF: {asset} SHORT signal but 1H bullish")
                return aligned
        
        except Exception as e:
            logger.error(f"MTF check error for {asset}: {e}")
            return True
    
    async def check_momentum_confirmation(self, asset, signal):
        """Wait for strong momentum confirmation"""
        if not Config.USE_MOMENTUM_CONFIRMATION:
            return True
        
        try:
            df = await DataFetcher.fetch_candles(asset, limit=5, timeframe=Config.TIMEFRAME)
            
            if df is None or len(df) < Config.CONFIRMATION_BARS + 1:
                return False
            
            # Check last N bars for momentum
            signal_bar = df.iloc[-(Config.CONFIRMATION_BARS + 1)]
            confirm_bars = df.iloc[-Config.CONFIRMATION_BARS:]
            
            if signal == 1:  # LONG
                # All confirmation bars should be bullish
                all_green = all(confirm_bars['close'] > confirm_bars['open'])
                higher_closes = all(confirm_bars['close'].iloc[i] > confirm_bars['close'].iloc[i-1] 
                                   for i in range(1, len(confirm_bars)))
                
                confirmed = all_green and higher_closes
                if not confirmed:
                    logger.info(f"   ❌ MOMENTUM: {asset} LONG weak ({Config.CONFIRMATION_BARS} bar confirmation failed)")
                return confirmed
            else:  # SHORT
                # All confirmation bars should be bearish
                all_red = all(confirm_bars['close'] < confirm_bars['open'])
                lower_closes = all(confirm_bars['close'].iloc[i] < confirm_bars['close'].iloc[i-1] 
                                  for i in range(1, len(confirm_bars)))
                
                confirmed = all_red and lower_closes
                if not confirmed:
                    logger.info(f"   ❌ MOMENTUM: {asset} SHORT weak ({Config.CONFIRMATION_BARS} bar confirmation failed)")
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
        
        # Volume filter
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
        # Skip if asset not in allocation
        if asset not in Config.CAPITAL_ALLOCATION:
            return
        
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
        
        # NEW: Strong momentum confirmation
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
        
        # Calculate SL/TP with OPTIMIZED RR
        if signal == 1:
            sl = latest['range_low'] if latest['range_low'] < current_price else current_price * 0.985
            tp = current_price + (current_price - sl) * Config.RR_RATIO
        else:
            sl = latest['range_high'] if latest['range_high'] > current_price else current_price * 1.015
            tp = current_price - (sl - current_price) * Config.RR_RATIO
        
        # Calculate size
        capital = Config.CAPITAL_ALLOCATION.get(asset, 30)
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
        logger.info(f"   SL: ${sl:.4f} | TP: ${tp:.4f} (RR: {Config.RR_RATIO}:1)")
        logger.info(f"   Size: ${size} | Volume: {latest['volume_ratio']:.2f}x")
        logger.info(f"   Filters: MTF ✅ | Momentum ✅ | Squeeze ✅")
    
    async def update_immediate_breakeven(self, position):
        """Move SL to breakeven after 1% favorable move"""
        if not Config.USE_IMMEDIATE_BREAKEVEN:
            return
        
        if position.breakeven_moved:
            return
        
        current_price = await DataFetcher.get_avantis_price(position.asset)
        if current_price is None:
            return
        
        if position.direction == 'LONG':
            favorable_pct = (current_price - position.entry) / position.entry
        else:
            favorable_pct = (position.entry - current_price) / position.entry
        
        if favorable_pct >= Config.IMMEDIATE_BE_TRIGGER and position.sl != position.entry:
            position.sl = position.entry
            position.breakeven_moved = True
            
            logger.info(f"🔒 Immediate BE: {position.asset} SL → ${position.entry:.4f}")
    
    async def update_profit_scaling(self, position):
        """Add to winning positions"""
        if not Config.USE_PROFIT_SCALING:
            return
        
        if hasattr(position, 'scaled') and position.scaled:
            return
        
        current_price = await DataFetcher.get_avantis_price(position.asset)
        if current_price is None:
            return
        
        pnl = position.calculate_pnl(current_price)
        pnl_pct = pnl / position.size
        
        if pnl_pct >= Config.SCALING_TRIGGER:
            # Add more capital to winner
            additional_size = position.size * Config.SCALING_SIZE
            position.size += additional_size
            position.scaled = True
            
            logger.info(f"📈 SCALING: {position.asset} +${additional_size:.2f} (P&L: {pnl_pct*100:.1f}%)")
    
    async def update_positions(self):
        """Update all positions"""
        for position in list(self.position_manager.positions):
            current_price = await DataFetcher.get_avantis_price(position.asset)
            if current_price is None:
                continue
            
            # Check immediate breakeven
            await self.update_immediate_breakeven(position)
            
            # NEW: Check profit scaling
            await self.update_profit_scaling(position)
            
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
        logger.info("🚀 V3 Profit Bot started!")
        logger.info(f"💰 Target: Maximum $ returns")
        logger.info(f"📊 SOL (primary) + ARB (secondary)")
        logger.info("")
        
        while True:
            try:
                # Check signals for allocated assets
                for asset in Config.CAPITAL_ALLOCATION.keys():
                    await self.check_signals(asset)
                
                # Update positions
                await self.update_positions()
                
                # Log status
                equity = self.starting_equity + self.position_manager.get_total_realized_pnl()
                
                prices = {}
                for asset in Config.CAPITAL_ALLOCATION.keys():
                    prices[asset] = await DataFetcher.get_avantis_price(asset)
                
                unrealized = self.position_manager.get_total_unrealized_pnl(prices)
                
                logger.info(f"💰 Equity: ${equity:.2f} | Unrealized: ${unrealized:+.2f} | Positions: {self.position_manager.count_positions()}")
                
                await asyncio.sleep(60)
            
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)

if __name__ == "__main__":
    bot = TradingBot()
    asyncio.run(bot.run())

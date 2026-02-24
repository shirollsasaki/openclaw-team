#!/usr/bin/env python3
"""
Strategy 1 V2 + Squeeze + 1Delta Dynamic Leverage
All V2 improvements + Squeeze filter + 1delta leveraged lending
Safe dynamic leverage based on signal confidence
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
    STRATEGY_NAME = "Strategy 1 V2 + Squeeze + 1Delta"
    STRATEGY_VERSION = "3.0.0 - Dynamic Leverage via 1delta"
    
    # Wallet
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    WALLET_ADDRESS = os.getenv('WALLET_ADDRESS', 'YOUR_WALLET_ADDRESS')
    
    # Trading Mode
    SIMULATION_MODE = True  # ⚠️ SIMULATION - Testing 1delta integration first
    
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
    
    # Position Limits
    MAX_POSITIONS_PER_ASSET = 3
    MAX_TOTAL_POSITIONS = 10
    MAX_LONG_POSITIONS = 6
    MAX_SHORT_POSITIONS = 6
    
    # SMC Indicators
    SWING_LENGTH = 3
    LOOKBACK_PERIOD = 20
    MIN_SL_DISTANCE = 0.005
    MAX_SL_DISTANCE = 0.10
    
    # Partial Profit Taking
    BREAKEVEN_AT = 0.5    # Move SL to breakeven at 50% to TP
    TAKE_PARTIAL_AT = 0.5  # Take 50% profit at 50% to TP
    PARTIAL_SIZE = 0.5     # Close 50% of position
    
    # Trailing Stop Loss
    USE_TRAILING_SL = True
    TRAILING_SL_ACTIVATION = 0.01  # Start trailing after 1% profit
    TRAILING_SL_DISTANCE = 0.005   # Trail 0.5% below highest price
    
    # Filters
    USE_VOLUME_FILTER = True
    VOLUME_THRESHOLD = 1.5
    
    USE_TREND_FILTER = True
    TREND_EMA = 20
    
    # NEW: Squeeze Momentum Filter
    USE_SQUEEZE_FILTER = True
    SQUEEZE_BB_LENGTH = 20
    SQUEEZE_BB_MULT = 2.0
    SQUEEZE_KC_LENGTH = 20
    SQUEEZE_KC_MULT = 1.5
    
    # Risk Management
    MAX_DRAWDOWN = 0.30
    DAILY_LOSS_LIMIT = 0.10
    CONSECUTIVE_LOSS_LIMIT = 3
    
    # Execution
    CHECK_INTERVAL = 60
    
    # Discord
    DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', '')
    
    # Logging
    LOG_FILE = 'strategy1_v2_squeeze_1delta.log'
    TRADE_LOG = 'strategy1_v2_squeeze_1delta_trades.csv'
    
    # ============================================================================
    # 1DELTA DYNAMIC LEVERAGE SETTINGS
    # ============================================================================
    
    # Enable 1delta leveraged lending
    USE_1DELTA_LEVERAGE = True
    
    # 1delta Protocol Settings
    ONEDELTA_PROTOCOL = "aave-v3"  # Default lending protocol on Base
    COLLATERAL_ASSET = "ETH"       # Use ETH as collateral
    BORROW_ASSET = "USDC"          # Borrow USDC for trading
    
    # Signal Scoring Weights
    SCORE_WEIGHTS = {
        'volume': 25,      # Volume above threshold (max 25 points)
        'trend': 20,       # Trend alignment (max 20 points)
        'squeeze': 30,     # Squeeze release strength (max 30 points)
        'momentum': 15,    # Momentum magnitude (max 15 points)
        'market': 10       # Overall market conditions (max 10 points)
    }
    
    # Dynamic Leverage Mapping (signal score → 1delta leverage)
    # Conservative approach ensures max loss < available capital
    LEVERAGE_MAP = {
        90: {'leverage': 3.0, 'position_multiplier': 2.5},    # Very Strong: 3x leverage, 2.5x position
        70: {'leverage': 2.0, 'position_multiplier': 1.67},   # Strong: 2x leverage, 1.67x position
        60: {'leverage': 1.5, 'position_multiplier': 1.25},   # Good: 1.5x leverage, 1.25x position
        0:  {'leverage': 1.0, 'position_multiplier': 1.0}     # Weak: No leverage, normal position
    }
    
    # Health Factor Thresholds
    MIN_HEALTH_FACTOR = 1.5         # Minimum safe health factor
    DELEVERAGE_HEALTH_FACTOR = 1.3  # Auto-deleverage trigger
    EMERGENCY_HEALTH_FACTOR = 1.15  # Emergency close all
    
    # 1delta Risk Limits
    MAX_1DELTA_LEVERAGE = 3.0       # Never exceed 3x leverage
    MAX_BORROW_UTILIZATION = 0.75   # Max 75% of borrowing capacity
    
    # Gas & Fees
    ESTIMATED_1DELTA_GAS = 0.005    # ~$5 in ETH for 1delta operations
    FLASH_LOAN_FEE = 0.0005         # 0.05% flash loan fee

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
# SQUEEZE MOMENTUM INDICATOR
# ============================================================================

class SqueezeMomentumIndicator:
    """Squeeze Momentum Indicator (LazyBear)"""
    
    def __init__(self, bb_length=20, bb_mult=2.0, kc_length=20, kc_mult=1.5):
        self.bb_length = bb_length
        self.bb_mult = bb_mult
        self.kc_length = kc_length
        self.kc_mult = kc_mult
    
    def calculate(self, df):
        """Calculate Squeeze Momentum"""
        df = df.copy()
        
        # Bollinger Bands
        df['bb_basis'] = df['close'].rolling(self.bb_length).mean()
        df['bb_dev'] = self.bb_mult * df['close'].rolling(self.bb_length).std()
        df['bb_upper'] = df['bb_basis'] + df['bb_dev']
        df['bb_lower'] = df['bb_basis'] - df['bb_dev']
        
        # Keltner Channels
        df['kc_ma'] = df['close'].rolling(self.kc_length).mean()
        
        # True Range
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['kc_range'] = df['tr'].rolling(self.kc_length).mean()
        
        df['kc_upper'] = df['kc_ma'] + df['kc_range'] * self.kc_mult
        df['kc_lower'] = df['kc_ma'] - df['kc_range'] * self.kc_mult
        
        # Squeeze Status
        df['sqz_on'] = (df['bb_lower'] > df['kc_lower']) & (df['bb_upper'] < df['kc_upper'])
        df['sqz_off'] = (df['bb_lower'] < df['kc_lower']) & (df['bb_upper'] > df['kc_upper'])
        df['no_sqz'] = ~df['sqz_on'] & ~df['sqz_off']
        
        # Momentum
        highest = df['high'].rolling(self.kc_length).max()
        lowest = df['low'].rolling(self.kc_length).min()
        avg_hl = (highest + lowest) / 2
        sma_close = df['close'].rolling(self.kc_length).mean()
        basis_for_mom = (avg_hl + sma_close) / 2
        
        df['sqz_mom'] = self._linreg(df['close'] - basis_for_mom, self.kc_length)
        
        return df
    
    def _linreg(self, series, length):
        """Linear regression"""
        result = pd.Series(index=series.index, dtype=float)
        
        for i in range(length - 1, len(series)):
            y = series.iloc[i - length + 1:i + 1].values
            x = np.arange(length)
            
            if len(y) == length:
                slope = np.polyfit(x, y, 1)[0]
                result.iloc[i] = slope * (length - 1) + np.mean(y)
        
        return result

# ============================================================================
# SIGNAL SCORING SYSTEM
# ============================================================================

class SignalScorer:
    """
    Score signals from 0-100 based on multiple factors
    Higher score = higher confidence = more leverage
    """
    
    @staticmethod
    def calculate_score(asset, df, signal_direction, latest):
        """Calculate comprehensive signal score"""
        
        if not Config.USE_1DELTA_LEVERAGE:
            return 50  # Default medium score if 1delta disabled
        
        score = 0
        max_score = sum(Config.SCORE_WEIGHTS.values())
        
        # 1. Volume Score (max 25 points)
        volume_ratio = latest.get('volume_ratio', 1.0)
        if volume_ratio >= 3.0:
            volume_score = 25
        elif volume_ratio >= 2.5:
            volume_score = 22
        elif volume_ratio >= 2.0:
            volume_score = 18
        elif volume_ratio >= 1.5:
            volume_score = 12
        else:
            volume_score = 0
        
        score += volume_score
        
        # 2. Trend Score (max 20 points)
        trend_aligned = latest.get('trend_aligned', False)
        if trend_aligned:
            # Check strength of trend
            ema = latest.get('ema_20', latest['close'])
            trend_distance = abs(latest['close'] - ema) / latest['close']
            
            if trend_distance >= 0.03:  # 3%+ from EMA = strong trend
                trend_score = 20
            elif trend_distance >= 0.02:  # 2%+
                trend_score = 16
            elif trend_distance >= 0.01:  # 1%+
                trend_score = 12
            else:
                trend_score = 8
        else:
            trend_score = 0
        
        score += trend_score
        
        # 3. Squeeze Score (max 30 points) - MOST IMPORTANT
        if Config.USE_SQUEEZE_FILTER:
            sqz_off = latest.get('sqz_off', False)
            sqz_mom = latest.get('sqz_mom', 0)
            
            if sqz_off:
                # Squeeze just released - check momentum strength
                mom_abs = abs(sqz_mom)
                
                if mom_abs >= 0.004:  # Very strong momentum
                    squeeze_score = 30
                elif mom_abs >= 0.003:  # Strong
                    squeeze_score = 25
                elif mom_abs >= 0.002:  # Good
                    squeeze_score = 20
                elif mom_abs >= 0.001:  # Medium
                    squeeze_score = 15
                else:  # Weak
                    squeeze_score = 10
            else:
                squeeze_score = 0  # Squeeze not OFF = no points
        else:
            squeeze_score = 15  # Default if squeeze filter disabled
        
        score += squeeze_score
        
        # 4. Momentum Score (max 15 points)
        sqz_mom = abs(latest.get('sqz_mom', 0))
        if sqz_mom >= 0.004:
            momentum_score = 15
        elif sqz_mom >= 0.003:
            momentum_score = 12
        elif sqz_mom >= 0.002:
            momentum_score = 9
        elif sqz_mom >= 0.001:
            momentum_score = 6
        else:
            momentum_score = 3
        
        score += momentum_score
        
        # 5. Market Conditions Score (max 10 points)
        # Check for clean price action (not choppy)
        recent_candles = df.tail(10)
        atr = recent_candles['high'].max() - recent_candles['low'].min()
        avg_range = recent_candles['close'].std()
        
        if atr > 0:
            choppiness = avg_range / atr
            if choppiness < 0.3:  # Clean trending market
                market_score = 10
            elif choppiness < 0.5:  # Decent
                market_score = 7
            elif choppiness < 0.7:  # OK
                market_score = 4
            else:  # Choppy
                market_score = 0
        else:
            market_score = 5
        
        score += market_score
        
        # Normalize to 0-100
        normalized_score = (score / max_score) * 100
        
        logger.info(f"   📊 Signal Score: {normalized_score:.1f}/100")
        logger.info(f"      Volume: {volume_score}/25 | Trend: {trend_score}/20 | Squeeze: {squeeze_score}/30")
        logger.info(f"      Momentum: {momentum_score}/15 | Market: {market_score}/10")
        
        return normalized_score

# ============================================================================
# 1DELTA LEVERAGE MANAGER
# ============================================================================

class OneDeltaManager:
    """
    Manage 1delta leveraged lending positions
    Handles flash loan-based leverage, health factor monitoring, auto-deleverage
    """
    
    def __init__(self):
        self.current_leverage = 1.0
        self.collateral_amount = 0
        self.debt_amount = 0
        self.health_factor = float('inf')
        self.leveraged_capital = Config.TOTAL_CAPITAL
        self.is_leveraged = False
    
    def get_leverage_params(self, signal_score):
        """Get leverage and position sizing based on signal score"""
        
        if not Config.USE_1DELTA_LEVERAGE:
            return {
                'leverage': 1.0,
                'position_multiplier': 1.0,
                'confidence': 'MEDIUM',
                'max_position_size': Config.TOTAL_CAPITAL / 5  # $6 default
            }
        
        # Find appropriate leverage tier
        leverage_config = None
        for score_threshold in sorted(Config.LEVERAGE_MAP.keys(), reverse=True):
            if signal_score >= score_threshold:
                leverage_config = Config.LEVERAGE_MAP[score_threshold]
                break
        
        if not leverage_config:
            leverage_config = Config.LEVERAGE_MAP[0]  # Default to no leverage
        
        leverage = min(leverage_config['leverage'], Config.MAX_1DELTA_LEVERAGE)
        position_mult = leverage_config['position_multiplier']
        
        # Calculate available capital after leverage
        base_capital = Config.TOTAL_CAPITAL
        leveraged_capital = base_capital * leverage
        
        # Calculate safe position size
        # Ensure max loss (2% SL * 15x Avantis) < available capital
        base_position = base_capital / 5  # $6 per asset normally
        max_position = base_position * position_mult
        
        # Verify safety: max_loss < leveraged_capital
        max_loss_per_trade = max_position * 0.02 * Config.LEVERAGE  # 2% SL * 15x
        safety_ratio = leveraged_capital / max_loss_per_trade
        
        if safety_ratio < 1.1:  # Less than 10% buffer
            # Reduce position size to ensure safety
            max_position = (leveraged_capital * 0.9) / (0.02 * Config.LEVERAGE)
            logger.warning(f"   ⚠️  Position size reduced for safety: ${max_position:.2f}")
        
        # Determine confidence level
        if signal_score >= 90:
            confidence = 'VERY_HIGH'
        elif signal_score >= 70:
            confidence = 'HIGH'
        elif signal_score >= 60:
            confidence = 'MEDIUM_HIGH'
        else:
            confidence = 'MEDIUM'
        
        return {
            'leverage': leverage,
            'position_multiplier': position_mult,
            'confidence': confidence,
            'max_position_size': max_position,
            'leveraged_capital': leveraged_capital,
            'expected_cost': Config.ESTIMATED_1DELTA_GAS if leverage > 1.0 else 0
        }
    
    async def setup_leverage(self, target_leverage):
        """Setup 1delta leverage position (SIMULATION)"""
        
        if Config.SIMULATION_MODE:
            logger.info(f"   ⚠️  SIMULATION: Would setup {target_leverage}x leverage on 1delta")
            logger.info(f"      Collateral: ${Config.TOTAL_CAPITAL:.2f} {Config.COLLATERAL_ASSET}")
            logger.info(f"      Borrow: ${Config.TOTAL_CAPITAL * (target_leverage - 1):.2f} {Config.BORROW_ASSET}")
            logger.info(f"      Gas cost: ~${Config.ESTIMATED_1DELTA_GAS:.2f}")
            
            self.current_leverage = target_leverage
            self.collateral_amount = Config.TOTAL_CAPITAL
            self.debt_amount = Config.TOTAL_CAPITAL * (target_leverage - 1)
            self.leveraged_capital = Config.TOTAL_CAPITAL * target_leverage
            self.health_factor = 2.0  # Simulated safe health factor
            self.is_leveraged = target_leverage > 1.0
            
            return True
        
        # TODO: Real 1delta integration via smart contract
        # Would use flash loans to loop leverage
        logger.info("   🔴 LIVE 1delta integration not yet implemented")
        return False
    
    async def close_leverage(self):
        """Close 1delta leverage position (SIMULATION)"""
        
        if not self.is_leveraged:
            return True
        
        if Config.SIMULATION_MODE:
            logger.info(f"   ⚠️  SIMULATION: Would close {self.current_leverage}x leverage")
            logger.info(f"      Repay: ${self.debt_amount:.2f} {Config.BORROW_ASSET}")
            logger.info(f"      Withdraw: ${self.collateral_amount:.2f} {Config.COLLATERAL_ASSET}")
            logger.info(f"      Gas cost: ~${Config.ESTIMATED_1DELTA_GAS:.2f}")
            
            self.current_leverage = 1.0
            self.collateral_amount = 0
            self.debt_amount = 0
            self.leveraged_capital = Config.TOTAL_CAPITAL
            self.health_factor = float('inf')
            self.is_leveraged = False
            
            return True
        
        # TODO: Real 1delta close
        return False
    
    def check_health_factor(self, eth_price=None):
        """Monitor health factor and trigger auto-deleverage if needed"""
        
        if not self.is_leveraged:
            return True
        
        if Config.SIMULATION_MODE:
            # Simulate health factor based on current leverage
            # Higher leverage = lower health factor
            simulated_hf = 2.5 / self.current_leverage
            self.health_factor = simulated_hf
            
            logger.info(f"   💊 Health Factor: {self.health_factor:.3f} (simulated)")
            
            if self.health_factor < Config.EMERGENCY_HEALTH_FACTOR:
                logger.error(f"   🚨 EMERGENCY: Health factor {self.health_factor:.3f} < {Config.EMERGENCY_HEALTH_FACTOR}")
                return False
            elif self.health_factor < Config.DELEVERAGE_HEALTH_FACTOR:
                logger.warning(f"   ⚠️  LOW HEALTH: {self.health_factor:.3f} < {Config.DELEVERAGE_HEALTH_FACTOR}")
                logger.warning(f"   🔧 Auto-deleverage recommended")
                return False
            elif self.health_factor < Config.MIN_HEALTH_FACTOR:
                logger.warning(f"   ⚠️  Health factor {self.health_factor:.3f} below safe minimum {Config.MIN_HEALTH_FACTOR}")
                return True  # Still OK but warning
            
            return True
        
        # TODO: Real health factor check from 1delta
        return True
    
    async def auto_deleverage(self):
        """Emergency deleverage to improve health factor"""
        
        if not self.is_leveraged:
            return
        
        target_leverage = max(1.0, self.current_leverage * 0.7)  # Reduce by 30%
        
        logger.warning(f"   🔧 AUTO-DELEVERAGING: {self.current_leverage:.2f}x → {target_leverage:.2f}x")
        
        await self.close_leverage()
        
        if target_leverage > 1.0:
            await self.setup_leverage(target_leverage)

# ============================================================================
# SMC INDICATORS
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
        
        # Volume
        df['volume_avg'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_avg']
        
        # Trend
        df['ema_20'] = df['close'].ewm(span=20).mean()
        df['trend_bullish'] = df['close'] > df['ema_20']
        
        # NEW: Add Squeeze Momentum
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

# ============================================================================
# POSITION CLASS (Same as V2)
# ============================================================================

class Position:
    def __init__(self, asset, direction, entry, sl, tp, size, leverage, trade_index=None):
        self.asset = asset
        self.direction = direction
        self.entry = entry
        self.sl = sl
        self.tp = tp
        self.original_size = size
        self.size = size
        self.leverage = leverage
        self.entry_time = datetime.now()
        self.exit_price = None
        self.exit_time = None
        self.pnl = None
        self.status = 'OPEN'
        self.breakeven_moved = False
        self.partial_taken = False
        self.highest_price = entry if direction == 'LONG' else entry
        self.lowest_price = entry if direction == 'SHORT' else entry
        self.trailing_active = False
        self.trade_index = trade_index  # Avantis on-chain trade index
    
    def check_exit(self, current_high, current_low):
        """Check if TP or SL hit"""
        if self.direction == 'LONG':
            if current_high >= self.tp:
                return 'TP', self.tp
            elif current_low <= self.sl:
                return 'SL', self.sl
        else:
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
            if current_price > self.highest_price:
                self.highest_price = current_price
            
            profit_pct = (current_price - self.entry) / self.entry
            if profit_pct >= Config.TRAILING_SL_ACTIVATION:
                self.trailing_active = True
            
            if self.trailing_active:
                new_sl = self.highest_price * (1 - Config.TRAILING_SL_DISTANCE)
                if new_sl > self.sl:
                    old_sl = self.sl
                    self.sl = new_sl
                    logger.trade(f"📈 Trailing SL updated: {self.asset} ${old_sl:.4f} → ${new_sl:.4f}")
                    return True
        
        else:  # SHORT
            if current_price < self.lowest_price:
                self.lowest_price = current_price
            
            profit_pct = (self.entry - current_price) / self.entry
            if profit_pct >= Config.TRAILING_SL_ACTIVATION:
                self.trailing_active = True
            
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
# POSITION MANAGER (Same as V2)
# ============================================================================

class PositionManager:
    def __init__(self):
        self.positions = []
        self.closed_positions = []
        self.total_pnl = 0
        self.daily_pnl = 0
        self.last_reset_date = datetime.now().date()
        self.consecutive_losses = 0
    
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
    
    async def update_positions(self, prices, trading_engine=None):
        """Update with partial profits, breakeven stops, and trailing SL (ON-CHAIN)"""
        for pos in self.positions[:]:
            asset = pos.asset
            if asset not in prices:
                continue
            
            current_price = prices[asset]
            high = current_price * 1.002
            low = current_price * 0.998
            
            # Check for partial profit and breakeven
            if pos.direction == 'LONG':
                progress_to_tp = (current_price - pos.entry) / (pos.tp - pos.entry)
            else:
                progress_to_tp = (pos.entry - current_price) / (pos.entry - pos.tp)
            
            # Update trailing stop loss (and push to Avantis)
            sl_changed = pos.update_trailing_sl(current_price)
            if sl_changed and trading_engine and pos.trade_index is not None:
                await trading_engine.update_sl_on_avantis(asset, pos.trade_index, pos.sl)
            
            # Take partial profit (on Avantis)
            if progress_to_tp >= Config.TAKE_PARTIAL_AT and not pos.partial_taken:
                partial_size = pos.original_size * Config.PARTIAL_SIZE
                
                # Execute partial close on Avantis first
                if trading_engine and pos.trade_index is not None:
                    success = await trading_engine.partial_close_on_avantis(asset, pos.trade_index, partial_size)
                    if success:
                        partial_pnl = pos.take_partial_profit(current_price)
                        self.total_pnl += partial_pnl
                        self.daily_pnl += partial_pnl
                else:
                    # Simulation mode
                    partial_pnl = pos.take_partial_profit(current_price)
                    self.total_pnl += partial_pnl
                    self.daily_pnl += partial_pnl
            
            # Move to breakeven (and update on Avantis)
            if progress_to_tp >= Config.BREAKEVEN_AT and not pos.breakeven_moved:
                be_moved = pos.move_to_breakeven()
                if be_moved and trading_engine and pos.trade_index is not None:
                    await trading_engine.update_sl_on_avantis(asset, pos.trade_index, pos.entry)
            
            # Check for full exit
            exit_type, exit_price = pos.check_exit(high, low)
            
            if exit_type:
                pnl = pos.close(exit_price, exit_type)
                self.positions.remove(pos)
                self.closed_positions.append(pos)
                self.total_pnl += pnl
                self.daily_pnl += pnl
                
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
        
        # Consecutive loss limit
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
                'breakeven_moved': pos.breakeven_moved,
                'trailing_active': pos.trailing_active
            })
        
        df = pd.DataFrame(trades_data)
        df.to_csv(Config.TRADE_LOG, index=False)

# ============================================================================
# TRADING ENGINE
# ============================================================================

class TradingEngine:
    def __init__(self):
        self.position_manager = PositionManager()
        self.onedelta_manager = OneDeltaManager()
        self.running = False
        self.current_signal_score = 0
    
    def check_filters(self, asset, df, signal):
        """Check all filters including Squeeze Momentum"""
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
        
        # NEW: Squeeze Momentum filter
        if Config.USE_SQUEEZE_FILTER:
            # Must be squeeze OFF (breakout condition)
            if not latest['sqz_off']:
                logger.info(f"   Skipped {asset}: Squeeze not OFF (consolidation)")
                return False
            
            # Momentum must align with signal direction
            if signal == 1 and latest['sqz_mom'] <= 0:
                logger.info(f"   Skipped {asset}: LONG but momentum negative ({latest['sqz_mom']:.4f})")
                return False
            if signal == -1 and latest['sqz_mom'] >= 0:
                logger.info(f"   Skipped {asset}: SHORT but momentum positive ({latest['sqz_mom']:.4f})")
                return False
            
            logger.info(f"   ✅ Squeeze filter PASSED: {asset} (sqz_off, mom={latest['sqz_mom']:.4f})")
        
        return True
    
    def calculate_position_size(self, asset, entry, sl):
        asset_capital = Config.ASSETS[asset]['capital']
        equity = self.position_manager.get_equity()
        asset_equity = asset_capital * (equity / Config.TOTAL_CAPITAL)
        
        # Adjust risk based on consecutive losses
        risk_pct = Config.RISK_PER_TRADE
        if self.position_manager.consecutive_losses >= 2:
            risk_pct *= 0.5
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
    
    def calculate_position_size_with_leverage(self, asset, entry, sl, leverage_params):
        """Calculate position size using dynamic leverage from 1delta"""
        
        # Use leveraged capital instead of base capital
        leveraged_capital = leverage_params['leveraged_capital']
        asset_portion = leveraged_capital / 3  # $30, $60, $90, etc. divided by 3 assets
        
        # Adjust risk based on consecutive losses
        risk_pct = Config.RISK_PER_TRADE
        if self.position_manager.consecutive_losses >= 2:
            risk_pct *= 0.5
            logger.info(f"   Reduced risk to {risk_pct*100}% (after {self.position_manager.consecutive_losses} losses)")
        
        risk_amount = asset_portion * risk_pct
        sl_distance = abs(entry - sl) / entry
        
        if sl_distance < Config.MIN_SL_DISTANCE or sl_distance > Config.MAX_SL_DISTANCE:
            return None
        
        # Calculate base size from risk
        calculated_size = risk_amount / sl_distance
        
        # Cap at max_position_size from leverage params (ensures safety)
        max_safe_size = leverage_params['max_position_size']
        size = min(calculated_size, max_safe_size)
        
        # Also cap at 50% of asset capital
        max_size = asset_portion * 0.5
        size = min(size, max_size)
        
        if size < 0.1:
            return None
        
        logger.info(f"   💵 Position size: ${size:.2f} (from ${leveraged_capital:.2f} leveraged capital)")
        logger.info(f"   🛡️  Max loss: ${size * sl_distance * Config.LEVERAGE:.2f} (safe with ${leveraged_capital:.2f})")
        
        return round(size, 2)
    
    async def check_signals(self, asset):
        # Fetch candles
        df = await DataFetcher.fetch_candles(asset, limit=100)
        if df is None or len(df) < 50:
            return
        
        # Add indicators (includes Squeeze if enabled)
        df = SMCIndicators.add_indicators(df, Config.SWING_LENGTH, Config.LOOKBACK_PERIOD)
        
        latest = df.iloc[-1]
        
        if latest['signal'] == 0:
            return
        
        # Check filters (includes Squeeze)
        if not self.check_filters(asset, df, latest['signal']):
            return
        
        # ============================================================================
        # NEW: SIGNAL SCORING & DYNAMIC LEVERAGE
        # ============================================================================
        
        # Calculate signal score (0-100)
        signal_direction = 'LONG' if latest['signal'] == 1 else 'SHORT'
        signal_score = SignalScorer.calculate_score(asset, df, signal_direction, latest)
        self.current_signal_score = signal_score
        
        # Get leverage parameters based on score
        leverage_params = self.onedelta_manager.get_leverage_params(signal_score)
        
        logger.info(f"   🎯 Signal Confidence: {leverage_params['confidence']}")
        logger.info(f"   💰 1delta Leverage: {leverage_params['leverage']}x")
        logger.info(f"   📊 Position Multiplier: {leverage_params['position_multiplier']}x")
        logger.info(f"   💵 Max Position Size: ${leverage_params['max_position_size']:.2f}")
        
        # Setup 1delta leverage if needed
        if leverage_params['leverage'] > 1.0 and not self.onedelta_manager.is_leveraged:
            logger.info(f"   🔧 Setting up {leverage_params['leverage']}x leverage on 1delta...")
            success = await self.onedelta_manager.setup_leverage(leverage_params['leverage'])
            if not success:
                logger.error("   ❌ Failed to setup 1delta leverage - trading with base capital")
                leverage_params['leverage'] = 1.0
                leverage_params['max_position_size'] = Config.TOTAL_CAPITAL / 5
        
        # Check health factor if leveraged
        if self.onedelta_manager.is_leveraged:
            health_ok = self.onedelta_manager.check_health_factor()
            if not health_ok:
                logger.error("   ❌ Health factor too low - cannot open new position")
                await self.onedelta_manager.auto_deleverage()
                return
        
        # ============================================================================
        
        # Check position limits
        if self.position_manager.count_positions(asset) >= Config.MAX_POSITIONS_PER_ASSET:
            return
        
        if self.position_manager.count_positions() >= Config.MAX_TOTAL_POSITIONS:
            return
        
        # Direction limits
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
        
        # Calculate size using dynamic leverage parameters
        size = self.calculate_position_size_with_leverage(asset, current_price, sl, leverage_params)
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
        
        # Execute on Avantis and get trade_index
        trade_index = None
        if Config.SIMULATION_MODE:
            logger.info("⚠️  SIMULATION MODE - Trade not executed on Avantis")
        else:
            # LIVE TRADING - Execute on Avantis
            trade_index = await self.execute_live_trade(asset, direction, current_price, sl, tp, size)
            if trade_index is None:
                logger.error("❌ Failed to get trade_index from Avantis - position not added")
                return
            
            # Set trade_index on position for later updates
            position.trade_index = trade_index
        
        # Add to position manager (after successful execution in live mode)
        self.position_manager.add_position(position)
        
        # Discord notification
        squeeze_status = ""
        if Config.USE_SQUEEZE_FILTER:
            squeeze_status = f"\n🎯 Squeeze: OFF, Momentum: {latest['sqz_mom']:.4f}"
        
        leverage_status = ""
        if Config.USE_1DELTA_LEVERAGE and leverage_params['leverage'] > 1.0:
            leverage_status = (
                f"\n💰 1delta: {leverage_params['leverage']}x leverage"
                f"\n📊 Score: {signal_score:.1f}/100 ({leverage_params['confidence']})"
            )
        
        await send_discord_notification(
            f"🚀 **NEW {direction}** | {asset}\n"
            f"Entry: ${current_price:.4f}\n"
            f"SL: ${sl:.4f} | TP: ${tp:.4f}\n"
            f"Size: ${size:.2f} @ {Config.LEVERAGE}x\n"
            f"Volume: {latest['volume_ratio']:.2f}x avg{squeeze_status}{leverage_status}"
        )
    

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
            
            tx_hash = receipt.transactionHash.hex()
            logger.trade(f"✅ LIVE TRADE EXECUTED: {tx_hash}")
            
            # Get trade index from Avantis
            # The trade index is determined by counting existing trades for this pair
            trades, _ = await trader_client.trade.get_trades(trader)
            
            # Find the trade we just opened (most recent for this pair)
            trade_index = None
            for trade in trades:
                if trade.trade.pair_index == pair_index:
                    # Get the highest trade index for this pair (the one we just opened)
                    if trade_index is None or trade.trade.trade_index > trade_index:
                        trade_index = trade.trade.trade_index
            
            logger.trade(f"📊 Trade index on Avantis: {trade_index}")
            
            await send_discord_notification(
                f"🔴 **LIVE TRADE EXECUTED**\n"
                f"{direction} {asset} @ ${entry:.4f}\n"
                f"Size: ${size:.2f} @ {Config.LEVERAGE}x\n"
                f"Trade Index: {trade_index}\n"
                f"TX: {tx_hash[:10]}..."
            )
            
            return trade_index  # Return trade_index for tracking
            
        except Exception as e:
            logger.error(f"❌ LIVE TRADE FAILED: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await send_discord_notification(f"❌ **LIVE TRADE FAILED**\n{str(e)}")
            return None
    
    async def update_sl_on_avantis(self, asset, trade_index, new_sl):
        """Update stop loss on Avantis (on-chain)"""
        from avantis_trader_sdk import TraderClient
        
        if Config.SIMULATION_MODE:
            logger.info(f"⚠️  SIMULATION: Would update SL to ${new_sl:.4f} on Avantis")
            return True
        
        try:
            trader_client = TraderClient("https://mainnet.base.org")
            trader_client.set_local_signer(Config.PRIVATE_KEY)
            trader = trader_client.get_signer().get_ethereum_address()
            
            pair_index = Config.ASSETS[asset]['pair_index']
            
            # Build SL update transaction
            tx = await trader_client.trade.build_trade_update_sl_tx(
                pair_index=pair_index,
                trade_index=trade_index,
                new_sl=new_sl,
                trader=trader
            )
            
            # Execute
            receipt = await trader_client.sign_and_get_receipt(tx)
            
            logger.trade(f"✅ SL UPDATED ON AVANTIS: ${new_sl:.4f} | TX: {receipt.transactionHash.hex()[:10]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ FAILED TO UPDATE SL ON AVANTIS: {e}")
            return False
    
    async def partial_close_on_avantis(self, asset, trade_index, collateral_to_close):
        """Partially close position on Avantis (on-chain)"""
        from avantis_trader_sdk import TraderClient
        
        if Config.SIMULATION_MODE:
            logger.info(f"⚠️  SIMULATION: Would close ${collateral_to_close:.2f} on Avantis")
            return True
        
        try:
            trader_client = TraderClient("https://mainnet.base.org")
            trader_client.set_local_signer(Config.PRIVATE_KEY)
            trader = trader_client.get_signer().get_ethereum_address()
            
            pair_index = Config.ASSETS[asset]['pair_index']
            
            # Build partial close transaction
            tx = await trader_client.trade.build_trade_close_tx(
                pair_index=pair_index,
                trade_index=trade_index,
                collateral_to_close=collateral_to_close,
                trader=trader
            )
            
            # Execute
            receipt = await trader_client.sign_and_get_receipt(tx)
            
            logger.trade(f"✅ PARTIAL CLOSE ON AVANTIS: ${collateral_to_close:.2f} | TX: {receipt.transactionHash.hex()[:10]}...")
            
            await send_discord_notification(
                f"💰 **PARTIAL PROFIT TAKEN (ON-CHAIN)**\n"
                f"{asset}: Closed ${collateral_to_close:.2f}\n"
                f"TX: {receipt.transactionHash.hex()[:10]}..."
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ FAILED TO PARTIAL CLOSE ON AVANTIS: {e}")
            return False
    
    async def run(self):
        self.running = True
        
        logger.info("="*70)
        logger.info(f"{Config.STRATEGY_NAME}")
        logger.info("="*70)
        logger.info(f"V2 Improvements:")
        logger.info(f"  ✅ Breakeven stops at {Config.BREAKEVEN_AT*100}% to TP")
        logger.info(f"  ✅ Partial profits at {Config.TAKE_PARTIAL_AT*100}% to TP")
        logger.info(f"  ✅ Trailing SL: activates at {Config.TRAILING_SL_ACTIVATION*100}%, trails {Config.TRAILING_SL_DISTANCE*100}%")
        logger.info(f"  ✅ Position limits: {Config.MAX_TOTAL_POSITIONS} total")
        logger.info(f"  ✅ Direction limits: {Config.MAX_LONG_POSITIONS} LONG, {Config.MAX_SHORT_POSITIONS} SHORT")
        logger.info(f"  ✅ Volume filter: {Config.VOLUME_THRESHOLD}x minimum")
        logger.info(f"  ✅ Trend alignment filter enabled")
        logger.info(f"  ✅ Squeeze Momentum filter: {'ENABLED' if Config.USE_SQUEEZE_FILTER else 'DISABLED'}")
        logger.info(f"  ✅ Consecutive loss protection: pause after {Config.CONSECUTIVE_LOSS_LIMIT}")
        logger.info("")
        logger.info(f"1Delta Dynamic Leverage:")
        logger.info(f"  💰 Enabled: {Config.USE_1DELTA_LEVERAGE}")
        if Config.USE_1DELTA_LEVERAGE:
            logger.info(f"  📊 Score-based leverage (max {Config.MAX_1DELTA_LEVERAGE}x)")
            logger.info(f"  🛡️  Min health factor: {Config.MIN_HEALTH_FACTOR}")
            logger.info(f"  ⚠️  Auto-deleverage at: {Config.DELEVERAGE_HEALTH_FACTOR}")
            logger.info(f"  🎯 Signal scoring: Volume, Trend, Squeeze, Momentum, Market")
        logger.info("="*70)
        
        leverage_info = ""
        if Config.USE_1DELTA_LEVERAGE:
            leverage_info = "\n💰 Dynamic 1delta leverage enabled"
        
        await send_discord_notification(
            f"🚀 **{Config.STRATEGY_NAME} Started**\n"
            f"✅ All V2 features + Squeeze filter{leverage_info}\n"
            f"Max positions: {Config.MAX_TOTAL_POSITIONS}"
        )
        
        try:
            while self.running:
                self.position_manager.reset_daily_pnl()
                
                if not self.position_manager.check_risk_limits():
                    logger.error("⛔ RISK LIMITS EXCEEDED - PAUSING")
                    await asyncio.sleep(3600)
                    self.position_manager.consecutive_losses = 0
                    continue
                
                # Check 1delta health factor if leveraged
                if Config.USE_1DELTA_LEVERAGE and self.onedelta_manager.is_leveraged:
                    health_ok = self.onedelta_manager.check_health_factor()
                    if not health_ok and self.onedelta_manager.health_factor < Config.DELEVERAGE_HEALTH_FACTOR:
                        logger.error("⚠️  HEALTH FACTOR TOO LOW - Auto-deleveraging...")
                        await self.onedelta_manager.auto_deleverage()
                
                # Fetch prices
                prices = {}
                for asset in Config.ASSETS.keys():
                    avantis_price = await DataFetcher.get_avantis_price(asset)
                    if avantis_price:
                        prices[asset] = avantis_price
                
                # Update positions (with on-chain updates)
                await self.position_manager.update_positions(prices, trading_engine=self)
                
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
                
                # Add 1delta status if leveraged
                leverage_status = ""
                if Config.USE_1DELTA_LEVERAGE and self.onedelta_manager.is_leveraged:
                    leverage_status = f" | 1delta: {self.onedelta_manager.current_leverage:.1f}x, HF: {self.onedelta_manager.health_factor:.2f}"
                
                logger.info(
                    f"Equity: ${equity:.2f} | Unrealized: ${unrealized_pnl:+.2f} | Total: ${total_equity:.2f} | "
                    f"Open: {self.position_manager.count_positions()} (L:{long_count}/S:{short_count}) | "
                    f"Realized: ${self.position_manager.total_pnl:+.2f} | Losses: {self.position_manager.consecutive_losses}{leverage_status}"
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
    
    logger.info(f"Starting {Config.STRATEGY_NAME}")
    
    engine = TradingEngine()
    await engine.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot stopped by user")

#!/usr/bin/env python3
"""
Strategy 1 - LIVE TRADING
15x Leverage | ARB + OP + ETH | 15m Timeframe

⚠️ THIS TRADES REAL MONEY
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv
from avantis_trader_sdk import TraderClient
from avantis_trader_sdk.types import TradeInput, TradeInputOrderType

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    STRATEGY_NAME = "Strategy 1"
    STRATEGY_VERSION = "1.0.0 - LIVE"
    
    # Wallet
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')
    
    # Network
    BASE_RPC = 'https://mainnet.base.org'
    
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
    RISK_PER_TRADE = 0.03
    RR_RATIO = 2.0
    MAX_POSITIONS_PER_ASSET = 2
    MAX_TOTAL_POSITIONS = 6
    
    # SMC Indicators
    SWING_LENGTH = 3
    LOOKBACK_PERIOD = 20
    MIN_SL_DISTANCE = 0.005
    MAX_SL_DISTANCE = 0.10  # 10% (increased for 15m timeframe)
    
    # Risk Management
    MAX_DRAWDOWN = 0.30
    DAILY_LOSS_LIMIT = 0.10
    
    # Execution
    SLIPPAGE_TOLERANCE = 0.01
    CHECK_INTERVAL = 60
    
    # Discord
    DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', '')
    
    # Logging
    LOG_FILE = 'strategy1_live.log'
    TRADE_LOG = 'strategy1_live_trades.csv'

# ============================================================================
# LOGGING
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

class DataFetcher:
    SYMBOL_MAP = {
        'ARB': 'ARBUSDT',
        'OP': 'OPUSDT',
        'ETH': 'ETHUSDT'
    }
    
    PAIR_INDEX_MAP = {
        'ARB': 4,
        'OP': 7,
        'ETH': 0
    }
    
    @staticmethod
    async def get_avantis_price(asset):
        """Get current price from Avantis (Pyth oracle)"""
        from avantis_trader_sdk import FeedClient
        
        pair_index = DataFetcher.PAIR_INDEX_MAP.get(asset)
        if pair_index is None:
            return None
        
        try:
            feed_client = FeedClient()
            price_data = await feed_client.get_price_update_data(pair_index=pair_index)
            return price_data.pro.price  # Already formatted correctly
        except Exception as e:
            logger.error(f"Failed to fetch Avantis price for {asset}: {e}")
            return None
    
    @staticmethod
    async def fetch_candles(asset, limit=100):
        """Fetch candles from Binance but use Avantis price for latest"""
        symbol = DataFetcher.SYMBOL_MAP.get(asset)
        if not symbol:
            return None
        
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': '15m',
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
            
            # Override latest close with Avantis price
            avantis_price = await DataFetcher.get_avantis_price(asset)
            if avantis_price is not None:
                df.loc[df.index[-1], 'close'] = avantis_price
                logger.info(f"   Using Avantis price for {asset}: ${avantis_price:.6f}")
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to fetch {asset} candles: {e}")
            return None

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
        
        # Signals
        df['signal'] = 0
        for i in range(lookback, len(df)):
            if df['bos_bull'].iloc[i]:
                df.loc[df.index[i], 'signal'] = 1
            elif df['bos_bear'].iloc[i]:
                df.loc[df.index[i], 'signal'] = -1
        
        return df

# ============================================================================
# AVANTIS TRADING ENGINE
# ============================================================================

class AvantisTrader:
    def __init__(self):
        self.client = TraderClient(Config.BASE_RPC)
        self.client.set_local_signer(Config.PRIVATE_KEY)
        self.trader = self.client.get_signer().get_ethereum_address()
        self.running = False
        self.total_pnl = 0
        self.daily_pnl = 0
        self.last_reset_date = datetime.now().date()
    
    def calculate_unrealized_pnl(self, positions, prices):
        """Calculate unrealized P&L on open positions"""
        unrealized = 0
        
        for pos in positions:
            # Get pair index to asset mapping
            asset = None
            for a, config in Config.ASSETS.items():
                if config['pair_index'] == pos.trade.pair_index:
                    asset = a
                    break
            
            if not asset or asset not in prices:
                continue
            
            current_price = prices[asset]
            entry = pos.trade.open_price
            
            # Calculate price change
            if pos.trade.is_long:
                price_change_pct = (current_price - entry) / entry
            else:
                price_change_pct = (entry - current_price) / entry
            
            # Apply leverage
            pnl_pct = price_change_pct * pos.trade.leverage
            
            # Calculate USD P&L
            position_pnl = pos.trade.collateral_in_trade * pnl_pct
            
            unrealized += position_pnl
        
        return unrealized
        
    async def initialize(self):
        """Initialize Avantis - get pair indexes"""
        logger.info("🔧 Initializing Avantis...")
        
        try:
            # Get pair indexes
            pairs_info = await self.client.pairs_cache.get_pairs_info()
            
            for index, pair in pairs_info.items():
                pair_name = f"{pair.from_}/{pair.to}"
                if pair.from_ == 'ETH' and pair.to == 'USD':
                    Config.ASSETS['ETH']['pair_index'] = index
                elif pair.from_ == 'ARB' and pair.to == 'USD':
                    Config.ASSETS['ARB']['pair_index'] = index
                elif pair.from_ == 'OP' and pair.to == 'USD':
                    Config.ASSETS['OP']['pair_index'] = index
            
            logger.info(f"   ETH/USD: pair_index={Config.ASSETS['ETH']['pair_index']}")
            logger.info(f"   ARB/USD: pair_index={Config.ASSETS['ARB']['pair_index']}")
            logger.info(f"   OP/USD: pair_index={Config.ASSETS['OP']['pair_index']}")
            
            # Check USDC allowance
            allowance = await self.client.get_usdc_allowance_for_trading(self.trader)
            if allowance < 30:
                logger.info("   Approving USDC...")
                await self.client.approve_usdc_for_trading(999999)
                await asyncio.sleep(5)
            
            logger.info("✅ Avantis initialized\n")
            
        except Exception as e:
            logger.error(f"Failed to initialize Avantis: {e}")
            raise
    
    async def get_open_positions(self):
        """Get current open positions"""
        try:
            trades, _ = await self.client.trade.get_trades(self.trader)
            return trades
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    async def open_trade(self, asset, direction, entry, sl, tp, size):
        """Open a trade on Avantis"""
        try:
            pair_index = Config.ASSETS[asset]['pair_index']
            if pair_index is None:
                logger.error(f"No pair_index for {asset}")
                return False
            
            # Build trade input with all required fields
            trade_input = TradeInput(
                trader=self.trader,
                pair_index=pair_index,
                index=0,  # Trade index (0 for new)
                collateral_in_trade=size,
                is_long=(direction == 'LONG'),
                leverage=Config.LEVERAGE,
                tp=tp,
                sl=sl if sl > 0 else 0,  # Ensure valid SL
                open_price=None,  # None for market orders
            )
            
            # Build transaction
            tx = await self.client.trade.build_trade_open_tx(
                trade_input=trade_input,
                trade_input_order_type=TradeInputOrderType.MARKET,
                slippage_percentage=Config.SLIPPAGE_TOLERANCE * 100,
            )
            
            # Sign and send
            receipt = await self.client.sign_and_get_receipt(tx)
            
            logger.trade(f"✅ OPENED {direction} {asset} @ ${entry:.4f} | SL: ${sl:.4f} | TP: ${tp:.4f} | Size: ${size:.2f}")
            logger.info(f"   TX: {receipt.transactionHash.hex()}")
            
            await send_discord_notification(
                f"🚀 **{direction} {asset}**\n"
                f"Entry: ${entry:.4f}\n"
                f"SL: ${sl:.4f} | TP: ${tp:.4f}\n"
                f"Size: ${size:.2f} @ {Config.LEVERAGE}x\n"
                f"TX: https://basescan.org/tx/{receipt.transactionHash.hex()}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to open trade: {e}")
            return False
    
    async def check_signals(self, asset):
        """Check for trading signals"""
        # Fetch candles
        df = await DataFetcher.fetch_candles(asset, limit=100)
        if df is None or len(df) < 50:
            return
        
        # Add indicators
        df = SMCIndicators.add_indicators(df, Config.SWING_LENGTH, Config.LOOKBACK_PERIOD)
        
        # Check latest candle
        latest = df.iloc[-1]
        
        if latest['signal'] == 0:
            return
        
        # Check position limits
        positions = await self.get_open_positions()
        asset_positions = [p for p in positions if Config.ASSETS.get(asset, {}).get('pair_index') == p.trade.pair_index]
        
        if len(asset_positions) >= Config.MAX_POSITIONS_PER_ASSET:
            return
        if len(positions) >= Config.MAX_TOTAL_POSITIONS:
            return
        
        # Get current price from Avantis (real-time)
        avantis_price = await DataFetcher.get_avantis_price(asset)
        if avantis_price is None:
            logger.error(f"Could not get Avantis price for {asset}")
            return
        
        current_price = avantis_price
        logger.info(f"   Entry price from Avantis: ${current_price:.6f}")
        
        if latest['signal'] == 1:  # LONG
            direction = 'LONG'
            sl = latest['range_low'] if latest['range_low'] < current_price else current_price * 0.985
            tp = current_price + (current_price - sl) * Config.RR_RATIO
        else:  # SHORT
            direction = 'SHORT'
            sl = latest['range_high'] if latest['range_high'] > current_price else current_price * 1.015
            tp = current_price - (sl - current_price) * Config.RR_RATIO
        
        # Position sizing
        sl_distance = abs(current_price - sl) / current_price
        if sl_distance < Config.MIN_SL_DISTANCE or sl_distance > Config.MAX_SL_DISTANCE:
            return
        
        asset_capital = Config.ASSETS[asset]['capital']
        risk_amount = asset_capital * Config.RISK_PER_TRADE
        size = risk_amount / sl_distance
        size = min(size, asset_capital * 0.5)
        
        if size < 0.1:
            return
        
        size = round(size, 2)
        
        # Open trade
        await self.open_trade(asset, direction, current_price, sl, tp, size)
    
    async def run(self):
        """Main trading loop"""
        self.running = True
        
        logger.info("="*70)
        logger.info(f"{Config.STRATEGY_NAME} - LIVE TRADING")
        logger.info("="*70)
        logger.info(f"Wallet: {self.trader}")
        logger.info(f"Assets: {', '.join(Config.ASSETS.keys())}")
        logger.info(f"Leverage: {Config.LEVERAGE}x")
        logger.info(f"Expected: +129% per week")
        logger.info("="*70)
        logger.info("")
        logger.info("⚠️  LIVE TRADING ACTIVE - REAL MONEY")
        logger.info("")
        
        await send_discord_notification(
            f"🤖 **{Config.STRATEGY_NAME} - LIVE**\n"
            f"Assets: {', '.join(Config.ASSETS.keys())}\n"
            f"Leverage: {Config.LEVERAGE}x\n"
            f"Capital: ${Config.TOTAL_CAPITAL}\n"
            f"⚠️ LIVE TRADING ACTIVE"
        )
        
        try:
            await self.initialize()
            
            while self.running:
                # Reset daily P&L
                today = datetime.now().date()
                if today != self.last_reset_date:
                    self.daily_pnl = 0
                    self.last_reset_date = today
                
                # Get current prices
                prices = {}
                for asset in Config.ASSETS.keys():
                    avantis_price = await DataFetcher.get_avantis_price(asset)
                    if avantis_price:
                        prices[asset] = avantis_price
                
                # Check signals for each asset
                for asset in Config.ASSETS.keys():
                    await self.check_signals(asset)
                
                # Get positions
                positions = await self.get_open_positions()
                
                # Calculate unrealized P&L
                unrealized_pnl = self.calculate_unrealized_pnl(positions, prices)
                
                # Calculate equity
                starting_capital = Config.TOTAL_CAPITAL
                realized_equity = starting_capital + self.total_pnl
                total_equity = realized_equity + unrealized_pnl
                
                # Log status
                logger.info(
                    f"Status | Equity: ${realized_equity:.2f} | "
                    f"Unrealized: ${unrealized_pnl:+.2f} | "
                    f"Total: ${total_equity:.2f} | "
                    f"Open: {len(positions)} | "
                    f"Realized P&L: ${self.total_pnl:+.2f}"
                )
                
                # Log position details
                if positions and prices:
                    for pos in positions:
                        asset = None
                        for a, config in Config.ASSETS.items():
                            if config['pair_index'] == pos.trade.pair_index:
                                asset = a
                                break
                        
                        if asset and asset in prices:
                            current_price = prices[asset]
                            entry = pos.trade.open_price
                            direction = "LONG" if pos.trade.is_long else "SHORT"
                            
                            if pos.trade.is_long:
                                price_change_pct = (current_price - entry) / entry
                            else:
                                price_change_pct = (entry - current_price) / entry
                            
                            pnl_pct = price_change_pct * pos.trade.leverage
                            position_pnl = pos.trade.collateral_in_trade * pnl_pct
                            
                            logger.info(
                                f"   {direction} {asset}: Entry ${entry:.4f} → "
                                f"Current ${current_price:.4f} ({price_change_pct*100:+.2f}%) | "
                                f"Unrealized: ${position_pnl:+.2f}"
                            )
                
                # Wait before next check
                await asyncio.sleep(Config.CHECK_INTERVAL)
        
        except Exception as e:
            logger.error(f"Bot error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await send_discord_notification(f"❌ **BOT ERROR**\n{str(e)}")
        
        finally:
            logger.info("🛑 Bot stopped")

# ============================================================================
# MAIN
# ============================================================================

async def main():
    if not Config.PRIVATE_KEY:
        logger.error("❌ PRIVATE_KEY not found in .env file")
        return
    
    trader = AvantisTrader()
    await trader.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot stopped by user")

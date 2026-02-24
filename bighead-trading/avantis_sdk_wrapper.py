#!/usr/bin/env python3
"""
Avantis SDK Wrapper - Properly implements patterns from official AGENT.md
"""

import asyncio
import aiohttp
from typing import Optional, Dict
import os
from dotenv import load_dotenv

load_dotenv()

class AvantisSDKWrapper:
    """
    Wrapper for Avantis SDK that follows official AGENT.md patterns
    - Uses TraderClient for pair lookups
    - Uses FeedClient for price data
    - Caches pair indexes
    - Falls back to Binance when Avantis is down
    """
    
    def __init__(self, provider_url: str = "https://mainnet.base.org"):
        self.provider_url = provider_url
        self.trader_client = None
        self.feed_client = None
        self.pair_index_cache: Dict[str, int] = {}
        self.initialized = False
        
        # Binance symbol mapping
        self.binance_symbols = {
            'ARB': 'ARBUSDT',
            'OP': 'OPUSDT',
            'ETH': 'ETHUSDT'
        }
        
        # Fallback hardcoded indexes (if Avantis is down)
        self.fallback_indexes = {
            'ARB': 4,
            'OP': 7,
            'ETH': 0
        }
    
    async def initialize(self):
        """Initialize SDK clients and fetch pair indexes"""
        if self.initialized:
            return
        
        try:
            # Initialize clients (official pattern from AGENT.md)
            from avantis_trader_sdk import TraderClient, FeedClient
            
            self.trader_client = TraderClient(self.provider_url)
            self.feed_client = FeedClient()
            
            # Fetch pair indexes dynamically (official pattern)
            await self._fetch_pair_indexes()
            
            self.initialized = True
            
        except Exception as e:
            print(f"[WARNING] Avantis SDK initialization failed: {e}")
            print(f"[WARNING] Using fallback pair indexes and Binance prices")
            self.pair_index_cache = self.fallback_indexes.copy()
            self.initialized = True  # Continue with fallback
    
    async def _fetch_pair_indexes(self):
        """Fetch pair indexes from Avantis (official AGENT.md pattern)"""
        pairs_to_fetch = {
            'ARB': 'ARB/USD',
            'OP': 'OP/USD',
            'ETH': 'ETH/USD'
        }
        
        for asset, pair_name in pairs_to_fetch.items():
            try:
                # Official pattern: trader_client.pairs_cache.get_pair_index()
                pair_index = await self.trader_client.pairs_cache.get_pair_index(pair_name)
                self.pair_index_cache[asset] = pair_index
                print(f"[INFO] Fetched {pair_name} index: {pair_index}")
            except Exception as e:
                # Use fallback if fetch fails
                self.pair_index_cache[asset] = self.fallback_indexes[asset]
                print(f"[WARNING] Failed to fetch {pair_name} index, using fallback: {self.fallback_indexes[asset]}")
    
    def get_pair_index(self, asset: str) -> Optional[int]:
        """Get pair index for an asset"""
        return self.pair_index_cache.get(asset)
    
    async def get_price(self, asset: str) -> Optional[float]:
        """
        Get current price for an asset
        Official pattern: feed_client.get_price_update_data()
        Falls back to Binance if Avantis fails
        """
        if not self.initialized:
            await self.initialize()
        
        pair_index = self.get_pair_index(asset)
        if pair_index is None:
            return None
        
        # Try Avantis first (official pattern)
        try:
            if self.feed_client:
                # Official AGENT.md pattern:
                price_data = await self.feed_client.get_price_update_data(pair_index=pair_index)
                price = price_data.pro.price
                return price
        except Exception as e:
            # Avantis failed, fall back to Binance
            pass
        
        # Binance fallback
        return await self._get_binance_price(asset)
    
    async def _get_binance_price(self, asset: str) -> Optional[float]:
        """Fallback to Binance prices when Avantis is unavailable"""
        symbol = self.binance_symbols.get(asset)
        if not symbol:
            return None
        
        try:
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {'symbol': symbol}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return float(data['price'])
        except Exception as e:
            print(f"[ERROR] Binance fallback failed for {asset}: {e}")
            return None
    
    async def get_prices_batch(self, assets: list) -> Dict[str, float]:
        """Get prices for multiple assets efficiently"""
        prices = {}
        for asset in assets:
            price = await self.get_price(asset)
            if price:
                prices[asset] = price
        return prices
    
    def set_signer(self, private_key: str):
        """Set signer for trading (when ready for live trading)"""
        if self.trader_client:
            self.trader_client.set_local_signer(private_key)
    
    async def get_balance(self, address: str) -> Optional[float]:
        """Get USDC balance (for live trading)"""
        if not self.trader_client:
            return None
        
        try:
            balance = await self.trader_client.get_usdc_balance(address)
            return balance
        except Exception as e:
            print(f"[ERROR] Failed to get balance: {e}")
            return None
    
    async def get_open_trades(self, trader_address: str):
        """Get open trades for an address (for live trading)"""
        if not self.trader_client:
            return [], []
        
        try:
            trades, pending_orders = await self.trader_client.trade.get_trades(trader_address)
            return trades, pending_orders
        except Exception as e:
            print(f"[ERROR] Failed to get trades: {e}")
            return [], []


# Global singleton instance
_sdk_instance = None

async def get_sdk() -> AvantisSDKWrapper:
    """Get or create global SDK instance"""
    global _sdk_instance
    if _sdk_instance is None:
        _sdk_instance = AvantisSDKWrapper()
        await _sdk_instance.initialize()
    return _sdk_instance

#!/usr/bin/env python3
"""
Quick fix: Add Binance price fallback to all bot versions
"""

import os

BOTS = [
    'avantis_bot.py',
    'avantis_bot_v2.py',
    'avantis_bot_v2_squeeze.py',
    'avantis_bot_v2_squeeze_all3.py'
]

OLD_CODE = '''    @staticmethod
    async def get_avantis_price(asset):
        """Get current price from Avantis (Pyth oracle)"""
        from avantis_trader_sdk import FeedClient
        
        pair_index = DataFetcher.PAIR_INDEX_MAP.get(asset)
        if pair_index is None:
            return None
        
        try:
            feed_client = FeedClient()
            price_data = await feed_client.get_price_update_data(pair_index=pair_index)
            return price_data.price
        except Exception as e:
            logger.error(f"Failed to fetch Avantis price for {asset}: {e}")
            return None'''

NEW_CODE = '''    @staticmethod
    async def get_avantis_price(asset):
        """Get current price from Avantis (Pyth oracle) with Binance fallback"""
        from avantis_trader_sdk import FeedClient
        
        pair_index = DataFetcher.PAIR_INDEX_MAP.get(asset)
        if pair_index is None:
            return None
        
        try:
            feed_client = FeedClient()
            price_data = await feed_client.get_price_update_data(pair_index=pair_index)
            return price_data.price
        except Exception as e:
            # Avantis failed, use Binance as fallback
            logger.info(f"Avantis price unavailable for {asset}, using Binance fallback")
            return await DataFetcher.get_binance_price(asset)
    
    @staticmethod
    async def get_binance_price(asset):
        """Get current price from Binance (fallback)"""
        symbol = DataFetcher.SYMBOL_MAP.get(asset)
        if not symbol:
            return None
        
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {'symbol': symbol}
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=5) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    return float(data['price'])
        except Exception as e:
            logger.error(f"Failed to fetch Binance price for {asset}: {e}")
            return None'''

print("Fixing Avantis price fetch in all bots...")

for bot in BOTS:
    file_path = f'$OPENCLAW_HOME/bighead/{bot}'
    
    if not os.path.exists(file_path):
        print(f"  ⏭️  {bot} not found, skipping")
        continue
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        if OLD_CODE in content:
            content = content.replace(OLD_CODE, NEW_CODE)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            print(f"  ✅ Fixed {bot}")
        else:
            print(f"  ⚠️  {bot} - old code not found (already fixed?)")
    
    except Exception as e:
        print(f"  ❌ {bot} - Error: {e}")

print("\n✅ Done! Bots will now use Binance prices when Avantis is unavailable.")
print("Restart your bot to apply the fix.")

#!/usr/bin/env python3
"""
1Delta API Client
Official REST API integration for 1delta lending aggregation
"""

import aiohttp
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class OneDeltaAPIClient:
    """
    1Delta API Client for lending aggregation
    
    Docs: https://docs.1delta.io
    Base URL: https://api.1delta.io (assumed - verify in docs)
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ONEDELTA_API_KEY')
        self.base_url = "https://api.1delta.io"  # Verify this URL
        
        if not self.api_key:
            raise ValueError("1Delta API key not found. Set ONEDELTA_API_KEY in .env")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    async def get_best_supply_rate(
        self,
        asset: str,
        chain_id: int = 8453,  # Base chain
        min_liquidity: str = "1000"
    ) -> Dict:
        """
        Find the best supply rate across all lending protocols
        
        Args:
            asset: Asset symbol (e.g., 'USDC', 'ETH')
            chain_id: Chain ID (8453 = Base)
            min_liquidity: Minimum liquidity required
            
        Returns:
            {
                'protocol': 'aave-v3',
                'marketId': '0x...',
                'supplyAPY': 0.052,
                'liquidity': '45000000',
                'riskScore': 'low',
                'collateralFactor': 0.825
            }
        """
        endpoint = f"{self.base_url}/v1/lending/best-supply"
        
        params = {
            'asset': asset,
            'chainId': chain_id,
            'minLiquidity': min_liquidity
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                endpoint,
                headers=self._get_headers(),
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"1Delta API error ({response.status}): {error}")
    
    async def get_lending_markets(
        self,
        asset: str,
        chain_id: int = 8453
    ) -> List[Dict]:
        """
        Get all available lending markets for an asset
        
        Args:
            asset: Asset symbol
            chain_id: Chain ID
            
        Returns:
            List of markets with normalized metrics
        """
        endpoint = f"{self.base_url}/v1/lending/markets"
        
        params = {
            'asset': asset,
            'chainId': chain_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                endpoint,
                headers=self._get_headers(),
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"1Delta API error ({response.status}): {error}")
    
    async def build_deposit_tx(
        self,
        protocol: str,
        asset: str,
        amount: str,
        user_address: str,
        chain_id: int = 8453
    ) -> Dict:
        """
        Build a deposit transaction
        
        Args:
            protocol: Protocol name (e.g., 'aave-v3')
            asset: Asset symbol
            amount: Amount to deposit (in token units)
            user_address: User's wallet address
            chain_id: Chain ID
            
        Returns:
            Transaction object to sign and send
        """
        endpoint = f"{self.base_url}/v1/tx/deposit"
        
        payload = {
            'protocol': protocol,
            'asset': asset,
            'amount': amount,
            'userAddress': user_address,
            'chainId': chain_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint,
                headers=self._get_headers(),
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"1Delta API error ({response.status}): {error}")
    
    async def build_leverage_tx(
        self,
        protocol: str,
        collateral_asset: str,
        borrow_asset: str,
        collateral_amount: str,
        target_leverage: float,
        user_address: str,
        chain_id: int = 8453
    ) -> Dict:
        """
        Build a leveraged position using flash loans (looping)
        
        Args:
            protocol: Protocol name
            collateral_asset: Asset to use as collateral (e.g., 'ETH')
            borrow_asset: Asset to borrow (e.g., 'USDC')
            collateral_amount: Amount of collateral
            target_leverage: Target leverage (e.g., 2.0 = 2x)
            user_address: User's wallet address
            chain_id: Chain ID
            
        Returns:
            Transaction object for flash loan-based leverage
        """
        endpoint = f"{self.base_url}/v1/tx/leverage"
        
        payload = {
            'protocol': protocol,
            'collateralAsset': collateral_asset,
            'borrowAsset': borrow_asset,
            'collateralAmount': collateral_amount,
            'targetLeverage': target_leverage,
            'userAddress': user_address,
            'chainId': chain_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint,
                headers=self._get_headers(),
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"1Delta API error ({response.status}): {error}")
    
    async def get_health_factor(
        self,
        user_address: str,
        protocol: str = None,
        chain_id: int = 8453
    ) -> Dict:
        """
        Get health factor for a user's position
        
        Args:
            user_address: User's wallet address
            protocol: Optional specific protocol
            chain_id: Chain ID
            
        Returns:
            {
                'healthFactor': 1.5,
                'collateral': {...},
                'debt': {...},
                'liquidationRisk': 'low'
            }
        """
        endpoint = f"{self.base_url}/v1/lending/health"
        
        params = {
            'userAddress': user_address,
            'chainId': chain_id
        }
        
        if protocol:
            params['protocol'] = protocol
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                endpoint,
                headers=self._get_headers(),
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"1Delta API error ({response.status}): {error}")
    
    async def build_deleverage_tx(
        self,
        protocol: str,
        user_address: str,
        reduction_percentage: float,
        chain_id: int = 8453
    ) -> Dict:
        """
        Build transaction to reduce leverage
        
        Args:
            protocol: Protocol name
            user_address: User's wallet address
            reduction_percentage: How much to reduce (0.0-1.0)
            chain_id: Chain ID
            
        Returns:
            Transaction to partially close leveraged position
        """
        endpoint = f"{self.base_url}/v1/tx/deleverage"
        
        payload = {
            'protocol': protocol,
            'userAddress': user_address,
            'reductionPercentage': reduction_percentage,
            'chainId': chain_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint,
                headers=self._get_headers(),
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"1Delta API error ({response.status}): {error}")


# ============================================================================
# TEST CLIENT
# ============================================================================

async def test_onedelta_api():
    """Test 1Delta API client"""
    
    print("="*70)
    print("🔧 1DELTA API CLIENT TEST")
    print("="*70)
    print()
    
    try:
        client = OneDeltaAPIClient()
        print(f"✅ Client initialized")
        print(f"   API Key: {client.api_key[:10]}...{client.api_key[-5:]}")
        print()
        
        # Test 1: Get best supply rate for USDC on Base
        print("📊 Test 1: Best USDC supply rate on Base...")
        try:
            best_rate = await client.get_best_supply_rate(
                asset='USDC',
                chain_id=8453,
                min_liquidity='1000'
            )
            print(f"✅ Best rate found:")
            print(f"   Protocol: {best_rate.get('protocol')}")
            print(f"   APY: {best_rate.get('supplyAPY', 0)*100:.2f}%")
            print(f"   Liquidity: ${float(best_rate.get('liquidity', 0)):,.0f}")
            print()
        except Exception as e:
            print(f"⚠️  API call failed: {e}")
            print()
        
        # Test 2: Get all lending markets
        print("📊 Test 2: All USDC lending markets on Base...")
        try:
            markets = await client.get_lending_markets(
                asset='USDC',
                chain_id=8453
            )
            print(f"✅ Found {len(markets)} markets:")
            for market in markets[:3]:  # Show first 3
                print(f"   {market.get('protocol')}: {market.get('supplyAPY', 0)*100:.2f}% APY")
            print()
        except Exception as e:
            print(f"⚠️  API call failed: {e}")
            print()
        
        # Test 3: Check health factor (will likely return nothing since no position)
        print("📊 Test 3: Check health factor...")
        try:
            health = await client.get_health_factor(
                user_address='YOUR_WALLET_ADDRESS',
                chain_id=8453
            )
            print(f"✅ Health factor: {health.get('healthFactor', 'N/A')}")
            print()
        except Exception as e:
            print(f"⚠️  API call failed (expected if no position): {e}")
            print()
        
        print("="*70)
        print("✅ API CLIENT TESTS COMPLETE")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_onedelta_api())

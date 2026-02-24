#!/usr/bin/env python3
"""
Test 1Delta API endpoints to discover the correct format
"""

import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('ONEDELTA_API_KEY')
BASE_URL = "https://api.1delta.io"

async def test_endpoint(endpoint: str, params: dict = None, method: str = 'GET'):
    """Test an API endpoint"""
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n{'='*70}")
    print(f"Testing: {method} {url}")
    if params:
        print(f"Params: {params}")
    print(f"{'='*70}")
    
    try:
        async with aiohttp.ClientSession() as session:
            if method == 'GET':
                async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    status = response.status
                    text = await response.text()
                    
                    print(f"Status: {status}")
                    print(f"Response: {text[:500]}")
                    
                    if status == 200:
                        try:
                            json_data = await response.json()
                            print(f"✅ SUCCESS!")
                            return json_data
                        except:
                            pass
                    
                    return None
    except asyncio.TimeoutError:
        print("⚠️  Timeout")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

async def main():
    print("="*70)
    print("1DELTA API ENDPOINT DISCOVERY")
    print("="*70)
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-5:]}")
    print(f"Base URL: {BASE_URL}")
    
    # Try different endpoint structures
    endpoints_to_test = [
        # Try root/health
        ("/", {}),
        ("/health", {}),
        ("/v1", {}),
        
        # Try with aggregator parameter (different values)
        ("/v1/lending/markets", {"aggregator": "1delta"}),
        ("/v1/lending/markets", {"aggregator": "aave-v3"}),
        ("/v1/lending/markets", {"aggregator": "all"}),
        ("/v1/lending/markets", {"asset": "USDC", "chainId": 8453, "aggregator": "all"}),
        
        # Try different endpoint paths
        ("/api/v1/markets", {"asset": "USDC", "chainId": 8453}),
        ("/markets", {"asset": "USDC", "chainId": 8453}),
        
        # Try query endpoints
        ("/v1/query/markets", {"asset": "USDC", "chainId": 8453}),
        
        # Try leverage endpoints
        ("/v1/leverage/status", {"userAddress": "YOUR_WALLET_ADDRESS", "chainId": 8453}),
    ]
    
    for endpoint, params in endpoints_to_test:
        result = await test_endpoint(endpoint, params)
        if result:
            print(f"✅ Found working endpoint!")
            print(f"   Endpoint: {endpoint}")
            print(f"   Params: {params}")
            break
        await asyncio.sleep(0.5)  # Rate limiting
    
    print("\n" + "="*70)
    print("DISCOVERY COMPLETE")
    print("="*70)
    
    # Check if there's a docs endpoint
    print("\n🔍 Checking for API documentation...")
    docs_endpoints = [
        "/docs",
        "/v1/docs",
        "/api-docs",
        "/swagger",
        "/.well-known/api-docs"
    ]
    
    for endpoint in docs_endpoints:
        result = await test_endpoint(endpoint, {})
        if result:
            print(f"✅ Found docs at: {endpoint}")
            break
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())

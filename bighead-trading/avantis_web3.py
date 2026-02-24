#!/usr/bin/env python3
"""
Avantis Web3 Integration - Direct Contract Interaction
Bypasses SDK bug by calling contracts directly
"""

from web3 import Web3
from eth_account import Account
import json

# Avantis Contract Addresses on Base
TRADING_CONTRACT = "0x..." # TODO: Get from https://docs.avantisfi.com/
USDC_CONTRACT = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# Minimal ABIs needed
USDC_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

# TODO: Get actual Avantis Trading contract ABI from docs
# Placeholder structure based on error message:
# openTrade((address,uint256,uint256,uint256,uint256,uint256,bool,uint256,uint256,uint256,uint256),uint8,uint256)
TRADING_ABI = [
    {
        "name": "openTrade",
        "type": "function",
        "inputs": [
            {
                "name": "trade",
                "type": "tuple",
                "components": [
                    {"name": "trader", "type": "address"},
                    {"name": "pairIndex", "type": "uint256"},
                    {"name": "index", "type": "uint256"},
                    {"name": "initialPosToken", "type": "uint256"},
                    {"name": "positionSizeUSDC", "type": "uint256"},
                    {"name": "openPrice", "type": "uint256"},
                    {"name": "buy", "type": "bool"},
                    {"name": "leverage", "type": "uint256"},
                    {"name": "tp", "type": "uint256"},
                    {"name": "sl", "type": "uint256"},
                    {"name": "timestamp", "type": "uint256"}
                ]
            },
            {"name": "orderType", "type": "uint8"},
            {"name": "slippageP", "type": "uint256"}
        ],
        "outputs": []
    }
]

class AvantisWeb3:
    """Direct web3 integration with Avantis contracts"""
    
    def __init__(self, rpc_url, private_key):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        
        # Initialize contracts
        self.usdc = self.w3.eth.contract(
            address=Web3.to_checksum_address(USDC_CONTRACT),
            abi=USDC_ABI
        )
        
        # TODO: Uncomment when we have trading contract address
        # self.trading = self.w3.eth.contract(
        #     address=Web3.to_checksum_address(TRADING_CONTRACT),
        #     abi=TRADING_ABI
        # )
    
    def get_usdc_balance(self):
        """Get USDC balance"""
        balance_wei = self.usdc.functions.balanceOf(self.address).call()
        return balance_wei / 1e6  # USDC has 6 decimals
    
    def approve_usdc(self, amount=None):
        """Approve USDC for trading (unlimited if no amount)"""
        if amount is None:
            amount = 2**256 - 1  # Unlimited
        else:
            amount = int(amount * 1e6)  # Convert to wei
        
        tx = self.usdc.functions.approve(
            TRADING_CONTRACT,
            amount
        ).build_transaction({
            'from': self.address,
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.address)
        })
        
        signed = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt
    
    def open_trade(self, pair_index, is_long, collateral, leverage, tp, sl, slippage_pct=1):
        """
        Open a trade on Avantis
        
        Parameters:
        - pair_index: int (e.g., 0=ETH, 4=ARB, 7=OP)
        - is_long: bool (True=LONG, False=SHORT)
        - collateral: float (USDC amount)
        - leverage: int (e.g., 15)
        - tp: float (take profit price)
        - sl: float (stop loss price)
        - slippage_pct: float (e.g., 1 = 1%)
        """
        
        # Convert to contract format (10 decimals for prices, 6 for USDC)
        position_size = int(collateral * 1e6)  # USDC wei
        leverage_scaled = int(leverage * 1e10)  # 10 decimals
        tp_scaled = int(tp * 1e10)  # 10 decimals
        sl_scaled = int(sl * 1e10)  # 10 decimals
        slippage_scaled = int(slippage_pct * 1e10)  # 10 decimals
        
        # Build trade tuple
        trade_tuple = (
            self.address,        # trader
            pair_index,          # pairIndex
            0,                   # index (0 for new trade)
            0,                   # initialPosToken (0 for new)
            position_size,       # positionSizeUSDC
            0,                   # openPrice (0 for market order)
            is_long,             # buy (True=LONG, False=SHORT)
            leverage_scaled,     # leverage
            tp_scaled,           # tp
            sl_scaled,           # sl
            0                    # timestamp (0 for current)
        )
        
        # TODO: Uncomment when trading contract is initialized
        # order_type = 0  # 0 = MARKET
        
        # tx = self.trading.functions.openTrade(
        #     trade_tuple,
        #     order_type,
        #     slippage_scaled
        # ).build_transaction({
        #     'from': self.address,
        #     'gas': 500000,
        #     'gasPrice': self.w3.eth.gas_price,
        #     'nonce': self.w3.eth.get_transaction_count(self.address)
        # })
        
        # signed = self.w3.eth.account.sign_transaction(tx, self.account.key)
        # tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        
        # receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        # return receipt
        
        print(f"⚠️  Web3 integration ready but needs Avantis contract address")
        print(f"   Would open: {'LONG' if is_long else 'SHORT'} pair {pair_index}")
        print(f"   Collateral: ${collateral:.2f}, Leverage: {leverage}x")
        print(f"   TP: ${tp:.4f}, SL: ${sl:.4f}")
        
        return None

# Quick test
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    rpc = "https://mainnet.base.org"
    key = os.getenv('PRIVATE_KEY')
    
    if key:
        avantis = AvantisWeb3(rpc, key)
        print(f"Address: {avantis.address}")
        print(f"USDC Balance: ${avantis.get_usdc_balance():.2f}")
        
        # Test trade (won't execute without contract address)
        avantis.open_trade(
            pair_index=4,  # ARB
            is_long=True,
            collateral=5.0,
            leverage=15,
            tp=0.12,
            sl=0.095,
            slippage_pct=1
        )
    else:
        print("No private key found")

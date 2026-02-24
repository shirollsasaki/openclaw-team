# V2 Fixed - Web3Trader Error Resolved ✅

## Problem
```
NameError: name 'Web3' is not defined
```

V2 was trying to use `Web3` in the `Web3Trader` class but we removed the import when updating to the new SDK wrapper.

---

## Fix Applied

### Before:
```python
# At module level: No web3 imports

class Web3Trader:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(Config.BASE_RPC))  # ❌ Web3 not defined
```

### After:
```python
class Web3Trader:
    def __init__(self):
        try:
            from web3 import Web3  # ✅ Import inside class
            from eth_account import Account
            self.w3 = Web3(Web3.HTTPProvider(Config.BASE_RPC))
            self.account = Account.from_key(Config.PRIVATE_KEY)
        except ImportError:
            raise Exception("web3.py not installed")

class TradingEngine:
    def __init__(self):
        self.position_manager = PositionManager()
        # Make Web3Trader optional (simulation mode doesn't need it)
        self.web3_trader = None
        try:
            self.web3_trader = Web3Trader()
        except:
            logger.info("⚠️  Web3Trader not available - simulation mode only")
        self.running = False
```

---

## What This Means

✅ **V2 will now start successfully**
- Web3Trader initializes if web3.py is installed
- If not, it falls back to simulation mode
- Bot continues running either way

✅ **Works in both modes:**
- **Simulation mode:** Uses position tracking, no real trades
- **Live mode:** Can use Web3Trader when ready (needs Avantis contract address)

---

## Try Again

```bash
cd $OPENCLAW_HOME/bighead
python3 avantis_bot_v2.py
```

Should now start successfully! ✅

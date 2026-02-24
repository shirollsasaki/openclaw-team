# ✅ Wallet Funded - Next Steps

**Wallet:** `YOUR_WALLET_ADDRESS`

**Current Balance:**
- ✅ **0.0021 ETH** (~$6.30 for gas)
- ⏳ **30 USDC** (check BaseScan to confirm)

---

## 🔍 Step 1: Verify USDC Arrived

Click here: **https://basescan.org/address/YOUR_WALLET_ADDRESS**

Look for:
- **Tokens** section
- **USDC** balance should show **30.00**

If USDC shows up → Proceed to Step 2 ✅  
If not → Wait a few minutes for transaction to confirm

---

## 🔐 Step 2: Approve USDC for Avantis

**Why:** The bot needs permission to spend your USDC on Avantis

### **2a. Get Avantis Contract Address**

Visit: **https://docs.avantisfi.com/**

Look for:
- "Contract Addresses"
- "Trading Contract" on **Base** network
- Copy the address (starts with 0x...)

### **2b. Update Approval Script**

```bash
nano approve_usdc.py
```

Find this line (around line 20):
```python
AVANTIS_TRADING_CONTRACT = "0x_REPLACE_WITH_AVANTIS_CONTRACT_ADDRESS"
```

Replace with the address you found:
```python
AVANTIS_TRADING_CONTRACT = "0xYOUR_AVANTIS_ADDRESS_HERE"
```

Save and exit (Ctrl+X, then Y, then Enter)

### **2c. Run Approval**

```bash
python3 approve_usdc.py
```

**Expected output:**
```
🔐 USDC Approval for Avantis Trading

✅ Connected to Base network
📝 Building approval transaction...
🔏 Signing transaction...
📤 Sending transaction...
✅ Transaction sent!
⏳ Waiting for confirmation...
✅ USDC approved successfully!
```

**Check transaction on BaseScan to confirm**

---

## 🚀 Step 3: Start the Bot (Simulation Mode)

**Once USDC is approved:**

```bash
cd $OPENCLAW_HOME/bighead
python3 avantis_bot.py
```

**Expected output:**
```
======================================================================
AVANTIS TRADING BOT - STRATEGY 1
======================================================================
Strategy: Strategy 1 v1.0.0
Wallet: YOUR_WALLET_ADDRESS
Assets: ARB, OP, ETH
Leverage: 15x
Expected Return: +129% per week
======================================================================

⚠️  RUNNING IN SIMULATION MODE
⚠️  To trade live, integrate Avantis SDK trade execution

[2025-02-21 12:00:00] [INFO] 🤖 Strategy 1 started
[2025-02-21 12:00:00] [INFO] Trading: ARB, OP, ETH
[2025-02-21 12:00:00] [INFO] Leverage: 15x | Risk: 3% per trade
```

**The bot will:**
- Check for signals every 60 seconds
- Simulate trades (no real money yet)
- Log everything to `strategy1_bot.log`

---

## 📊 Step 4: Monitor (24 Hours)

### **Watch logs:**
```bash
tail -f strategy1_bot.log
```

### **Check trades:**
```bash
cat strategy1_trades.csv
```

### **What to expect:**
- 2-3 signals per day per asset
- Simulated P&L tracked
- No real trades executed yet

**After 24 hours:**
- Review simulated performance
- If positive → Enable live trading (Step 5)
- If negative → Debug and extend simulation

---

## 🔴 Step 5: Enable Live Trading (After 24h Simulation)

**Only proceed if simulation was profitable!**

### **5a. Get ARB/OP Pair Indexes**

The bot needs to know which pair IDs Avantis uses for ARB and OP.

Visit Avantis docs or run this query on their SDK:

```python
from avantis_trader_sdk import TraderClient

client = TraderClient("https://mainnet.base.org")
pairs = await client.pairs_cache.get_pairs_info()

for index, pair in pairs.items():
    if pair.from_ in ['ARB', 'OP', 'ETH']:
        print(f"{pair.from_}: pair_index = {index}")
```

Update `avantis_bot.py`:
```python
ASSETS = {
    'ARB': {'capital': 10.0, 'pair_index': YOUR_ARB_INDEX},
    'OP': {'capital': 10.0, 'pair_index': YOUR_OP_INDEX},
    'ETH': {'capital': 10.0, 'pair_index': 1}  # Already known
}
```

### **5b. Install Avantis SDK**

```bash
pip3 install avantis_trader_sdk eth-account
```

### **5c. Integrate Trade Execution**

Edit `avantis_bot.py`, find the `check_signals()` function (around line 500).

Find this comment:
```python
# TODO: Execute actual trade via Avantis SDK
# For now, this is simulation mode
```

Replace with:
```python
# Execute trade on Avantis
from avantis_trader_sdk import TraderClient
from avantis_trader_sdk.types import TradeInput, TradeInputOrderType

trader_client = TraderClient(Config.RPC_URL)
trader_client.set_local_signer(Config.PRIVATE_KEY)

trade_input = TradeInput(
    trader=Config.WALLET_ADDRESS,
    pair_index=Config.ASSETS[asset]['pair_index'],
    collateral_in_trade=size,
    is_long=(direction == 'LONG'),
    leverage=Config.LEVERAGE,
    tp=tp,
    sl=sl
)

tx = await trader_client.trade.build_trade_open_tx(
    trade_input,
    TradeInputOrderType.MARKET,
    slippage_percentage=Config.SLIPPAGE_TOLERANCE * 100
)

receipt = await trader_client.sign_and_get_receipt(tx)
logger.info(f"✅ Trade executed: {receipt.transactionHash.hex()}")
```

### **5d. Test with Small Amount**

Before going full $30:
1. Change capital to $3 per asset (total $9)
2. Run for 1-2 trades
3. Verify trades execute correctly
4. Scale back to $30 if successful

---

## 📋 Quick Checklist

### **Before Running Bot:**
- [x] ✅ Wallet funded (0.0021 ETH)
- [ ] ⏳ USDC confirmed (30 USDC)
- [ ] ⏳ USDC approved for Avantis
- [ ] ⏳ Bot started in simulation mode

### **After 24h Simulation:**
- [ ] ⏳ Simulated trades profitable?
- [ ] ⏳ ARB/OP pair indexes found
- [ ] ⏳ Avantis SDK installed
- [ ] ⏳ Trade execution integrated
- [ ] ⏳ Live trading enabled

---

## 🛟 Need Help?

**Stuck on a step?**
1. Check `SETUP.md` for detailed instructions
2. Check logs: `tail -f strategy1_bot.log`
3. Verify wallet: https://basescan.org/address/YOUR_WALLET_ADDRESS

**Common Issues:**
- **"No signals"** → Normal, wait. Expect 2-3/day.
- **"USDC approval failed"** → Check you have enough ETH for gas
- **"Bot crashed"** → Check logs for error, restart bot

---

## 🎯 Your Current Position

**Status:** ✅ Wallet funded with ETH  
**Next:** Verify USDC arrived → Approve USDC → Start bot

**You're on Step 1.** ✅

Once USDC confirms, proceed to Step 2 (approval).

---

**Questions? Let me know!** 🚀

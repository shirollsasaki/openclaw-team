# Fix: LEVERAGE_INCORRECT Error

**Error:** `execution reverted: LEVERAGE_INCORRECT`  
**Asset:** OP (Optimism)  
**Time:** 2026-02-22 17:44

---

## 🔍 ROOT CAUSE

**What happened:**
- ARB trade: ✅ Executed successfully at 15x
- OP trade: ❌ Failed with LEVERAGE_INCORRECT at 15x

**Likely reason:**
Avantis has **different max leverage limits per pair**:
- Major assets (ETH, BTC): Up to 200x
- Mid-cap (ARB): Up to 15x ✅
- Smaller cap (OP): Likely **10x or 12x max** ⚠️

---

## ✅ SOLUTION OPTIONS

### **Option 1: Reduce OP Leverage to 10x** (SAFE)

**Change:**
```python
# OLD (single leverage for all):
LEVERAGE = 15

# NEW (per-asset leverage):
LEVERAGE = {
    'ARB': 15,
    'OP': 10,   # Reduced for OP
    'ETH': 15
}
```

**Impact:**
- ARB: Still 15x (works)
- OP: 10x (should work)
- Same risk management
- Slightly lower profits on OP trades

---

### **Option 2: Disable OP, Use Only ARB** (SIMPLEST)

**Change:**
```python
ASSETS = {
    'ARB': {'capital': 60.0, 'pair_index': 4},  # All capital on ARB
    'OP': {'capital': 0.0, 'pair_index': 7},    # Disable OP
    'ETH': {'capital': 0.0, 'pair_index': 0}
}
```

**Pros:**
- No leverage issues
- All capital on one working asset
- Simpler to manage

**Cons:**
- Less diversification
- Miss OP signals

---

### **Option 3: Test and Find OP Max Leverage** (THOROUGH)

**Steps:**
1. Try 12x leverage for OP
2. If fails, try 10x
3. If fails, try 8x
4. Use whatever works

**Time:** 5-10 minutes testing

---

## 🎯 RECOMMENDED: Option 1 (Reduce OP to 10x)

**Why:**
- Keep diversification
- Conservative leverage for OP
- ARB still at 15x
- Both assets trading

**Risk/Reward Comparison:**

### **ARB @ 15x:**
```
Entry: $0.0950
SL: $0.0931 (2%)
TP: $0.0969 (2%, 1:1 for example)

Win: $30 × 2% × 15x = $9 profit
Loss: $30 × 2% × 15x = -$9 loss
```

### **OP @ 10x:**
```
Entry: $1.85
SL: $1.81 (2%)
TP: $1.89 (2%)

Win: $30 × 2% × 10x = $6 profit
Loss: $30 × 2% × 10x = -$6 loss
```

**Impact:** OP profits ~33% lower, but still profitable! ✅

---

## 🔧 IMPLEMENTATION (Option 1)

### **Step 1: Add Per-Asset Leverage**

**In `avantis_bot_v2_squeeze.py`:**

**Find:**
```python
LEVERAGE = 15
```

**Replace with:**
```python
LEVERAGE = {
    'ARB': 15,
    'OP': 10,
    'ETH': 15
}
```

---

### **Step 2: Update execute_live_trade**

**Find this line (~line 890):**
```python
leverage=Config.LEVERAGE,
```

**Replace with:**
```python
leverage=Config.LEVERAGE[asset],
```

---

### **Step 3: Update Position class**

**Find:**
```python
self.leverage = Config.LEVERAGE
```

**Replace with:**
```python
self.leverage = Config.LEVERAGE[asset]
```

---

### **Step 4: Restart Bot**

```bash
bash STOP_LIVE_BOT.sh
bash START_LIVE_BOT.sh
```

---

## 📊 EXPECTED RESULTS

### **After Fix:**

**ARB Trades:**
```
Leverage: 15x ✅
Position: $12-45
Max profit: $9-33 per $30 position
Status: Working perfectly
```

**OP Trades:**
```
Leverage: 10x ✅
Position: $12-45
Max profit: $6-22 per $30 position
Status: Should execute without errors
```

**Both assets trading, no more LEVERAGE_INCORRECT!** ✅

---

## ⚠️ ALTERNATIVE: Quick Test First

**Before coding, test manually:**

```python
# In Python shell:
from avantis_trader_sdk import TraderClient, TradeInput, TradeInputOrderType

client = TraderClient("https://mainnet.base.org")
client.set_local_signer("YOUR_PRIVATE_KEY")

# Test OP at different leverages
for lev in [12, 10, 8]:
    try:
        trade_input = TradeInput(
            trader="YOUR_WALLET_ADDRESS",
            pair_index=7,  # OP
            collateral_in_trade=12.0,
            is_long=False,
            leverage=lev,
            tp=1.89,
            sl=1.81
        )
        
        # Just estimate gas (don't execute)
        tx = await client.trade.build_trade_open_tx(
            trade_input=trade_input,
            trade_input_order_type=TradeInputOrderType.MARKET,
            slippage_p=1.0
        )
        
        print(f"✅ {lev}x leverage WORKS for OP!")
        break
    except Exception as e:
        if "LEVERAGE_INCORRECT" in str(e):
            print(f"❌ {lev}x too high for OP")
        else:
            print(f"⚠️  {lev}x - different error: {e}")
```

---

## 🎯 MY RECOMMENDATION

**Do this:**

1. **Implement Option 1** (per-asset leverage)
2. **Set OP to 10x** (conservative, likely to work)
3. **Keep ARB at 15x** (confirmed working)
4. **Restart bot**
5. **Monitor next OP signal**

**Time:** 5 minutes

**Want me to make these changes?** 🔧

---

## 📈 PERFORMANCE IMPACT

### **With 10x on OP:**
- Slightly lower profits on OP trades (~33% less)
- Same risk management
- Both assets trading ✅
- No more errors ✅

### **Example Week:**
```
ARB trades: 2 @ 15x → $18 profit
OP trades: 1 @ 10x → $6 profit
Total: $24/week

vs

ARB trades: 2 @ 15x → $18 profit
OP trades: 0 (error) → $0 profit
Total: $18/week (missing OP!)
```

**Better to have OP at 10x than not at all!** ✅

---

**Ready to fix? Say the word!** 🚀

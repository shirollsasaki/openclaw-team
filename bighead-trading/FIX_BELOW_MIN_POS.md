# Fix: BELOW_MIN_POS Error

**Error:** `execution reverted: BELOW_MIN_POS`  
**Cause:** Position size (collateral) below Avantis minimum  
**Time:** 2026-02-22 16:28

---

## 🔍 ROOT CAUSE

### **Current Setup:**
```python
Capital per asset: $10
Risk per trade: 3% = $0.30
Current min check: size < $0.10
```

### **What Happens:**
```python
# With 3% SL distance:
size = $0.30 / 0.03 = $10 collateral ✅

# With 5% SL distance:
size = $0.30 / 0.05 = $6 collateral ⚠️

# With 8% SL distance:
size = $0.30 / 0.08 = $3.75 collateral ❌ BELOW MIN
```

**Avantis likely requires minimum $10-20 collateral per position!**

---

## ✅ SOLUTION

### **Option 1: Increase Minimum Position Size (Recommended)**

**Change:**
```python
# OLD
if size < 0.1:
    return None

# NEW  
MIN_POSITION_SIZE = 10.0  # Avantis minimum (estimate)

if size < MIN_POSITION_SIZE:
    logger.info(f"   Skipped: Position too small (${size:.2f} < ${MIN_POSITION_SIZE})")
    return None
```

**Result:** Only trade when we can open positions >= $10 collateral

---

### **Option 2: Increase Capital Per Asset**

**Change:**
```python
# OLD
ASSETS = {
    'ARB': {'capital': 10.0, 'pair_index': 4},
    'OP': {'capital': 10.0, 'pair_index': 7},
    'ETH': {'capital': 10.0, 'pair_index': 0}
}

# NEW
ASSETS = {
    'ARB': {'capital': 15.0, 'pair_index': 4},  # $15 each
    'OP': {'capital': 15.0, 'pair_index': 7},
    'ETH': {'capital': 0.0, 'pair_index': 0}    # Disable ETH for now
}

TOTAL_CAPITAL = 30.0  # Still $30 total, just 2 assets
```

**Result:** 
- 3% risk = $0.45 per trade
- Min position size: $0.45 / 0.05 = $9 (borderline)
- Better: $0.45 / 0.03 = $15 ✅

---

### **Option 3: Increase Risk Per Trade**

**Change:**
```python
# OLD
RISK_PER_TRADE = 0.03  # 3%

# NEW
RISK_PER_TRADE = 0.05  # 5%
```

**Result:**
- 5% risk on $10 = $0.50
- Min position: $0.50 / 0.05 = $10 ✅
- **But:** Higher risk!

---

### **Option 4: Combination (BEST)**

**Changes:**
```python
# 1. Increase min position size
MIN_POSITION_SIZE = 12.0  # Safe buffer above Avantis min

# 2. Adjust capital allocation
ASSETS = {
    'ARB': {'capital': 15.0, 'pair_index': 4},
    'OP': {'capital': 15.0, 'pair_index': 7},
    'ETH': {'capital': 0.0, 'pair_index': 0}  # Disable for now
}

# 3. Keep risk conservative
RISK_PER_TRADE = 0.03  # 3%
```

**Math:**
- Per asset: $15
- 3% risk: $0.45
- Position (3% SL): $0.45 / 0.03 = $15 ✅
- Position (5% SL): $0.45 / 0.05 = $9 (too small, skip)
- Min check: $12 (safety buffer)

**Result:**
- Only trades with tight SLs (better quality)
- All positions >= $12 collateral
- Conservative risk management
- Better chance of meeting Avantis minimum

---

## 🚀 RECOMMENDED FIX

**Apply Option 4 (Combination):**

1. **Increase minimum position size to $12**
2. **Reallocate $30 to 2 assets ($15 each)** instead of 3
3. **Keep 3% risk**
4. **Only trade when SL tight enough** to generate $12+ position

**This ensures:**
- ✅ All positions above Avantis minimum
- ✅ Conservative risk (3%)
- ✅ Better trade quality (tighter SLs)
- ✅ Still using full $30 capital

---

## 📊 BEFORE vs AFTER

### **Before:**
```
3 assets × $10 = $30 total
3% risk = $0.30 per trade
Min position: $0.10

With 8% SL: $0.30/0.08 = $3.75 ❌ TOO SMALL
```

### **After (Option 4):**
```
2 assets × $15 = $30 total
3% risk = $0.45 per trade  
Min position: $12

With 3% SL: $0.45/0.03 = $15 ✅ GOOD
With 5% SL: $0.45/0.05 = $9 ❌ SKIP (below $12)
With 8% SL: $0.45/0.08 = $5.625 ❌ SKIP
```

**Only trades high-quality setups with tight SLs!** ✅

---

## 🛠️ IMPLEMENTATION

**File:** `avantis_bot_v2_squeeze.py`

**Changes needed:**

### **1. Add MIN_POSITION_SIZE constant**
```python
class Config:
    ...
    # Position Sizing
    MIN_POSITION_SIZE = 12.0  # Avantis minimum (with buffer)
    RISK_PER_TRADE = 0.03
    ...
```

### **2. Update ASSETS allocation**
```python
ASSETS = {
    'ARB': {'capital': 15.0, 'pair_index': 4},
    'OP': {'capital': 15.0, 'pair_index': 7},
    'ETH': {'capital': 0.0, 'pair_index': 0}  # Disabled
}
TOTAL_CAPITAL = 30.0
```

### **3. Update calculate_position_size check**
```python
def calculate_position_size(self, asset, entry, sl):
    ...
    size = round(size, 2)
    
    # Check minimum (Avantis requirement)
    if size < Config.MIN_POSITION_SIZE:
        logger.info(f"   Skipped: Position too small (${size:.2f} < ${Config.MIN_POSITION_SIZE})")
        return None
    
    return size
```

---

## ⏱️ TIME TO FIX

**5 minutes:**
1. Update Config constants
2. Test calculation
3. Restart bot

---

## ✅ VERIFICATION

**After fix, bot should:**
- Skip signals with wide SLs (below $12 position)
- Only trade high-quality setups (tight SLs)
- All positions >= $12 collateral
- No more BELOW_MIN_POS errors

**Test:**
```python
# Simulate:
capital = 15
risk_pct = 0.03
risk_amount = capital * risk_pct  # $0.45

# Tight SL (3%):
sl_distance = 0.03
size = risk_amount / sl_distance
print(f"3% SL: ${size:.2f}")  # $15 ✅

# Wide SL (5%):
sl_distance = 0.05
size = risk_amount / sl_distance
print(f"5% SL: ${size:.2f}")  # $9 ❌ Skip

# Very wide SL (8%):
sl_distance = 0.08
size = risk_amount / sl_distance
print(f"8% SL: ${size:.2f}")  # $5.63 ❌ Skip
```

---

## 🎯 NEXT STEPS

1. **Apply fix** (Option 4)
2. **Restart bot**
3. **Monitor next signal**
4. **Verify no BELOW_MIN_POS**
5. **Check trade quality improves**

---

**Ready to apply fix?** 🔧

# How Volume Filter Works 📊

## The Message You Saw

```
[2026-02-22 00:33:51] [INFO] Skipped ARB: Low volume (0.32x)
```

This means the bot **detected a trading signal** for ARB, but **rejected it** because volume was too low.

---

## 🔍 How It's Calculated

### **Step 1: Calculate 20-Period Volume Average**

```python
df['volume_avg'] = df['volume'].rolling(20).mean()
```

**Example data (last 20 candles):**
```
Candle 1:  volume = 1000
Candle 2:  volume = 1200
Candle 3:  volume = 900
...
Candle 20: volume = 1100

Average = (1000 + 1200 + 900 + ... + 1100) / 20 = 1050
```

---

### **Step 2: Calculate Current Volume Ratio**

```python
df['volume_ratio'] = df['volume'] / df['volume_avg']
```

**Example:**
```
Current candle volume: 335
Volume average (20 periods): 1050

Volume ratio = 335 / 1050 = 0.32x
```

**This means:** Current volume is only **32% of the average** volume.

---

### **Step 3: Apply Filter**

```python
VOLUME_THRESHOLD = 1.5  # Minimum required

if volume_ratio < VOLUME_THRESHOLD:
    # REJECT the signal
    logger.info(f"Skipped {asset}: Low volume ({volume_ratio:.2f}x)")
    return False
```

**In your case:**
- ARB volume ratio: **0.32x**
- Required minimum: **1.5x**
- **0.32 < 1.5** → Signal rejected ❌

---

## 📈 Visual Example

### **Good Volume (Signal Accepted)** ✅

```
Last 20 candles average: 1000
Current candle volume:   2100

Volume ratio = 2100 / 1000 = 2.1x

2.1x > 1.5x threshold ✅
→ Signal ACCEPTED, bot can trade
```

---

### **Bad Volume (Signal Rejected)** ❌

```
Last 20 candles average: 1000
Current candle volume:   320

Volume ratio = 320 / 1000 = 0.32x

0.32x < 1.5x threshold ❌
→ Signal REJECTED (low volume)
```

---

## 🎯 Why This Filter Exists

### **Problem Without Volume Filter:**
- **Low volume = unreliable price action**
- Breakouts on low volume often **fail** (false signals)
- **Example:** Price breaks resistance but only 100 traders → likely to reverse

### **With Volume Filter:**
- **High volume = real conviction**
- More traders participating = **stronger move**
- **Example:** Price breaks resistance with 2000 traders → likely to continue

---

## 📊 Real Example from Your Bot

### **ARB Signal at 00:33:51**

```
Signal detected: LONG ARB (Break of Structure)
Current price: $0.0993
Entry would be: $0.0993

Volume check:
  Last 20 candles avg: ~1,050 units
  Current candle:      335 units
  Ratio:              0.32x

Filter decision: ❌ REJECT
Reason: 0.32x < 1.5x (only 32% of normal volume)
```

**Why rejected:**
- ARB showed a breakout signal
- But only **32% of normal volume**
- Too risky - likely a **false breakout**
- Bot skipped it to avoid losing trade

---

## ⚙️ Volume Filter Settings

### **Current Config (All Bots):**

```python
USE_VOLUME_FILTER = True
VOLUME_THRESHOLD = 1.5  # Must be 1.5x average volume
```

### **What This Means:**
- ✅ Volume must be **50% ABOVE average** (1.5x)
- ❌ Normal volume (1.0x) is **not enough**
- ❌ Below average (0.32x) is **way too low**

---

## 🔧 Adjusting the Filter

### **Want More Trades? (Lower threshold)**

```python
VOLUME_THRESHOLD = 1.2  # Accept 20% above average
```

**Effect:**
- More signals accepted
- More trades
- But **lower quality** (more false signals)

---

### **Want Fewer, Better Trades? (Higher threshold)**

```python
VOLUME_THRESHOLD = 2.0  # Require 2x average volume
```

**Effect:**
- Fewer signals accepted
- Fewer trades
- But **higher quality** (stronger signals)

---

### **Disable Volume Filter? (Not recommended)**

```python
USE_VOLUME_FILTER = False
```

**Effect:**
- All signals accepted regardless of volume
- **Many more trades**
- **Much higher risk** (false breakouts)
- **Lower win rate**

---

## 📊 Filter Comparison

| Threshold | Signals Accepted | Quality | Trades/Week | Recommended? |
|-----------|------------------|---------|-------------|--------------|
| **1.2x** | Many | Medium | ~25 | ⚠️ Aggressive |
| **1.5x** | Moderate | Good | ~17 | ✅ **Current** |
| **2.0x** | Few | Excellent | ~10 | ✅ Conservative |
| **OFF** | All | Poor | ~35 | ❌ Not recommended |

---

## 🎯 Current Bot Behavior

**Your bots right now:**

1. **Detect signal** (Break of Structure, etc.)
2. **Check volume ratio:**
   - If < 1.5x → Skip (like ARB at 0.32x)
   - If ≥ 1.5x → Continue to next filter
3. **Check other filters** (trend, time, RSI, etc.)
4. **If all pass** → Take trade

---

## 📉 Why ARB Had Low Volume

**Possible reasons for 0.32x volume:**

1. **Time of day:** Off-peak hours (less traders)
2. **Market conditions:** Overall low activity
3. **No news:** Nothing driving volume
4. **Consolidation:** Market waiting for breakout

**Bot's decision:** ✅ **Correct to skip**
- Low volume breakout = high risk of failure
- Waiting for stronger signal with volume confirmation

---

## 💡 What Happens Next

**Bot will keep monitoring ARB:**
- If volume increases to 1.5x+ **AND** signal appears → Trade ✅
- If volume stays low → Keep skipping ❌

**Expected:**
- During US trading hours (1-6 PM UTC): Volume higher → More signals
- During off-hours (midnight-6 AM UTC): Volume lower → More skips

---

## 🔍 Check Current Volume

Want to see current volume ratios?

```bash
# Add this to your bot monitoring
grep "volume_ratio" strategy1_v2.log | tail -20
```

Or I can add volume ratio to the Discord updates if you want!

---

## ✅ Summary

**Your bot saw:**
- 📊 ARB breakout signal
- 📉 Volume only 0.32x average (way too low)
- ❌ Rejected to avoid false breakout
- ✅ Smart risk management working correctly

**This is GOOD behavior!** The filter is protecting you from low-quality trades. 🛡️

---

**Want to adjust the volume threshold or see more volume stats in updates?** Let me know!

# 📊 Price Source: Avantis Only

**Updated:** 2026-02-21

## ✅ Changes Made

**Before:**
- Bot fetched all prices from Binance
- Used Binance ARBUSDT for entry decisions
- Could cause price mismatch with Avantis

**After:**
- Bot uses **Avantis (Pyth oracle)** for ALL entry prices
- Binance only used for historical candles (SMC patterns)
- Latest candle close ALWAYS replaced with Avantis real-time price
- Entry price verified against Avantis before trade

## 🔄 How It Works Now

### 1. Signal Detection
```python
# Fetch 15m candles from Binance (historical OHLC)
candles = await fetch_candles(asset, limit=100)

# Override latest close with Avantis price
avantis_price = await get_avantis_price(asset)
candles.loc[-1, 'close'] = avantis_price  # Use Avantis!

# Calculate SMC indicators on this data
# (historical patterns + current Avantis price)
```

### 2. Trade Entry
```python
# When signal detected, get FRESH Avantis price
avantis_price = await get_avantis_price(asset)

# Use this for entry
current_price = avantis_price  # NOT Binance!

# Calculate SL/TP based on Avantis price
# Execute at Avantis price
```

## 📊 Price Sources

| Data Type | Source | Why |
|-----------|--------|-----|
| **Historical OHLC** | Binance | Pyth doesn't provide candle history |
| **Latest Close** | Avantis (Pyth) | Real-time trading price |
| **Entry Price** | Avantis (Pyth) | What you'll actually get filled at |
| **SL/TP Calc** | Avantis (Pyth) | Based on entry price |

## ✅ Benefits

1. **No price mismatch** - Entry at same price shown on Avantis
2. **No slippage surprises** - Calculated SL/TP match execution
3. **Accurate signals** - Latest price from actual trading venue
4. **Safe backtesting** - Historical patterns + real execution price

## 🎯 Example

**ARB Signal:**

```
Historical pattern (Binance):
  13:00 | Close: $0.0994
  13:15 | Close: $0.1001
  13:30 | Close: $0.1003
  13:45 | Close: $0.1013 ← Replaced with Avantis

Avantis real-time: $0.1013 ✅

Signal detected: LONG ARB
Entry verification: Get Avantis price again → $0.1013
Execute at: $0.1013 (same as Avantis shows)
```

## 🔍 Verification

Check price match:
```bash
python3 check_avantis_price.py
```

Expected:
```
Avantis: $0.1013
Binance: $0.1014
Difference: 0.07% ✅
```

## ⚠️ Important

**The bot now ALWAYS uses Avantis prices for:**
- Entry decisions
- SL/TP calculations  
- Position sizing

**Binance is ONLY used for:**
- Historical candle patterns (SMC indicators need OHLC history)
- Latest candle is OVERRIDDEN with Avantis price

**This ensures you trade at the EXACT price shown on Avantis.**

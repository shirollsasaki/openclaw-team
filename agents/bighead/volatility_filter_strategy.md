# Dynamic Volatility Filter Strategy

## Concept

Instead of trading fixed assets (ARB/OP/ETH), **automatically select and trade the top 3 most volatile assets** that meet our criteria in real-time.

## How It Works

### **1. Pre-Trade Volatility Check (Every 15 Minutes)**

Before detecting signals on any asset:

```python
async def get_tradeable_assets():
    """Select top assets based on current volatility"""
    
    volatility_scores = {}
    
    for asset in ALL_ASSETS:
        # Get last 24h of 15m candles
        df = await fetch_recent_data(asset, hours=24)
        
        # Calculate ATR (volatility)
        atr_pct = calculate_atr(df)
        
        # Filter: only assets in sweet spot (0.3-0.7% ATR)
        if 0.3 <= atr_pct <= 0.7:
            # Score = volatility * trend strength
            trend_score = calculate_trend_strength(df)
            volatility_scores[asset] = atr_pct * trend_score
    
    # Return top 3 by score
    top_assets = sorted(volatility_scores.items(), 
                       key=lambda x: x[1], 
                       reverse=True)[:3]
    
    return [asset for asset, score in top_assets]
```

### **2. Signal Detection (Only on Qualified Assets)**

```python
async def trading_loop():
    while True:
        # Get current top 3 volatile assets
        active_assets = await get_tradeable_assets()
        
        print(f"Trading: {active_assets}")  # e.g., ['ARB', 'SOL', 'ETH']
        
        # Only detect signals on these assets
        for asset in active_assets:
            df = await fetch_candles(asset, '15m')
            signal = detect_bos_signal(df)
            
            if signal and can_open_position(asset):
                execute_trade(asset, signal)
        
        await asyncio.sleep(900)  # 15 minutes
```

### **3. Position Management Rules**

**Critical:** Don't close existing profitable positions just because an asset falls out of top 3.

```python
# ✅ Good: Keep existing positions until TP/SL
if asset in active_assets or has_open_position(asset):
    check_for_signals(asset)

# ❌ Bad: Force-close positions when asset drops from top 3
# Don't do this - let trades play out naturally
```

### **4. Rebalance Frequency**

**Option A: Every 15 Minutes (Aggressive)** ⚠️
- Pros: Instantly adapts to volatility spikes
- Cons: Too much churn, whipsawing between assets
- Risk: Open ARB position, close it, switch to SOL, miss ARB TP

**Option B: Daily Rebalance (Recommended)** ✅
- Check volatility once per day at 00:00 UTC
- Trade selected assets for next 24 hours
- Existing positions stay open until TP/SL
- Reduces noise, smoother equity curve

**Option C: Hybrid (Smart)** 🎯
- Daily rebalance for primary allocation
- But allow emergency switches if volatility doubles
- Example: If BTC ATR jumps from 0.15% → 0.6%, add it immediately

---

## Volatility Scoring Formula

**Simple Version:**
```python
score = atr_pct  # Just raw volatility
```

**Better Version:**
```python
# Combine volatility + trend strength + recent profit
score = (atr_pct * trend_strength * recency_weight)

where:
- atr_pct = 14-period ATR as % of price
- trend_strength = how clean recent structure breaks are (0-1)
- recency_weight = favor assets that made us money recently (1.2x multiplier)
```

**Best Version (My Recommendation):**
```python
def calculate_asset_score(df, asset_name):
    # 1. Volatility (must be in sweet spot)
    atr_pct = calculate_atr(df, period=14)
    if not (0.3 <= atr_pct <= 0.7):
        return 0  # Disqualify
    
    # 2. Structure quality (clean BOS > choppy noise)
    bos_count = count_bos_signals(df, last_48h=True)
    structure_score = min(bos_count / 5, 1.0)  # Cap at 5 signals
    
    # 3. Recent performance bonus
    recent_pnl = get_last_7d_pnl(asset_name)
    performance_multiplier = 1.0 + (recent_pnl / 100) * 0.5
    
    # 4. Volume check (avoid illiquid assets)
    volume_rank = get_volume_rank(asset_name)
    volume_weight = 1.0 if volume_rank <= 10 else 0.8
    
    # Final score
    score = atr_pct * structure_score * performance_multiplier * volume_weight
    
    return score
```

---

## Example in Action

### **Scenario 1: ARB Stays Hot**
```
Day 1-7: ARB top scorer (0.59% ATR, clean structure)
→ Bot trades ARB + OP + ETH

Day 8: ARB still #1, OP falls to #5, SOL rises to #2
→ Rebalance: Trade ARB + SOL + ETH (drop OP)
→ But keep any open OP positions until they hit TP/SL
```

### **Scenario 2: Market Regime Change**
```
Week 1: ARB/OP/ETH trending (high vol)
→ Bot capitalizes, makes profit

Week 2: Crypto market calms down, all ATR drops
→ Filter finds NO assets in 0.3-0.7% range
→ Bot goes IDLE (no new trades, wait for volatility)
→ Existing positions close naturally

Week 3: SOL news causes spike (ATR jumps to 0.55%)
→ SOL enters top 3, bot starts trading again
```

---

## Pros & Cons

### ✅ **Advantages**

1. **Adapts to Market Conditions**
   - ARB hot today? Trade it.
   - SOL volatile tomorrow? Switch to it.

2. **Maximizes Opportunities**
   - Always trading the most active assets
   - Don't miss sudden volatility spikes

3. **Risk Management**
   - If all assets become too volatile (>0.7%), bot stops
   - If all become too calm (<0.3%), bot waits

4. **Objective Selection**
   - No bias toward "favorite" assets
   - Data-driven decisions

### ⚠️ **Disadvantages**

1. **Complexity**
   - Need to monitor 8+ assets in real-time
   - More API calls, more data processing

2. **Backtesting Harder**
   - Strategy changes over time
   - Can't replicate exact historical behavior

3. **Switching Costs**
   - If rebalancing daily, might miss multi-day trends
   - Risk of whipsawing between assets

4. **Position Management**
   - Need to track which asset each position belongs to
   - Can't just assume "all positions are ARB"

---

## Implementation Plan

### **Phase 1: Static Allocation (Proven)**
Build bot with fixed ARB + OP + ETH allocation first.
- Simpler to test
- Matches backtest exactly
- Get it working FAST

### **Phase 2: Add Volatility Monitor (Passive)**
Add daily volatility reporting:
```
Daily Report (00:00 UTC):
- ARB: 0.59% ATR (rank #1) ✅ Trading
- OP: 0.82% ATR (rank #2) ⚠️ High DD risk
- ETH: 0.17% ATR (rank #6) ⚠️ Low volatility
- SOL: 0.51% ATR (rank #3) 📈 Consider adding

Recommendation: Swap OP → SOL
```

You review manually, decide whether to switch.

### **Phase 3: Full Automation (Dynamic Filter)**
Bot auto-rebalances daily:
```python
# 00:00 UTC every day
active_assets = get_top_volatile_assets(count=3, min_atr=0.3, max_atr=0.7)
set_active_trading_pairs(active_assets)
send_discord_notification(f"Trading today: {active_assets}")
```

---

## My Recommendation

### **Start with Static (Phase 1)** ✅

**Why:**
1. Proven by backtest (ARB +87%, OP +39%, ETH +34%)
2. Simpler to build and debug
3. Get profitable FAST (tonight)
4. Validate execution quality before adding complexity

**Then Add Dynamic Filter (Phase 3) in Week 2** 🎯

Once bot is profitable and stable:
- Add daily volatility scoring
- Auto-rebalance at 00:00 UTC
- Keep top 3 assets active
- Discord notification on changes

### **Hybrid Approach (Best of Both)**

```python
# Primary allocation (static, proven)
PRIMARY_ASSETS = ['ARB', 'ETH']  # Safe core

# Dynamic slot (1 asset selected daily)
dynamic_asset = get_highest_volatility_asset(
    exclude=['ARB', 'ETH'],
    min_atr=0.4,
    max_atr=0.8
)

ACTIVE_ASSETS = PRIMARY_ASSETS + [dynamic_asset]
# Result: ARB + ETH (stable) + [SOL or OP or LINK] (rotating)
```

This gives you:
- ✅ Stability (ARB/ETH proven)
- ✅ Adaptability (1 slot rotates to hottest asset)
- ✅ Simplicity (only 1 dynamic decision)

---

## Bottom Line

**Your instinct is correct — volatility filter is powerful.**

**But for tonight:**
- Build static ARB + ETH bot (proven, fast)
- Get it profitable first
- Add dynamic filter next week once core is stable

**Long-term (Week 2+):**
- Implement daily volatility rebalancing
- Top 3 assets auto-selected at 00:00 UTC
- Discord notifications on changes
- Much more adaptive to market conditions

Sound good?

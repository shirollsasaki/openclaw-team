# 📊 TIMEFRAME COMPARISON TEST - V2+Squeeze

**Started:** 2026-02-22 14:34  
**Purpose:** Find optimal timeframe for V2+Squeeze strategy  
**Duration:** Run for 24-48 hours to collect data

---

## 🎯 TEST SETUP

```
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║  🔴 15m (LIVE) - PID 15482                                        ║
║     Mode: LIVE TRADING (real money)                              ║
║     Check: Every 60 seconds                                      ║
║     Capital: $30 USDC                                            ║
║                                                                   ║
║  📊 5m (SIMULATION) - PID 15988                                   ║
║     Mode: Simulation (testing)                                   ║
║     Check: Every 30 seconds                                      ║
║     Capital: $30 virtual                                         ║
║                                                                   ║
║  📊 1m (SIMULATION) - PID 15990                                   ║
║     Mode: Simulation (testing)                                   ║
║     Check: Every 15 seconds                                      ║
║     Capital: $30 virtual                                         ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## ⚙️ CONFIGURATION

All three bots use **IDENTICAL** strategy settings:

```python
Strategy: V2 + Squeeze Momentum Filter
Leverage: 15x
Risk: 3% per trade
RR Ratio: 2:1

Filters:
├─ Volume: 1.5x average minimum
├─ Trend: Must be aligned
└─ Squeeze: Must be OFF (breakout only)

Features:
├─ Breakeven stops at 50% to TP
├─ Partial profits at 50% to TP
├─ Trailing SL (1% activation, 0.5% trail)
└─ Position limits: 10 total, 6 per direction
```

**ONLY difference:** Timeframe & check interval

---

## 🔍 WHAT WE'RE TESTING

### **Hypothesis:**

**Shorter timeframes might:**
- ✅ Catch more signals (more trades)
- ✅ Faster reaction to squeeze releases
- ✅ Better entry/exit timing
- ❌ More noise/false signals
- ❌ More gas fees (if used live)

**Longer timeframes might:**
- ✅ Higher quality signals
- ✅ Less noise/whipsaw
- ✅ Fewer gas fees
- ❌ Fewer opportunities
- ❌ Slower to react

---

## 📊 TIMEFRAME DETAILS

### **15m (Current LIVE)**
```
Timeframe: 15 minutes
Check interval: Every 60 seconds
Candles: 100 x 15m = 25 hours of data
Trade frequency: Expected 1-2/day
Gas cost: ~$1.50 per trade (on-chain SL/TP updates)

Pros:
├─ Proven in backtesting
├─ Clean signals
└─ Lower gas costs (fewer trades)

Cons:
├─ Slower to react
└─ Fewer opportunities
```

---

### **5m (NEW - Simulation)**
```
Timeframe: 5 minutes
Check interval: Every 30 seconds
Candles: 100 x 5m = ~8 hours of data
Trade frequency: Expected 2-4/day
Gas cost: ~$1.50 per trade (if live)

Pros:
├─ 3x more data points vs 15m
├─ Faster reaction to breakouts
└─ More trading opportunities

Cons:
├─ More noise/false signals?
├─ More frequent checks (CPU)
└─ More gas costs (if live)
```

---

### **1m (NEW - Simulation)**
```
Timeframe: 1 minute
Check interval: Every 15 seconds
Candles: 100 x 1m = ~1.7 hours of data
Trade frequency: Expected 5-10/day
Gas cost: ~$1.50 per trade (if live)

Pros:
├─ Most data points
├─ Fastest reaction
└─ Maximum opportunities

Cons:
├─ Most noise/whipsaw
├─ Highest gas costs (if live)
├─ Most CPU usage
└─ May overtrade
```

---

## 🎯 SUCCESS METRICS

**We'll compare after 24-48 hours:**

| Metric | Why It Matters |
|--------|----------------|
| **Total P&L** | Which makes most money? |
| **Win Rate** | Which has better quality signals? |
| **Trade Frequency** | How many opportunities? |
| **Risk/Reward** | Which has best avg R:R? |
| **Max Drawdown** | Which is safest? |
| **Time in Market** | Which is most efficient? |

---

## 📊 MONITORING

### **Quick Check:**
```bash
python3 compare_timeframes.py
```

**Shows:**
- Current P&L for each timeframe
- Open positions
- Total trades
- Win rate
- Leaderboard

---

### **Detailed Logs:**

**15m (LIVE):**
```bash
tail -f strategy1_v2_squeeze.log
```

**5m (Simulation):**
```bash
tail -f strategy1_v2_squeeze_5m.log
```

**1m (Simulation):**
```bash
tail -f strategy1_v2_squeeze_1m.log
```

---

### **Process Status:**
```bash
ps aux | grep "avantis_bot_v2_squeeze" | grep -v grep
```

**Should show:**
- 15482: 15m LIVE ✅
- 15988: 5m Simulation ✅
- 15990: 1m Simulation ✅

---

## 🔴 IMPORTANT NOTES

### **1. Only 15m is LIVE**
```
LIVE:       15m (PID 15482) - Real $30 USDC ✅
Simulation: 5m (PID 15988) - Virtual only 📊
Simulation: 1m (PID 15990) - Virtual only 📊
```

**Don't worry about 5m/1m trades** - they're not real money!

---

### **2. All Use Same Filters**

All three have the **Squeeze filter** enabled:
- Only trades when squeeze releases
- Very selective
- Could take hours for first signal

**Expected behavior:**
- 15m: 1-2 trades/day
- 5m: 2-4 trades/day
- 1m: 5-10 trades/day

*(If markets cooperate and squeeze releases happen)*

---

### **3. Memory Warning**

Your Mac is low on RAM. Running 3 more bots might cause crashes.

**If bots crash frequently:**
```bash
# Stop old simulation bots
pkill -f "avantis_bot.py"      # V1
pkill -f "avantis_bot_v2.py"   # V2 Enhanced
pkill -f "all3.py"              # V2+All3

# Keep these running:
# - 15m LIVE (15482)
# - 5m Sim (15988)
# - 1m Sim (15990)
```

---

## 📈 EXPECTED TIMELINE

### **Hour 1-2:**
- All bots monitoring
- Likely 0 trades (squeeze filter selective)
- Just collecting data

### **Hour 3-6:**
- 1m likely to get first signals (more frequent checks)
- 5m might catch a few
- 15m waiting for clean setup

### **Hour 12-24:**
- Enough data to compare
- Can see trade frequency differences
- Win rate patterns emerge

### **Hour 24-48:**
- Clear winner should emerge
- Can make confident decision
- Switch LIVE bot to best timeframe

---

## 🎯 DECISION CRITERIA

**After 24-48 hours, we'll choose LIVE timeframe based on:**

### **If 1m wins:**
```
Pros: Most signals, fastest reaction
Cons: Higher gas costs, more CPU
Decision: Switch LIVE to 1m if ROI > 2x gas costs
```

### **If 5m wins:**
```
Pros: Good balance of speed + quality
Cons: More gas than 15m
Decision: Switch LIVE to 5m if ROI > 1.5x gas costs
```

### **If 15m wins:**
```
Pros: Cleanest signals, lowest gas
Cons: Fewer opportunities
Decision: Keep LIVE on 15m (current setup)
```

---

## 🔧 FILES CREATED

```
New Bot Files:
├── avantis_bot_v2_squeeze_5m.py    (5m timeframe)
├── avantis_bot_v2_squeeze_1m.py    (1m timeframe)

Logs:
├── strategy1_v2_squeeze.log        (15m LIVE)
├── strategy1_v2_squeeze_5m.log     (5m Sim)
├── strategy1_v2_squeeze_1m.log     (1m Sim)

Monitoring:
├── compare_timeframes.py           (Comparison script)
└── TIMEFRAME_TEST_SETUP.md         (This file)
```

---

## 🚀 NEXT STEPS

**Now:**
1. ✅ All 3 bots running
2. ✅ Monitoring in place
3. ⏳ Waiting for signals

**In 6 hours:**
```bash
python3 compare_timeframes.py
```
- Check which has traded
- See early performance

**In 24 hours:**
```bash
python3 compare_timeframes.py
```
- Full comparison
- Identify best performer
- Make decision

**In 48 hours:**
- Confirm winner is consistent
- Switch LIVE bot to best timeframe
- Stop other simulations

---

## 💡 TIPS

**Don't expect instant results:**
- Squeeze filter is very selective
- Could be hours before ANY trades
- Need patience to collect data

**Check periodically:**
```bash
# Quick status every few hours
python3 compare_timeframes.py

# Watch for first trade
tail -f strategy1_v2_squeeze_*.log
```

**If bots crash:**
```bash
# Restart all 3
bash STOP_LIVE_BOT.sh
python3 avantis_bot_v2_squeeze.py &    # 15m LIVE
python3 avantis_bot_v2_squeeze_5m.py & # 5m Sim
python3 avantis_bot_v2_squeeze_1m.py & # 1m Sim
```

---

## ✅ SUMMARY

```
Test Running:
├─ 15m LIVE: PID 15482 ✅
├─ 5m Sim: PID 15988 ✅
└─ 1m Sim: PID 15990 ✅

Goal: Find optimal timeframe
Method: Run 24-48 hours, compare results
Winner: Highest ROI with acceptable trade frequency

Monitor: python3 compare_timeframes.py
Status: ⏳ Collecting data...
```

---

**Timeframe test is LIVE!** Check back in 6-24 hours for comparison data. 🚀📊

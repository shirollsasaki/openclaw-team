# Run All Strategy Versions Side-by-Side

**Quick reference for running V1, V2, and V2+Squeeze in parallel**

---

## 🚀 Start All Three

### **Terminal 1: V1 (Baseline)**
```bash
cd $OPENCLAW_HOME/bighead
python3 avantis_bot.py
```
- **File:** `avantis_bot.py`
- **Log:** `strategy1_bot.log`
- **Trades:** `strategy1_trades.csv`
- **Features:** Basic SMC, no filters
- **Expected:** ~20 trades/week

---

### **Terminal 2: V2 (Enhanced)**
```bash
cd $OPENCLAW_HOME/bighead
python3 avantis_bot_v2.py
```
- **File:** `avantis_bot_v2.py`
- **Log:** `strategy1_v2.log`
- **Trades:** `strategy1_v2_trades.csv`
- **Features:** Breakeven + Partial + Trailing + Volume + Trend
- **Expected:** ~17 trades/week

---

### **Terminal 3: V2 + Squeeze (Most Selective)**
```bash
cd $OPENCLAW_HOME/bighead
python3 avantis_bot_v2_squeeze.py
```
- **File:** `avantis_bot_v2_squeeze.py`
- **Log:** `strategy1_v2_squeeze.log`
- **Trades:** `strategy1_v2_squeeze_trades.csv`
- **Features:** All V2 features + Squeeze Momentum filter
- **Expected:** ~13 trades/week

---

## 📊 Monitor All Three

### **Watch Logs:**

```bash
# V1
tail -f strategy1_bot.log

# V2
tail -f strategy1_v2.log

# V2 + Squeeze
tail -f strategy1_v2_squeeze.log
```

### **Quick Status Check:**

```bash
# See latest status for all
tail -20 strategy1_bot.log | grep "Equity:"
tail -20 strategy1_v2.log | grep "Equity:"
tail -20 strategy1_v2_squeeze.log | grep "Equity:"
```

### **Check What's Running:**

```bash
ps aux | grep "avantis_bot" | grep -v grep
```

---

## 🛑 Stop All

```bash
pkill -f "avantis_bot"
```

**Or individually:**
```bash
# Find PIDs
ps aux | grep "avantis_bot"

# Kill specific
kill <PID>
```

---

## 📈 Compare Performance (After 24h)

### **Get Final Results:**

```bash
# V1 trades
wc -l strategy1_trades.csv
tail -1 strategy1_bot.log | grep "Realized"

# V2 trades
wc -l strategy1_v2_trades.csv
tail -1 strategy1_v2.log | grep "Realized"

# V2 + Squeeze trades
wc -l strategy1_v2_squeeze_trades.csv
tail -1 strategy1_v2_squeeze.log | grep "Realized"
```

### **Comparison Template:**

| Metric | V1 | V2 | V2+Squeeze | Winner |
|--------|----|----|------------|--------|
| **Trades** | ? | ? | ? | ? |
| **Win Rate** | ? | ? | ? | ? |
| **Total P&L** | ? | ? | ? | ? |
| **Max DD** | ? | ? | ? | ? |

**Fill in after 24 hours, deploy the winner.**

---

## 🎯 What to Expect

### **V1 (Baseline):**
- Fastest to open positions
- Takes all SMC signals
- No filters = more trades
- Higher noise/false signals

### **V2 (Enhanced):**
- Opens positions selectively
- Volume + trend filters
- Breakeven protection saves trades
- Partial profits lock gains

### **V2 + Squeeze (Most Selective):**
- Slowest to open (most selective)
- Waits for squeeze-off breakouts
- Highest quality signals
- Fewest trades but best win rate

**Remember:** Fewer trades ≠ worse. Quality > Quantity.

---

## 💡 Tips

1. **Let all 3 run for at least 24 hours**
2. **Don't judge on first 2-3 trades** (sample size too small)
3. **Check win rate AND total P&L** (both matter)
4. **Notice which hits breakeven/partials** (V2 advantages)
5. **See which avoids false breakouts** (Squeeze advantage)

---

## 🎉 Deployment Decision

**After 24-48 hours:**

**If V1 wins:** Simplicity works, deploy V1 live  
**If V2 wins:** Risk management matters, deploy V2 live  
**If V2+Squeeze wins:** Quality beats quantity, deploy V2+Squeeze live  

**Then scale capital gradually.**

---

**Ready to start?** Just copy the commands above into 3 terminals! 🚀

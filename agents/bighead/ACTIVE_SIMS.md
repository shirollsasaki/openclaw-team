# Active Simulations - Status

**Last Updated:** 2026-02-21 3:05 PM

---

## 🟢 Currently Running

### **Strategy 1 V1 (Original)**
- **PID:** Check with `ps aux | grep avantis_bot.py`
- **Started:** 3:05 PM (just restarted)
- **Log File:** `strategy1_bot.log`
- **Output:** `v1_output.log`
- **Features:** Basic SMC, no filters, max 6 positions

### **Strategy 1 V2 (Enhanced)**
- **PID:** 6596
- **Started:** 2:59 PM
- **Log File:** `strategy1_v2.log`
- **Output:** `v2_output.log`
- **Features:** 11 improvements including trailing SL, breakeven, partial profits

### **Discord Monitor**
- **PID:** 6598
- **Started:** 2:59 PM
- **Log File:** `monitor.log`
- **Posts:** Every 5 minutes to Discord

---

## 📊 How to View Logs

### **Watch V1 in Real-Time:**
```bash
tail -f $OPENCLAW_HOME/bighead/strategy1_bot.log
```

### **Watch V2 in Real-Time:**
```bash
tail -f $OPENCLAW_HOME/bighead/strategy1_v2.log
```

### **See Latest V1 Status:**
```bash
tail -30 strategy1_bot.log | grep -A 20 "===="
```

### **See Latest V2 Status:**
```bash
tail -30 strategy1_v2.log | grep -A 20 "===="
```

### **Check What's Running:**
```bash
ps aux | grep -i python3 | grep -E "avantis|monitor" | grep -v grep
```

### **Stop Everything:**
```bash
pkill -f "avantis_bot"
pkill -f "monitor_bots"
```

### **Restart V1:**
```bash
cd $OPENCLAW_HOME/bighead
python3 avantis_bot.py > v1_output.log 2>&1 &
```

### **Restart V2:**
```bash
cd $OPENCLAW_HOME/bighead
python3 avantis_bot_v2.py > v2_output.log 2>&1 &
```

---

## 📁 Log File Locations

All logs in: `$OPENCLAW_HOME/bighead/`

```
strategy1_bot.log       # V1 detailed logs
strategy1_v2.log        # V2 detailed logs
strategy1_trades.csv    # V1 closed trades
strategy1_v2_trades.csv # V2 closed trades
monitor.log             # Monitor output
v1_output.log           # V1 stdout/stderr
v2_output.log           # V2 stdout/stderr
```

---

## 🎯 Quick Status Check

```bash
# Current positions V1
tail -20 strategy1_bot.log | grep -E "Open:|Unrealized:"

# Current positions V2
tail -20 strategy1_v2.log | grep -E "Open:|Unrealized:"

# Check if processes are alive
ps aux | grep -E "avantis_bot|monitor_bots" | grep -v grep
```

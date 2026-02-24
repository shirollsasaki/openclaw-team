# 🚀 How to Run 1Delta Strategy in Simulation

**Quick Reference:** Run, monitor, and control the 1Delta dynamic leverage bot

---

## ✅ CURRENTLY RUNNING

```
Status: 🟢 Already Running!
PID: 16400
Mode: 📊 SIMULATION
File: avantis_bot_v2_squeeze_1delta.py
Log: strategy1_v2_squeeze_1delta.log
```

---

## 📊 CHECK IF RUNNING

```bash
ps aux | grep avantis_bot_v2_squeeze_1delta.py | grep -v grep
```

**If running, you'll see:**
```
youruser  16400  ... avantis_bot_v2_squeeze_1delta.py
```

**If nothing shows up:** Bot is not running (start it)

---

## 🚀 START THE BOT

### **Method 1: Simple Start**

```bash
cd $OPENCLAW_HOME/bighead
python3 avantis_bot_v2_squeeze_1delta.py &
```

**Note:** Use `&` at the end to run in background

---

### **Method 2: With nohup (Recommended)**

```bash
cd $OPENCLAW_HOME/bighead
nohup python3 avantis_bot_v2_squeeze_1delta.py > /dev/null 2>&1 &
echo "Bot started! PID: $!"
```

**Advantage:** Bot keeps running even if terminal closes

---

### **Method 3: Save PID for Easy Management**

```bash
cd $OPENCLAW_HOME/bighead
nohup python3 avantis_bot_v2_squeeze_1delta.py > /dev/null 2>&1 &
echo $! > .bot_1delta_pid
echo "Bot started! PID: $(cat .bot_1delta_pid)"
```

**Then you can stop it easily:**
```bash
kill $(cat .bot_1delta_pid)
```

---

## 🛑 STOP THE BOT

### **Method 1: If You Know PID**

```bash
kill 16400  # Replace with actual PID
```

---

### **Method 2: Find and Kill**

```bash
pkill -f avantis_bot_v2_squeeze_1delta.py
```

---

### **Method 3: Force Kill (If Stuck)**

```bash
pkill -9 -f avantis_bot_v2_squeeze_1delta.py
```

---

## 🔄 RESTART THE BOT

```bash
# Stop it
pkill -f avantis_bot_v2_squeeze_1delta.py

# Wait 2 seconds
sleep 2

# Start it
cd $OPENCLAW_HOME/bighead
nohup python3 avantis_bot_v2_squeeze_1delta.py > /dev/null 2>&1 &
echo "Bot restarted! PID: $!"
```

---

## 📊 MONITOR THE BOT

### **Watch Live Log (Real-time):**

```bash
tail -f $OPENCLAW_HOME/bighead/strategy1_v2_squeeze_1delta.log
```

**Press Ctrl+C to stop watching**

---

### **See Last 50 Lines:**

```bash
tail -50 $OPENCLAW_HOME/bighead/strategy1_v2_squeeze_1delta.log
```

---

### **See Last 100 Lines:**

```bash
tail -100 $OPENCLAW_HOME/bighead/strategy1_v2_squeeze_1delta.log
```

---

### **Search for Specific Events:**

**See all signal scores:**
```bash
grep "Signal Score" $OPENCLAW_HOME/bighead/strategy1_v2_squeeze_1delta.log
```

**See leverage decisions:**
```bash
grep "1delta Leverage" $OPENCLAW_HOME/bighead/strategy1_v2_squeeze_1delta.log
```

**See position sizes:**
```bash
grep "Position size" $OPENCLAW_HOME/bighead/strategy1_v2_squeeze_1delta.log
```

**See health factor checks:**
```bash
grep "Health Factor" $OPENCLAW_HOME/bighead/strategy1_v2_squeeze_1delta.log
```

---

## ✅ VERIFY IT'S IN SIMULATION MODE

```bash
grep "SIMULATION_MODE" $OPENCLAW_HOME/bighead/avantis_bot_v2_squeeze_1delta.py | head -1
```

**Should show:**
```python
SIMULATION_MODE = True  # ⚠️ SIMULATION
```

**If you see `False`:** It's in LIVE mode! ⚠️

---

## 🎯 WHAT YOU'LL SEE

### **On Startup:**

```
[INFO] Starting Strategy 1 V2 + Squeeze + 1Delta
[INFO] ======================================================================
[INFO] Strategy 1 V2 + Squeeze + 1Delta
[INFO] ======================================================================
[INFO] V2 Improvements:
[INFO]   ✅ Breakeven stops at 50.0% to TP
[INFO]   ✅ Partial profits at 50.0% to TP
[INFO]   ✅ Trailing SL: activates at 1.0%, trails 0.5%
[INFO]   ✅ Position limits: 10 total
[INFO]   ✅ Squeeze Momentum filter: ENABLED
[INFO] 
[INFO] 1Delta Dynamic Leverage:
[INFO]   💰 Enabled: True
[INFO]   📊 Score-based leverage (max 3.0x)
[INFO]   🛡️  Min health factor: 1.5
[INFO]   ⚠️  Auto-deleverage at: 1.3
[INFO]   🎯 Signal scoring: Volume, Trend, Squeeze, Momentum, Market
[INFO] ======================================================================
```

---

### **Every 60 Seconds (Status Update):**

```
[INFO] ==============================================================================================================
[INFO] Equity: $30.00 | Unrealized: $+0.00 | Total: $30.00 | Open: 0 (L:0/S:0) | Realized: $+0.00 | Losses: 0
[INFO] ==============================================================================================================
[INFO] No open positions
[INFO] ==============================================================================================================
```

---

### **When Signal Appears:**

```
[INFO] Signal detected: SHORT ARB

[INFO]    📊 Signal Score: 78.5/100
[INFO]       Volume: 22/25 | Trend: 16/20 | Squeeze: 25/30
[INFO]       Momentum: 12/15 | Market: 7/10

[INFO]    🎯 Signal Confidence: HIGH
[INFO]    💰 1delta Leverage: 2.0x
[INFO]    📊 Position Multiplier: 1.67x
[INFO]    💵 Max Position Size: $10.00

[INFO]    🔧 Setting up 2.0x leverage on 1delta...
[INFO]    ⚠️  SIMULATION: Would setup 2.0x leverage on 1delta
[INFO]       Collateral: $30.00 ETH
[INFO]       Borrow: $30.00 USDC
[INFO]       Gas cost: ~$5.00

[INFO]    💵 Position size: $10.00 (from $60.00 leveraged capital)
[INFO]    🛡️  Max loss: $45.00 (safe with $60.00)

[INFO]    ⚠️  SIMULATION MODE - Trade not executed on Avantis
```

---

## 🔍 TROUBLESHOOTING

### **Bot Not Logging Anything:**

```bash
# Check if process is alive
ps aux | grep avantis_bot_v2_squeeze_1delta.py

# Check for errors
tail -100 $OPENCLAW_HOME/bighead/strategy1_v2_squeeze_1delta.log

# Try restarting
pkill -f avantis_bot_v2_squeeze_1delta.py
sleep 2
python3 avantis_bot_v2_squeeze_1delta.py &
```

---

### **Can't Find Log File:**

```bash
# List all log files
ls -lh $OPENCLAW_HOME/bighead/*.log

# Create if missing
cd $OPENCLAW_HOME/bighead
python3 avantis_bot_v2_squeeze_1delta.py &
```

---

### **Bot Keeps Crashing:**

```bash
# Run in foreground to see errors
cd $OPENCLAW_HOME/bighead
python3 avantis_bot_v2_squeeze_1delta.py

# Watch for error messages
```

---

## 📁 QUICK COMMANDS CHEAT SHEET

```bash
# START
cd $OPENCLAW_HOME/bighead && python3 avantis_bot_v2_squeeze_1delta.py &

# STOP
pkill -f avantis_bot_v2_squeeze_1delta.py

# CHECK IF RUNNING
ps aux | grep avantis_bot_v2_squeeze_1delta.py | grep -v grep

# WATCH LIVE
tail -f strategy1_v2_squeeze_1delta.log

# SEE RECENT ACTIVITY
tail -50 strategy1_v2_squeeze_1delta.log

# FIND SIGNALS
grep "Signal Score" strategy1_v2_squeeze_1delta.log

# VERIFY SIMULATION MODE
grep "SIMULATION_MODE" avantis_bot_v2_squeeze_1delta.py | head -1
```

---

## 🎯 CURRENT STATUS

```bash
# Check everything at once
echo "=== 1DELTA BOT STATUS ==="
echo ""
echo "Running:"
ps aux | grep avantis_bot_v2_squeeze_1delta.py | grep -v grep || echo "  ❌ Not running"
echo ""
echo "Mode:"
grep "SIMULATION_MODE" $OPENCLAW_HOME/bighead/avantis_bot_v2_squeeze_1delta.py | head -1
echo ""
echo "Last 5 log lines:"
tail -5 $OPENCLAW_HOME/bighead/strategy1_v2_squeeze_1delta.log
```

---

## ✅ YOUR BOT RIGHT NOW

```
Status: 🟢 RUNNING
PID: 16400
Mode: 📊 SIMULATION
Log: strategy1_v2_squeeze_1delta.log

To watch live:
tail -f $OPENCLAW_HOME/bighead/strategy1_v2_squeeze_1delta.log

To stop:
kill 16400
or
pkill -f avantis_bot_v2_squeeze_1delta.py
```

---

**Your 1Delta bot is already running in simulation!** ✅

Just use `tail -f strategy1_v2_squeeze_1delta.log` to watch it work! 📊

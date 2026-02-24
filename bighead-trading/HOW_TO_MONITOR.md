# 📊 How to Monitor Your Live Bot

**Bot Status:** 🟢 Running (PID 14703)  
**Current Time:** 2026-02-22 13:11

---

## 🎯 QUICK MONITORING COMMANDS

### **1. Check If Bot Is Running**
```bash
ps aux | grep avantis_bot_v2_squeeze.py | grep -v grep
```

**You should see:**
```
youruser  14703  ... avantis_bot_v2_squeeze.py
```

✅ **Your bot IS running!**

---

### **2. Watch Live Log (Real-time)**
```bash
tail -f strategy1_v2_squeeze.log
```

**This shows:**
- Every signal detected
- Filters passing/failing
- Trades opened/closed
- P&L updates
- Position status

**Press Ctrl+C to stop watching**

---

### **3. See Last 50 Lines**
```bash
tail -50 strategy1_v2_squeeze.log
```

**Quick snapshot of recent activity**

---

### **4. Search for Specific Events**
```bash
# See all trades
grep "OPENED\|CLOSED" strategy1_v2_squeeze.log | tail -20

# See current equity
grep "Equity:" strategy1_v2_squeeze.log | tail -5

# See filters working
grep "Skipped" strategy1_v2_squeeze.log | tail -10
```

---

## 📊 CURRENT STATUS CHECK

Run this to see current state:

```bash
python3 check_bots_now.py
```

**Shows:**
- Current equity
- Open positions
- Total P&L
- Last update time

---

## 🔍 WHAT TO LOOK FOR

### **Bot is Working If You See:**

```
[INFO] Fetched ARB/USD index: 4
[INFO] Fetched OP/USD index: 7
[INFO] Fetched ETH/USD index: 0
[INFO] Equity: $30.00 | Unrealized: $+0.00 | Total: $30.00
```

### **Signal Detection:**
```
[INFO] Signal detected: SHORT ARB
[INFO]    Volume: 2.3x ✅
[INFO]    Trend: Aligned ✅
[INFO]    Squeeze: OFF ✅
```

### **Filters Working:**
```
[INFO]    Skipped ARB: Low volume (0.32x)
[INFO]    Skipped OP: Squeeze not OFF
```

### **Live Trade Execution:**
```
[TRADE] 🔴 EXECUTING LIVE TRADE ON AVANTIS
[TRADE] OPENED SHORT ARB @ $0.0964
[TRADE] ✅ LIVE TRADE EXECUTED: 0x1234...
```

---

## 📱 MONITORING OPTIONS

### **Option 1: Terminal (Real-time)**
```bash
tail -f strategy1_v2_squeeze.log
```

**Pros:**
- Real-time updates
- See everything
- Most detailed

**Cons:**
- Terminal must stay open
- Can be overwhelming

---

### **Option 2: Discord (Every 5 min)**

Discord bot is running (PID 10908)

**You get:**
```
🔴 LIVE TRADING UPDATE

V2+Squeeze: $32.50 (+$2.50 / +8.3%)
Positions: 1 open (SHORT ARB)
Last trade: +$1.20 (TP hit)
```

**Pros:**
- Automatic
- Mobile notifications
- Clean summary

**Cons:**
- 5-minute delay
- Less detail

---

### **Option 3: Quick Check (On-demand)**
```bash
python3 check_bots_now.py
```

**Pros:**
- Instant snapshot
- Easy to understand
- No need to watch

**Cons:**
- Manual (you have to run it)
- Point-in-time only

---

### **Option 4: Web (Avantis Dashboard)**

https://avantisfi.com

**Shows:**
- Live positions
- Real-time P&L
- Transaction history
- Official Avantis data

**Pros:**
- Official source
- Visual interface
- Mobile friendly

**Cons:**
- Need to open browser
- Connect wallet each time

---

## 🎯 RECOMMENDED MONITORING SETUP

### **For Active Monitoring:**
```bash
# Terminal 1: Watch logs
tail -f strategy1_v2_squeeze.log

# Terminal 2: Quick checks
watch -n 30 "python3 check_bots_now.py"
```

### **For Passive Monitoring:**
- Discord notifications (every 5 min)
- Check Avantis once per day
- Run `check_bots_now.py` when you're curious

---

## 📊 LOG FILE LOCATIONS

```bash
# Current live log
strategy1_v2_squeeze.log          (234 KB, actively updating)

# Trade history CSV
strategy1_v2_squeeze_trades.csv   (All closed trades)

# Other simulation bots still running
strategy1_bot.log                 (V1)
strategy1_v2.log                  (V2)
strategy1_v2_squeeze_all3.log     (V2+All3)
```

**Your live bot writes to:** `strategy1_v2_squeeze.log`

---

## 🔍 EXAMPLE: WATCH LIVE

Open terminal and run:
```bash
cd $OPENCLAW_HOME/bighead
tail -f strategy1_v2_squeeze.log
```

**You'll see updates every 60 seconds:**
```
[2026-02-22 13:12:34] [INFO] ==========================================
[2026-02-22 13:12:34] [INFO] Equity: $30.00 | Unrealized: $+0.00
[2026-02-22 13:12:34] [INFO] Total: $30.00 | Open: 0 (L:0/S:0)
[2026-02-22 13:12:34] [INFO] Realized: $+0.00 | Losses: 0
[2026-02-22 13:12:34] [INFO] ==========================================
[2026-02-22 13:12:34] [INFO] No open positions
```

**When a signal appears:**
```
[2026-02-22 13:15:42] [INFO] Signal detected: SHORT ARB
[2026-02-22 13:15:42] [INFO]    Volume: 2.1x ✅
[2026-02-22 13:15:42] [INFO]    Trend: Bearish (aligned) ✅
[2026-02-22 13:15:42] [INFO]    Squeeze: OFF ✅
[2026-02-22 13:15:42] [INFO]    Momentum: -0.0023 (aligned) ✅
[2026-02-22 13:15:42] [TRADE] 🔴 EXECUTING LIVE TRADE ON AVANTIS
[2026-02-22 13:15:45] [TRADE] ✅ LIVE TRADE EXECUTED: 0x1234...
```

---

## 🚨 WARNING SIGNS TO WATCH FOR

### **Bot Issues:**
```
[ERROR] Failed to fetch price
[ERROR] Connection timeout
```
→ Check internet, Avantis API status

### **Risk Issues:**
```
[INFO] Consecutive losses: 3
[INFO] Daily loss: -$2.85 (close to limit)
```
→ Bot will auto-stop at limits

### **Unexpected:**
```
[TRADE] OPENED LONG ARB @ $...  (when you expected SHORT)
```
→ Review what's happening

---

## 📱 MOBILE MONITORING

**Best option: Discord**

1. Install Discord app
2. Enable notifications for your channel
3. Get updates every 5 minutes
4. Check Avantis.com on mobile browser when needed

---

## ✅ MONITORING CHECKLIST

Daily:
- [ ] Check Discord for updates
- [ ] Run `check_bots_now.py` once
- [ ] Visit Avantis.com to verify positions

When trades happen:
- [ ] Watch log for entry/exit
- [ ] Verify on Avantis dashboard
- [ ] Check P&L matches expectations

If concerned:
- [ ] `tail -f strategy1_v2_squeeze.log`
- [ ] Look for errors or warnings
- [ ] Consider stopping if needed

---

## 🎯 COMMANDS SUMMARY

```bash
# Is bot running?
ps aux | grep 14703

# Watch live
tail -f strategy1_v2_squeeze.log

# Quick check
python3 check_bots_now.py

# See trades only
grep "OPENED\|CLOSED" strategy1_v2_squeeze.log | tail -20

# Current equity
grep "Equity:" strategy1_v2_squeeze.log | tail -1

# Stop bot
kill 14703

# Close all positions
python3 EMERGENCY_CLOSE_ALL.py
```

---

## 📊 YOUR BOT RIGHT NOW

**Status:** 🟢 Running  
**PID:** 14703  
**Log:** strategy1_v2_squeeze.log  
**Discord:** Active (updates every 5 min)  
**Mode:** 🔴 LIVE TRADING  

**Best way to watch:** `tail -f strategy1_v2_squeeze.log`

---

**Save this guide!** You'll reference it often. 📱

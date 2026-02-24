# 🤖 Bot Monitoring - Complete Setup

**All 4 bots are now being monitored!**

---

## ✅ Current Status (as of 23:53)

All 4 bots are **running successfully:**

| Bot | Status | Equity | P&L | Positions |
|-----|--------|--------|-----|-----------|
| **V1 Baseline** | 🟢 RUNNING | $30.00 | $0.00 (+0.0%) | 0 open |
| **V2 Enhanced** | 🟢 RUNNING | $30.00 | $0.00 (+0.0%) | 0 open |
| **V2+Squeeze** | 🟢 RUNNING | $30.00 | $0.00 (+0.0%) | 0 open |
| **V2+Sq+All3** | 🟢 RUNNING | $30.00 | $0.00 (+0.0%) | 0 open |

**All bots:**
- ✅ Using official Avantis SDK patterns
- ✅ Monitoring markets for signals
- ✅ Will trade when setups appear
- ✅ Logs are being written

---

## 📊 Monitoring Tools Created

### **1. Quick Status Check** (Instant)
```bash
cd $OPENCLAW_HOME/bighead
python3 check_bots_now.py
```

**Shows:**
- Current equity and P&L for each bot
- Open positions
- Last update time
- Leaderboard sorted by performance

---

### **2. Continuous Console Monitor** (Terminal)
```bash
cd $OPENCLAW_HOME/bighead
bash watch_bots.sh
```

**Features:**
- Updates every 60 seconds
- Clears screen and shows fresh data
- Runs until you press Ctrl+C
- Perfect for keeping open in a terminal

---

### **3. Discord Updates** (Background) ✅ RUNNING
```bash
# Already running in background (PID: 10908)
# Check status:
ps aux | grep discord_bot_updates
```

**Features:**
- Sends update to Discord every 5 minutes
- Shows all bot stats
- Leaderboard comparison
- Automatic - no interaction needed

**To stop:**
```bash
pkill -f discord_bot_updates
```

---

### **4. Advanced Monitor** (Full-featured)
```bash
cd $OPENCLAW_HOME/bighead
python3 monitor_all_bots.py
```

**Features:**
- Tracks signals, trades opened/closed, win rate
- Detailed statistics
- Discord notifications
- 5-minute update interval

---

## 📁 Log Files (Real-time)

All bots are writing logs:

| Bot | Log File | Size |
|-----|----------|------|
| V1 | `strategy1_bot.log` | ~1.2 MB (10,651 lines) |
| V2 | `strategy1_v2.log` | ~410 KB (3,161 lines) |
| V2+Squeeze | `strategy1_v2_squeeze.log` | ~16 KB (168 lines) |
| V2+Sq+All3 | `strategy1_v2_squeeze_all3.log` | ~17 KB (189 lines) |

**Tail logs in real-time:**
```bash
# V1
tail -f strategy1_bot.log

# V2
tail -f strategy1_v2.log

# V2+Squeeze
tail -f strategy1_v2_squeeze.log

# V2+Sq+All3
tail -f strategy1_v2_squeeze_all3.log
```

---

## 🔔 Discord Notifications

**Current setup:**
- ✅ Discord bot monitor running (PID: 10908)
- 📢 Sends updates every 5 minutes
- 🔗 Using webhook from .env

**What you'll receive:**
```
🤖 BOT UPDATE - 23:55:00

🟢 📊 V1 Baseline
  💰 $30.00 ➡️ +0.00 (+0.0%)

🟢 📈 V2 Enhanced
  💰 $30.00 ➡️ +0.00 (+0.0%)

🟢 🎯 V2+Squeeze
  💰 $30.00 ➡️ +0.00 (+0.0%)

🟢 ⭐ V2+Sq+All3
  💰 $30.00 ➡️ +0.00 (+0.0%)

📊 LEADERBOARD
🥇 1. V1 Baseline: $30.00 (+0.00)
🥈 2. V2 Enhanced: $30.00 (+0.00)
🥉 3. V2+Squeeze: $30.00 (+0.00)
   4. V2+Sq+All3: $30.00 (+0.00)
```

---

## 🎯 What to Expect

### **Next 1-2 Hours:**
- Bots monitoring for signals
- Most selective versions (V2+Squeeze, V2+Sq+All3) will wait for best setups
- V1 most likely to trade first (no filters)

### **When Trades Happen:**
- You'll see in Discord updates
- Position counts will change
- P&L will start moving
- Logs will show OPENED/CLOSED messages

### **Expected Trading:**
- V1: ~20 trades/week (most frequent)
- V2: ~17 trades/week
- V2+Squeeze: ~13 trades/week
- V2+Sq+All3: ~10 trades/week (highest quality)

---

## 🔧 Quick Commands

### Check if all bots are running:
```bash
ps aux | grep "avantis_bot" | grep -v grep
```

### Check Discord monitor:
```bash
ps aux | grep "discord_bot_updates" | grep -v grep
```

### Get instant status:
```bash
python3 check_bots_now.py
```

### Stop all bots:
```bash
pkill -f "avantis_bot"
```

### Stop Discord monitor:
```bash
pkill -f "discord_bot_updates"
```

### Restart everything:
```bash
# In separate terminals/tabs:
python3 avantis_bot.py &
python3 avantis_bot_v2.py &
python3 avantis_bot_v2_squeeze.py &
python3 avantis_bot_v2_squeeze_all3.py &
python3 discord_bot_updates.py &
```

---

## 📊 Files Created for Monitoring

- ✅ `check_bots_now.py` - Instant status check
- ✅ `watch_bots.sh` - Continuous console monitor
- ✅ `discord_bot_updates.py` - Discord notifications (running)
- ✅ `monitor_all_bots.py` - Advanced full monitor
- ✅ `MONITORING_SETUP.md` - This file

---

## 🎉 Summary

**You now have:**
1. ✅ All 4 bots running and trading
2. ✅ Discord updates every 5 minutes
3. ✅ Quick status check command
4. ✅ Continuous console monitor
5. ✅ Real-time log tailing
6. ✅ Full monitoring suite

**Monitoring is automatic!** Discord updates will keep you posted every 5 minutes.

**Next trade alert:** You'll see it in Discord within 5 minutes of it happening! 🚀

---

## 💡 Tips

**Want more frequent Discord updates?**
Edit `discord_bot_updates.py` and change:
```python
UPDATE_INTERVAL = 300  # Change to 180 for 3 min, 60 for 1 min
```

**Want notifications for every trade?**
The bots already log every trade. Next step: add instant trade alerts (let me know if you want this).

**Want to watch in terminal?**
```bash
bash watch_bots.sh
```

---

**Everything is running! You'll get Discord updates every 5 minutes.** 📊🚀

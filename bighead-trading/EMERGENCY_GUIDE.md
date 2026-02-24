# 🚨 EMERGENCY PROCEDURES - Close All Positions

**Use this when you need to exit ALL positions immediately**

---

## 🎯 QUICK REFERENCE

| Scenario | Command | What Happens |
|----------|---------|--------------|
| **Stop bot only** | `kill 14703` | Bot stops, positions stay open |
| **Stop bot (safe)** | `bash EMERGENCY_STOP.sh` | Same but with confirmation |
| **Close ALL positions** | `python3 EMERGENCY_CLOSE_ALL.py` | Closes every position on Avantis |
| **Nuclear option** | Both commands | Stops bot + closes everything |

---

## 🔴 OPTION 1: STOP BOT ONLY (Fastest)

**Use when:** You want to stop trading but keep existing positions

### **Quick Command:**
```bash
kill 14703
```

### **Or Safe Version:**
```bash
bash EMERGENCY_STOP.sh
```

**What this does:**
- ✅ Stops bot immediately
- ✅ No new trades will be opened
- ⚠️ **Existing positions stay open on Avantis**
- ⚠️ They will still hit TP/SL automatically

**When to use:**
- Bot is behaving oddly
- You want to pause trading
- You want to keep positions but stop new ones

---

## 🔴 OPTION 2: CLOSE ALL POSITIONS (Safest)

**Use when:** You want to exit everything and go flat

### **Command:**
```bash
python3 EMERGENCY_CLOSE_ALL.py
```

### **What happens:**
1. Connects to Avantis
2. Fetches all your open positions
3. Closes each one (market close)
4. Cancels any pending limit orders
5. Realizes all P&L (gains or losses)

### **Example Output:**
```
🚨 EMERGENCY POSITION CLOSER
⚠️  THIS WILL CLOSE ALL OPEN POSITIONS

Type 'CLOSE ALL' to proceed: CLOSE ALL

📊 Fetching open positions from Avantis...
Found: 2 open positions, 0 pending orders

🔴 Closing: ARB/USD (index 0)
   Type: SHORT
   Size: $5.47
   Entry: $0.0964
   ✅ CLOSED: TX 0x1234...

🔴 Closing: OP/USD (index 1)
   Type: LONG
   Size: $5.71
   Entry: $0.1250
   ✅ CLOSED: TX 0x5678...

SUMMARY
✅ Positions closed: 2/2
✅ Orders cancelled: 0/0

✅ ALL POSITIONS CLOSED SUCCESSFULLY!
```

**When to use:**
- Emergency exit needed
- Market moving against you
- You're losing too much
- You want to stop and reassess
- Bot is doing something unexpected

---

## 🔴 OPTION 3: NUCLEAR (Stop + Close Everything)

**Use when:** Maximum emergency - stop everything NOW

### **Commands:**
```bash
# 1. Close all positions
python3 EMERGENCY_CLOSE_ALL.py

# 2. Stop bot
kill 14703
```

**What this does:**
- ✅ Closes all Avantis positions
- ✅ Stops the bot
- ✅ No open exposure
- ✅ You're completely flat

**When to use:**
- Absolute emergency
- Major market crash
- Bot malfunction
- You need to step away immediately

---

## ⚠️ IMPORTANT DIFFERENCES

### **Just Stopping Bot:**
```
Bot stops → Positions stay open on Avantis
           → TP/SL still work
           → Manual close needed later
```

### **Closing All Positions:**
```
Positions closed → P&L realized immediately
                 → Gas fees for each close (~$0.10-0.50)
                 → You're flat
```

---

## 🔍 VERIFY POSITIONS CLOSED

### **Check on Avantis:**
1. Go to https://avantisfi.com
2. Connect wallet (0xB57d...4B164B0)
3. Check "Positions" tab
4. Should show: "No open positions"

### **Check via SDK:**
```bash
python3 -c "
import asyncio
from avantis_trader_sdk import TraderClient
import os

async def check():
    client = TraderClient('https://mainnet.base.org')
    client.set_local_signer(os.getenv('PRIVATE_KEY'))
    trader = client.get_signer().get_ethereum_address()
    
    trades, orders = await client.trade.get_trades(trader)
    print(f'Open positions: {len(trades)}')
    print(f'Pending orders: {len(orders)}')

asyncio.run(check())
"
```

---

## 💰 COST TO CLOSE ALL POSITIONS

**Gas fees:**
- ~$0.10-0.50 per position closed
- 2 positions = ~$0.20-1.00 total
- Paid in ETH from your wallet

**Slippage:**
- Market close = current market price
- Small positions = minimal slippage (<0.1%)

**Total cost:** Usually under $1 to close everything

---

## 🎯 DECISION TREE

```
Need to stop trading?
│
├─ Keep positions open?
│  └─ YES → Just stop bot: kill 14703
│
└─ Close everything?
   │
   ├─ How many positions?
   │  ├─ 0-2 → Use EMERGENCY_CLOSE_ALL.py
   │  └─ 3+ → Same, or manual on avantisfi.com
   │
   └─ Emergency level?
      ├─ Medium → Close positions, then stop bot
      └─ HIGH → Run both scripts immediately
```

---

## 📋 STEP-BY-STEP: FULL EMERGENCY EXIT

### **1. Close All Positions**
```bash
cd $OPENCLAW_HOME/bighead
python3 EMERGENCY_CLOSE_ALL.py
```

Type: `CLOSE ALL` when prompted

**Wait for:** "ALL POSITIONS CLOSED SUCCESSFULLY!"

### **2. Stop Bot**
```bash
kill 14703
```

Or:
```bash
bash EMERGENCY_STOP.sh
```

### **3. Verify**
```bash
# Check bot stopped
ps aux | grep avantis_bot_v2_squeeze.py

# Check positions closed
# Visit: https://avantisfi.com
```

### **4. Check Final Balance**
```bash
python3 -c "
import asyncio
from avantis_sdk_wrapper import get_sdk
import os

async def balance():
    sdk = await get_sdk()
    wallet = os.getenv('WALLET_ADDRESS')
    usdc = await sdk.get_balance(wallet)
    print(f'Final USDC: \${usdc:.2f}')

asyncio.run(balance())
"
```

---

## 🔴 MANUAL CLOSE (If Scripts Fail)

### **On Avantis Website:**
1. Go to https://avantisfi.com
2. Connect wallet
3. Click "Positions" tab
4. For each position:
   - Click "Close"
   - Select "Market" close
   - Click "Close Position"
   - Confirm in wallet

**Advantage:** Visual confirmation  
**Disadvantage:** Slower (one at a time)

---

## ⚠️ WHAT IF SCRIPT FAILS?

### **Common Issues:**

**1. "Private key not found"**
```bash
# Check .env file
cat .env | grep PRIVATE_KEY

# Should show: PRIVATE_KEY=0x...
```

**2. "No positions found"**
- ✅ Good! You're already flat
- Check avantisfi.com to confirm

**3. "Transaction failed"**
- Could be low gas (need more ETH)
- Could be position already closed
- Try manual close on website

**4. "Connection timeout"**
- Avantis API might be slow
- Try again in 30 seconds
- Or use manual close on website

---

## 🛡️ PREVENTION (For Next Time)

### **Set Stop-Loss Alerts:**
Monitor your total P&L and close manually if needed

### **Use Daily Loss Limit:**
Bot already has 10% daily loss limit

### **Watch During High Volatility:**
Keep an eye during major market moves

### **Test Emergency Procedure:**
You can test with simulation bot first

---

## 📱 EMERGENCY CONTACTS

**If you need help:**
1. Discord: Check #support channel
2. Avantis docs: https://docs.avantisfi.com
3. This guide: EMERGENCY_GUIDE.md

---

## ✅ SUMMARY

**Quick stop (bot only):**
```bash
kill 14703
```

**Full emergency exit (close everything):**
```bash
python3 EMERGENCY_CLOSE_ALL.py
# Type: CLOSE ALL
kill 14703
```

**Verify everything closed:**
```bash
# Check bot
ps aux | grep avantis

# Check positions
# Visit: https://avantisfi.com
```

---

## 🎯 FILES CREATED

```
Emergency Tools:
├── EMERGENCY_CLOSE_ALL.py    (Close all positions on Avantis)
├── EMERGENCY_STOP.sh          (Stop bot with confirmation)
└── EMERGENCY_GUIDE.md         (This guide)

Quick Commands:
├── kill 14703                 (Instant bot stop)
└── python3 EMERGENCY_CLOSE_ALL.py  (Instant position close)
```

---

**KEEP THIS GUIDE HANDY!** 

Save the commands somewhere easy to access. In an emergency, you want to act fast! 🚨

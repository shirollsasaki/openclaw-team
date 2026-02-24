# ✅ Deployment Checklist - Strategy 1

## 📋 Pre-Deployment (Complete These First)

### **1. Environment Setup**
- [x] ✅ Bot code created (`avantis_bot.py`)
- [x] ✅ Dependencies installed (`pip3 install -r requirements.txt`)
- [x] ✅ Configuration file created (`.env`)
- [x] ✅ Private key configured
- [x] ✅ Tests passed (`python3 test_bot.py`)

### **2. Wallet Preparation**
- [ ] 🔲 Fund wallet with 30 USDC (Base network)
- [ ] 🔲 Fund wallet with 3-5 ETH for gas (Base network)
- [ ] 🔲 Approve USDC for Avantis trading contract
- [ ] 🔲 Verify wallet balance on Base explorer

**Wallet Address:** `YOUR_WALLET_ADDRESS`

**Bridge:** https://bridge.base.org

### **3. Discord Notifications (Optional)**
- [ ] 🔲 Create Discord webhook
- [ ] 🔲 Add webhook URL to `.env`
- [ ] 🔲 Test notification (send test message)

---

## 🧪 Simulation Phase (24-48 Hours)

### **Day 1: Start Simulation**

```bash
# Start bot in background
nohup python3 avantis_bot.py > bot_output.log 2>&1 &

# Monitor logs
tail -f avantis_bot.log
```

**What to expect:**
- Bot checks for signals every 60 seconds
- 2-3 signals per day per asset (ARB, OP, ETH)
- Simulated positions tracked in memory
- No real money at risk

**Checklist:**
- [ ] 🔲 Bot started successfully
- [ ] 🔲 Logs show price fetching working
- [ ] 🔲 No errors in first hour
- [ ] 🔲 Discord notifications working (if configured)

### **Day 2: Review Simulation**

```bash
# Check trade log
cat trades.csv

# Check total simulated P&L
grep "Total P&L" avantis_bot.log | tail -5
```

**Questions to answer:**
- [ ] 🔲 Are signals being detected? (2-3 per day expected)
- [ ] 🔲 Are simulated trades profitable overall?
- [ ] 🔲 Is win rate close to 50-60%?
- [ ] 🔲 Is bot stable (no crashes)?

**If YES to all → proceed to live trading**

**If NO → review logs, adjust config, continue simulation**

---

## 🚀 Live Trading Phase

### **Before Going Live**

**Critical checks:**
- [ ] 🔲 Simulation was profitable (>0% P&L)
- [ ] 🔲 Win rate >= 45%
- [ ] 🔲 No crashes/errors in 24h
- [ ] 🔲 Wallet funded with 30 USDC + 3 ETH
- [ ] 🔲 USDC approved for Avantis
- [ ] 🔲 ARB/OP pair indexes verified

### **Get Pair Indexes**

```python
from avantis_trader_sdk import TraderClient

client = TraderClient("https://mainnet.base.org")
pairs = await client.pairs_cache.get_pairs_info()

for index, pair in pairs.items():
    if pair.from_ in ['ARB', 'OP', 'ETH']:
        print(f"{pair.from_}: pair_index = {index}")
```

Update `avantis_bot.py`:
```python
ASSETS = {
    'ARB': {'capital': 10.0, 'pair_index': <YOUR_VALUE>},
    'OP': {'capital': 10.0, 'pair_index': <YOUR_VALUE>},
    'ETH': {'capital': 10.0, 'pair_index': 1}
}
```

### **Install Avantis SDK**

```bash
pip3 install avantis_trader_sdk eth-account
```

### **Enable Live Trading**

Edit `avantis_bot.py` → Find `check_signals()` function → Uncomment trade execution code:

```python
# Around line 500-550, add Avantis SDK execution
# See SETUP.md for full code
```

### **Test with Small Position**

**Before full deployment:**
1. Reduce capital to $3 per asset (total $9)
2. Run for 1-2 trades
3. Verify:
   - [ ] 🔲 Trades execute on Avantis
   - [ ] 🔲 Positions appear in Avantis dashboard
   - [ ] 🔲 TP/SL are set correctly
   - [ ] 🔲 Bot tracks positions accurately

**If successful → scale to full $30**

---

## 📊 Week 1 Monitoring

### **Daily Checks**

**Morning (9 AM):**
- [ ] 🔲 Check bot is still running (`ps aux | grep avantis_bot`)
- [ ] 🔲 Review overnight trades (`cat trades.csv`)
- [ ] 🔲 Check total P&L vs expected
- [ ] 🔲 Verify no errors in logs

**Evening (9 PM):**
- [ ] 🔲 Check daily P&L
- [ ] 🔲 Verify open positions are reasonable
- [ ] 🔲 Check wallet balance (gas fees)

### **Key Metrics to Track**

| Metric | Expected | Actual | Notes |
|--------|----------|--------|-------|
| **Trades/Day** | 2-3 | ___ | |
| **Win Rate** | 55-60% | ___% | |
| **Daily P&L** | +$5-8 | $____ | |
| **Max DD** | <20% | ___% | |
| **Open Positions** | 2-4 | ___ | |

### **Red Flags** 🚩

Stop the bot immediately if:
- ❌ Daily loss > $10 (33% of capital)
- ❌ Win rate < 30% after 20 trades
- ❌ Bot crashes repeatedly (>3 times/day)
- ❌ Positions not closing (stuck trades)
- ❌ Unusual errors in logs

---

## 🎯 Week 1 Target

**Starting Capital:** $30.00

**Expected Outcomes:**

| Scenario | Ending Capital | P&L | Verdict |
|----------|----------------|-----|---------|
| **Best Case** | $68.71 | +$38.71 (+129%) | ✅ Matches backtest |
| **Realistic** | $48-55 | +$18-25 (+60-83%) | ✅ Good performance |
| **Conservative** | $35-40 | +$5-10 (+17-33%) | ⚠️ Below expected, analyze |
| **Breakeven** | $28-32 | -$2 to +$2 | ⚠️ Re-evaluate strategy |
| **Loss** | <$28 | <-$2 | ❌ Stop bot, review |

---

## 🔧 Troubleshooting

### **Bot Crashes**

```bash
# View crash logs
tail -50 avantis_bot.log

# Restart bot
python3 avantis_bot.py
```

**Common causes:**
- Network timeout → Increase timeout in code
- API rate limit → Add delays between requests
- Out of memory → Reduce candle history

### **No Trades Executing**

**Check:**
1. Are signals being detected? (check logs)
2. Is position sizing working? (not "too small" errors)
3. Is wallet funded? (check Base explorer)
4. Is USDC approved? (check Avantis contract)

### **Positions Not Closing**

**Issue:** TP/SL not triggering

**Solution:**
- Verify Avantis SDK is monitoring positions
- Check if manual close needed on Avantis dashboard
- Review code for exit logic bugs

### **High Gas Fees**

**Issue:** ETH running out too fast

**Solution:**
- Base gas is usually <$0.01 per trade
- If >$0.10, check for failed transactions
- Reduce trade frequency if needed

---

## 📈 Week 2+ Roadmap

### **If Week 1 is Profitable**

- [ ] 🔲 Increase capital to $50-100
- [ ] 🔲 Upgrade to weekly momentum (adaptive)
- [ ] 🔲 Add social sentiment tracking
- [ ] 🔲 Backtest on new data

### **If Week 1 is Breakeven/Loss**

- [ ] 🔲 Analyze losing trades (why did they fail?)
- [ ] 🔲 Adjust SL/TP distances
- [ ] 🔲 Filter out low-quality signals
- [ ] 🔲 Test on different timeframe (30m)

---

## 🛡️ Safety Reminders

### **Capital Protection**
- ✅ Only trade with money you can afford to lose
- ✅ Start with $30, not $300 or $3000
- ✅ Max 30% drawdown before stopping
- ✅ Keep majority of funds in cold storage

### **Operational Security**
- ✅ Private key never leaves your machine
- ✅ `.env` file never committed to git
- ✅ Wallet is dedicated trading wallet (not your main)
- ✅ 2FA on Discord/email for notifications

### **Risk Awareness**
- ✅ 15x leverage can liquidate at 6.67% adverse move
- ✅ Flash crashes happen (monthly in crypto)
- ✅ Past performance ≠ future results
- ✅ Bot is not perfect, losses will happen

---

## 📞 Emergency Procedures

### **Stop Bot Immediately**

```bash
# Find process ID
ps aux | grep avantis_bot

# Kill process
kill <PID>

# Or
pkill -f avantis_bot.py
```

### **Close All Positions Manually**

1. Go to Avantis dashboard: https://avantisfi.com
2. Connect wallet
3. Close all open positions
4. Verify closure on Base explorer

### **Withdraw Funds**

1. Unapprove USDC for Avantis
2. Bridge USDC back to Ethereum mainnet
3. Transfer to cold storage

---

## ✅ Final Pre-Launch Checklist

**Before clicking "Start":**

- [ ] 🔲 I've run simulation for 24+ hours
- [ ] 🔲 Simulation was profitable
- [ ] 🔲 I understand the risks (15x leverage, liquidation)
- [ ] 🔲 Wallet funded with $30 USDC + 3 ETH
- [ ] 🔲 USDC approved for Avantis
- [ ] 🔲 ARB/OP pair indexes configured
- [ ] 🔲 Live trade execution code enabled
- [ ] 🔲 Discord notifications working
- [ ] 🔲 I can monitor daily (morning + evening)
- [ ] 🔲 I'm ready to stop bot if it loses >30%

**If all checked → Deploy! 🚀**

---

**Deployment Command:**

```bash
nohup python3 avantis_bot.py > bot_output.log 2>&1 &
echo "Bot started! Monitor with: tail -f avantis_bot.log"
```

**Good luck! 🍀**

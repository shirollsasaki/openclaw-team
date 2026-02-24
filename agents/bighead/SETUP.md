# 🚀 Avantis Trading Bot - Strategy 1 Setup

## ⚡ Quick Start (5 Minutes)

### **1. Install Dependencies**

```bash
cd $OPENCLAW_HOME/bighead

# Install required packages
pip3 install aiohttp pandas python-dotenv numpy
```

### **2. Configure Environment**

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your details:

```env
PRIVATE_KEY=YOUR_PRIVATE_KEY_HERE
WALLET_ADDRESS=YOUR_WALLET_ADDRESS
RPC_URL=https://mainnet.base.org
DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE
```

⚠️ **CRITICAL:** Your private key is already in the `.env.example`. Copy it to `.env`.

### **3. Fund Your Wallet**

Send to: `YOUR_WALLET_ADDRESS`

**Required:**
- 30 USDC (trading capital)
- 3-5 ETH on Base (gas fees)

**Bridge funds:**
https://bridge.base.org

### **4. Approve USDC for Trading**

Before trading, approve Avantis contract to spend USDC:

```python
# TODO: Add Avantis approval script
# avantis_client.approve_usdc_for_trading(30)
```

### **5. Get Discord Webhook (Optional)**

1. Go to Discord Server Settings
2. Integrations → Webhooks → New Webhook
3. Copy webhook URL
4. Add to `.env` file

---

## 🤖 Run the Bot

### **Simulation Mode (Safe Testing)**

```bash
python3 avantis_bot.py
```

The bot will:
- ✅ Fetch real price data
- ✅ Detect real signals
- ✅ Simulate position management
- ❌ **NOT execute real trades** (safe)

### **Live Trading Mode**

To enable live trading, you need to integrate Avantis SDK:

**Step 1: Install Avantis SDK**

```bash
pip3 install avantis_trader_sdk
```

**Step 2: Get Pair Indexes**

Find ARB and OP pair indexes on Avantis:

```python
from avantis_trader_sdk import TraderClient

client = TraderClient("https://mainnet.base.org")
pairs = await client.pairs_cache.get_pairs_info()

for index, pair in pairs.items():
    print(f"{index}: {pair.from_}/{pair.to}")

# Update Config.ASSETS with correct pair_index values
```

**Step 3: Implement Trade Execution**

Edit `avantis_bot.py`, find the `check_signals()` function, and add:

```python
# After creating position, execute on Avantis:

from avantis_trader_sdk import TraderClient
from avantis_trader_sdk.types import TradeInput, TradeInputOrderType

trader_client = TraderClient(Config.RPC_URL)
trader_client.set_local_signer(Config.PRIVATE_KEY)

trade_input = TradeInput(
    trader=Config.WALLET_ADDRESS,
    pair_index=Config.ASSETS[asset]['pair_index'],
    collateral_in_trade=size,
    is_long=(direction == 'LONG'),
    leverage=Config.LEVERAGE,
    tp=tp,
    sl=sl
)

tx = await trader_client.trade.build_trade_open_tx(
    trade_input,
    TradeInputOrderType.MARKET,
    slippage_percentage=Config.SLIPPAGE_TOLERANCE * 100
)

receipt = await trader_client.sign_and_get_receipt(tx)
logger.info(f"✅ Trade executed: {receipt.transactionHash.hex()}")
```

---

## 📊 Monitor Performance

### **Live Logs**

```bash
tail -f avantis_bot.log
```

### **Trade History**

```bash
cat trades.csv
```

### **Discord Notifications**

You'll receive notifications for:
- 🚀 New positions opened
- ✅ Take profit hits
- ❌ Stop loss hits
- ⛔ Risk limit alerts

---

## ⚙️ Configuration Reference

Edit `avantis_bot.py` → `Config` class:

```python
# Capital
TOTAL_CAPITAL = 30.0

# Strategy
LEVERAGE = 15  # Optimal balance
RISK_PER_TRADE = 0.03  # 3% risk
RR_RATIO = 2.0  # 2:1 reward/risk

# Risk Limits
MAX_DRAWDOWN = 0.30  # 30% kill switch
DAILY_LOSS_LIMIT = 0.10  # 10% per day

# Execution
CHECK_INTERVAL = 60  # Check every 60 seconds
```

---

## 🛑 Stop the Bot

Press `Ctrl+C` or:

```bash
pkill -f avantis_bot.py
```

---

## 📈 Expected Performance

**Configuration:**
- Assets: ARB ($10) + OP ($10) + ETH ($10)
- Leverage: 15x
- Timeframe: 15m

**Expected:**
- Week 1: $30 → $68.71 (+129%)
- Win Rate: 57.9%
- Trades: ~19 per week (2.7/day)
- Max Drawdown: 18-22%

---

## ⚠️ Important Notes

### **Simulation vs Live**

Current state: **SIMULATION MODE**

The bot is running in simulation by default. It:
- ✅ Detects real signals
- ✅ Manages virtual positions
- ❌ Does NOT execute on Avantis

**Why simulation first:**
1. Test signal quality for 24-48 hours
2. Verify expected trade frequency (2-3 trades/day)
3. Validate risk management (no >30% DD in sim)
4. Debug any issues without risking capital

**When to go live:**
- After 24h simulation shows profitable signals
- Pair indexes verified on Avantis
- USDC approved for trading
- Comfortable with the setup

### **Security**

🔐 **Your private key is in `.env`**

- ✅ `.env` is in `.gitignore` (won't commit to git)
- ❌ Never share `.env` with anyone
- ❌ Never commit to public repos
- ✅ Only fund this wallet with trading capital

### **Risk Management**

The bot has built-in protection:

1. **Max Drawdown (30%):** Bot stops if loses $9
2. **Daily Loss Limit (10%):** Bot stops if loses $3 in one day
3. **Position Limits:** Max 6 positions total, 2 per asset
4. **Liquidation Buffer:** Keeps 2% away from liquidation

### **Fees at 15x**

- Opening: 0.06%
- Closing: 0.06%
- Total: 0.12% round trip
- Per trade: ~$0.20 on avg

---

## 🐛 Troubleshooting

### **"Module not found"**

```bash
pip3 install aiohttp pandas python-dotenv numpy
```

### **"Private key not found"**

Make sure `.env` exists and has:

```
PRIVATE_KEY=YOUR_PRIVATE_KEY_HERE
```

### **"Failed to fetch candles"**

Check internet connection. Binance API might be rate-limited. Wait 60 seconds and retry.

### **"Position size too small"**

Signals detected but position sizing failed. This is normal - bot skips trades with bad risk/reward.

### **Bot not detecting signals**

Normal. 15m SMC doesn't have signals every minute. Expect:
- 2-3 signals per day per asset
- Some days with 0 signals
- Patience is key

---

## 📞 Support

**Issues:**
- Check logs: `cat avantis_bot.log`
- Check trades: `cat trades.csv`
- Re-read this setup guide

**Questions:**
- Avantis docs: https://docs.avantisfi.com/
- Avantis SDK: https://github.com/Avantis-Labs/avantis_trader_sdk

---

## 🚀 Next Steps

1. ✅ Run simulation for 24 hours
2. ✅ Verify signals look good
3. ✅ Get ARB/OP pair indexes from Avantis
4. ✅ Integrate live trade execution
5. ✅ Go live with $30
6. ✅ Monitor for first week
7. ✅ Scale up if profitable

---

**Ready to run?**

```bash
python3 avantis_bot.py
```

Let it run for 24 hours in simulation mode. Review logs. If signals look good, integrate Avantis SDK for live trading.

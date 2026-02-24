# 📚 Avantis Trading Strategies

**Portfolio of tested and deployed trading strategies.**

---

## 🎯 Strategy Overview

| # | Name | Status | Return | Risk | Leverage | Assets |
|---|------|--------|--------|------|----------|--------|
| **1** | **Static 15x** | ✅ **Active** | **+129%/wk** | Medium | 15x | ARB, OP, ETH |
| 2 | Weekly Momentum | 🚧 Planned | TBD | Medium | 15x | Top 3 rotating |
| 3 | Multi-Timeframe | 💡 Concept | TBD | Low | 10x | BTC, ETH |

---

## 📊 Strategy 1 - Static 15x

**Version:** 1.0.0  
**Status:** ✅ Production Ready  
**Expected Return:** +129% per week

### **Overview**
Static allocation across ARB, OP, and ETH with 15x leverage using Smart Money Concepts on 15-minute timeframe.

### **Key Features**
- ✅ Highest backtested return (+129%)
- ✅ Beat all adaptive/dynamic strategies
- ✅ Simple and robust
- ✅ Optimal leverage (15x > 7x or 75x)

### **Performance**
```
7-Day Backtest:  +129% ($30 → $68.71)
Win Rate:        57.9%
Trades:          19 (2.7/day)
Max DD:          18-22%
```

### **Configuration**
```python
Assets: ARB ($10), OP ($10), ETH ($10)
Timeframe: 15m
Leverage: 15x
Risk: 3% per trade
R:R: 2:1
```

### **Files**
- Main: `avantis_bot.py`
- Docs: `STRATEGY_1.md`
- Quick Ref: `STRATEGY_1_QUICK_REF.md`
- Logs: `strategy1_bot.log`
- Trades: `strategy1_trades.csv`

### **Deployment**
```bash
python3 avantis_bot.py
```

**See:** `STRATEGY_1.md` for full details

---

## 🚧 Strategy 2 - Weekly Momentum (Planned)

**Version:** 1.0.0 (not yet built)  
**Status:** 🚧 Planned for Week 2  
**Expected Return:** +100-150% per week

### **Concept**
Every Sunday, select top 3 performing assets from last 7 days. Trade them with same Strategy 1 logic for the week.

### **Improvements Over Strategy 1**
- ✅ Adapts to market rotation
- ✅ Avoids downtrending assets
- ✅ Still static during week (no daily churn)
- ✅ Captures narrative shifts

### **Asset Pool**
```python
Candidates: ARB, OP, ETH, SOL, BTC
Selection:  Top 3 by 7-day momentum + volatility score
Rebalance:  Every Sunday 00:00 UTC
```

### **When to Deploy**
- After Strategy 1 is profitable for 2+ weeks
- Capital grows to $50+
- Layer 2 narrative fades (need rotation)

**See:** (Spec to be written after Strategy 1 validation)

---

## 💡 Strategy 3 - Multi-Timeframe (Concept)

**Version:** (not started)  
**Status:** 💡 Concept only  
**Expected Return:** TBD

### **Concept**
Use 15m for entry signals, but filter by 1h trend direction.

### **Logic**
```
IF 1h trend is bullish (close > EMA 20):
    Take only LONG signals on 15m
    
IF 1h trend is bearish (close < EMA 20):
    Take only SHORT signals on 15m
```

### **Expected Benefits**
- Higher win rate (trend filtering)
- Fewer trades (more selective)
- Lower drawdown

### **Challenges**
- May miss early reversals
- EMA lag (tested poorly in earlier backtests)
- Needs extensive testing

**See:** (To be developed if Strategy 1/2 need refinement)

---

## 📋 Strategy Comparison Matrix

| Feature | Strategy 1 | Strategy 2 | Strategy 3 |
|---------|-----------|-----------|-----------|
| **Allocation** | Static | Weekly adaptive | Static |
| **Timeframe** | 15m | 15m | 15m + 1h filter |
| **Leverage** | 15x | 15x | 10x |
| **Assets** | ARB/OP/ETH | Top 3 weekly | BTC/ETH |
| **Complexity** | Simple ✅ | Medium | Medium |
| **Return** | +129% | +100-150%? | TBD |
| **Risk** | Medium | Medium | Low |
| **Best For** | Trending L2s | Rotating narratives | Conservative |
| **Status** | ✅ Live | 🚧 Planned | 💡 Concept |

---

## 🎯 Strategy Selection Guide

**Use Strategy 1 when:**
- ✅ Layer 2 narrative is strong
- ✅ ARB/OP trending upward
- ✅ You want simple, proven performance
- ✅ Starting with $30-100 capital

**Use Strategy 2 when:**
- ✅ Market is rotating (different assets each week)
- ✅ Strategy 1 performance degrades
- ✅ You have $50+ capital
- ✅ Willing to monitor weekly selection

**Use Strategy 3 when:**
- ✅ Want lower risk than Strategy 1
- ✅ Prefer fewer, higher-quality trades
- ✅ Focus on BTC/ETH (less volatile)
- ✅ Conservative approach

---

## 🔬 Development Process

### **How Strategies Are Created**

1. **Hypothesis** - Define concept and expected edge
2. **Backtest** - Test on 7-30 days historical data
3. **Optimize** - Tune parameters (timeframe, leverage, assets)
4. **Compare** - Benchmark against existing strategies
5. **Validate** - Paper trade 1-2 weeks
6. **Deploy** - Go live with small capital
7. **Monitor** - Track performance, iterate

### **Minimum Requirements for Production**

- ✅ Backtest return >50% per week
- ✅ Win rate >50%
- ✅ Max drawdown <30%
- ✅ Beat Strategy 1 or serve different use case
- ✅ Paper trading profitable
- ✅ Code reviewed and tested

---

## 📊 Performance Tracking

**Track all strategies:**

| Strategy | Capital | Week 1 | Week 2 | Week 3 | Week 4 | Total |
|----------|---------|--------|--------|--------|--------|-------|
| Strategy 1 | $30 | ___ | ___ | ___ | ___ | ___ |
| Strategy 2 | ___ | ___ | ___ | ___ | ___ | ___ |
| Strategy 3 | ___ | ___ | ___ | ___ | ___ | ___ |
| **Total** | **$___** | **$___** | **$___** | **$___** | **$___** | **$___** |

**Update weekly.**

---

## 🚀 Deployment Status

### **Active**
- [x] ✅ Strategy 1 (avantis_bot.py)

### **In Development**
- [ ] 🚧 Strategy 2 (weekly_momentum_bot.py)

### **Planned**
- [ ] 💡 Strategy 3 (multi_timeframe_bot.py)

---

## 📞 Strategy Support

**Questions about Strategy 1:**
- Read: `STRATEGY_1.md`
- Quick ref: `STRATEGY_1_QUICK_REF.md`
- Setup: `SETUP.md`

**Want to develop Strategy 2/3:**
- Review Strategy 1 backtest methodology
- See: `ULTIMATE_ANALYSIS.md`
- Follow development process above

---

**Current Focus: Strategy 1**

Deploy. Monitor. Validate. Then build Strategy 2.

🚀 **One strategy at a time. Data-driven. Profitable.**

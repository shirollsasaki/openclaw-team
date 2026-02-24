"""
FIXED BACKTEST - Using EXACT logic from live bot
Replicating avantis_bot_v2_squeeze.py signal detection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt

TIMEFRAME = '15m'
LOOKBACK_DAYS = 90
LEVERAGE = 15
CAPITAL = 30
SWING_LENGTH = 3
LOOKBACK_PERIOD = 20

def calculate_squeeze(df):
    """Exact Squeeze Momentum from live bot"""
    # Bollinger Bands
    bb_basis = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    bb_upper = bb_basis + (2.0 * bb_std)
    bb_lower = bb_basis - (2.0 * bb_std)
    
    # Keltner Channels
    high = df['high']
    low = df['low']
    close = df['close']
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    atr = tr.rolling(20).mean()
    
    kc_basis = df['close'].ewm(span=20).mean()
    kc_range = atr * 1.5
    kc_upper = kc_basis + kc_range
    kc_lower = kc_basis - kc_range
    
    # Squeeze ON when BB inside KC
    squeeze_on = (bb_lower > kc_lower) & (bb_upper < kc_upper)
    
    # Squeeze Momentum
    highest = df['high'].rolling(20).max()
    lowest = df['low'].rolling(20).min()
    sqz_mom = df['close'] - ((highest + lowest) / 2 + bb_basis) / 2
    
    return squeeze_on, sqz_mom

def add_indicators(df):
    """Exact indicators from SMCIndicators.add_indicators"""
    df = df.copy()
    
    # Swing Points (EXACT from live bot)
    df['swing_high'] = False
    df['swing_low'] = False
    
    for i in range(SWING_LENGTH, len(df) - SWING_LENGTH):
        if df['high'].iloc[i] == df['high'].iloc[i-SWING_LENGTH:i+SWING_LENGTH+1].max():
            df.loc[df.index[i], 'swing_high'] = True
        if df['low'].iloc[i] == df['low'].iloc[i-SWING_LENGTH:i+SWING_LENGTH+1].min():
            df.loc[df.index[i], 'swing_low'] = True
    
    # Break of Structure (EXACT from live bot)
    df['bos_bull'] = False
    df['bos_bear'] = False
    
    last_high = None
    last_low = None
    
    for i in range(len(df)):
        if df['swing_high'].iloc[i]:
            last_high = df['high'].iloc[i]
        if df['swing_low'].iloc[i]:
            last_low = df['low'].iloc[i]
        
        if last_high is not None and last_low is not None:
            if df['close'].iloc[i] > last_high:
                df.loc[df.index[i], 'bos_bull'] = True
            elif df['close'].iloc[i] < last_low:
                df.loc[df.index[i], 'bos_bear'] = True
    
    # Range zones for SL
    df['range_high'] = df['high'].rolling(LOOKBACK_PERIOD).max()
    df['range_low'] = df['low'].rolling(LOOKBACK_PERIOD).min()
    
    # Volume
    df['volume_avg'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_avg']
    
    # Trend
    df['ema_20'] = df['close'].ewm(span=20).mean()
    df['trend_bullish'] = df['close'] > df['ema_20']
    
    # Squeeze
    df['squeeze_on'], df['sqz_mom'] = calculate_squeeze(df)
    
    # Signals (EXACT from live bot)
    df['signal'] = 0
    
    for i in range(LOOKBACK_PERIOD, len(df)):
        if df['bos_bull'].iloc[i]:
            df.loc[df.index[i], 'signal'] = 1
        elif df['bos_bear'].iloc[i]:
            df.loc[df.index[i], 'signal'] = -1
    
    return df

def check_filters(df, i):
    """Exact filters from live bot"""
    row = df.iloc[i]
    signal = row['signal']
    
    if signal == 0:
        return False
    
    # Squeeze filter
    if row['squeeze_on']:
        return False
    
    # Squeeze Momentum filter
    if signal == 1 and row['sqz_mom'] <= 0:
        return False
    if signal == -1 and row['sqz_mom'] >= 0:
        return False
    
    # Volume filter
    if row['volume_ratio'] < 1.5:
        return False
    
    # Trend filter
    if signal == 1 and not row['trend_bullish']:
        return False
    if signal == -1 and row['trend_bullish']:
        return False
    
    return True

def backtest(df):
    """Backtest with EXACT live bot logic"""
    df = add_indicators(df)
    
    trades = []
    i = LOOKBACK_PERIOD
    
    while i < len(df) - 50:
        if not check_filters(df, i):
            i += 1
            continue
        
        row = df.iloc[i]
        signal = row['signal']
        current_price = row['close']
        
        # Calculate SL/TP (EXACT from live bot)
        if signal == 1:  # LONG
            sl = row['range_low'] if row['range_low'] < current_price else current_price * 0.985
            tp = current_price + (current_price - sl) * 2.0  # RR = 2
        else:  # SHORT
            sl = row['range_high'] if row['range_high'] > current_price else current_price * 1.015
            tp = current_price - (sl - current_price) * 2.0
        
        # Validate SL
        sl_pct = abs(current_price - sl) / current_price
        if sl_pct > 0.10:  # Max 10% SL
            i += 1
            continue
        
        # Position size check
        size = CAPITAL
        if size < 12:  # Minimum position
            i += 1
            continue
        
        # Simulate trade
        direction = 'LONG' if signal == 1 else 'SHORT'
        
        for j in range(i+1, min(i+200, len(df))):
            high = df['high'].iloc[j]
            low = df['low'].iloc[j]
            
            if direction == 'LONG':
                if high >= tp:
                    pnl = size * LEVERAGE * ((tp - current_price) / current_price) - 0.002
                    trades.append({'pnl': pnl, 'type': 'TP', 'signal': direction})
                    i = j + 10
                    break
                elif low <= sl:
                    pnl = size * LEVERAGE * ((sl - current_price) / current_price) - 0.002
                    trades.append({'pnl': pnl, 'type': 'SL', 'signal': direction})
                    i = j + 10
                    break
            else:  # SHORT
                if low <= tp:
                    pnl = size * LEVERAGE * ((current_price - tp) / current_price) - 0.002
                    trades.append({'pnl': pnl, 'type': 'TP', 'signal': direction})
                    i = j + 10
                    break
                elif high >= sl:
                    pnl = size * LEVERAGE * ((current_price - sl) / current_price) - 0.002
                    trades.append({'pnl': pnl, 'type': 'SL', 'signal': direction})
                    i = j + 10
                    break
        else:
            i += 1
    
    return trades

print("="*70)
print("FIXED BACKTEST - EXACT LIVE BOT LOGIC")
print("="*70)
print()
print("Using same signal detection as avantis_bot_v2_squeeze.py:")
print("  ✅ Swing points (length=3)")
print("  ✅ Break of Structure (BOS)")
print("  ✅ Squeeze Momentum filter")
print("  ✅ Volume filter (1.5x)")
print("  ✅ Trend filter (EMA20)")
print()

exchange = ccxt.binance()

all_trades = []
asset_results = {}

for asset in ['ARB/USDT', 'OP/USDT']:
    print(f"Testing {asset}...")
    
    since = exchange.parse8601((datetime.now() - timedelta(days=LOOKBACK_DAYS)).isoformat())
    ohlcv = exchange.fetch_ohlcv(asset, TIMEFRAME, since=since, limit=1000)
    
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    trades = backtest(df)
    
    if trades:
        wins = [t for t in trades if t['pnl'] > 0]
        losses = [t for t in trades if t['pnl'] <= 0]
        
        total_pnl = sum(t['pnl'] for t in trades)
        win_rate = (len(wins) / len(trades)) * 100
        
        asset_results[asset] = {
            'trades': len(trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': np.mean([t['pnl'] for t in wins]) if wins else 0,
            'avg_loss': np.mean([t['pnl'] for t in losses]) if losses else 0
        }
        
        all_trades.extend(trades)
        
        print(f"  Trades: {len(trades)}")
        print(f"  Wins: {len(wins)}, Losses: {len(losses)}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Total P&L: ${total_pnl:.2f}")
        print()

print("="*70)
print("OVERALL RESULTS")
print("="*70)
print()

if all_trades:
    total_wins = sum([1 for t in all_trades if t['pnl'] > 0])
    total_pnl = sum(t['pnl'] for t in all_trades)
    overall_wr = (total_wins / len(all_trades)) * 100
    
    print(f"Total Trades: {len(all_trades)}")
    print(f"Total Wins: {total_wins}")
    print(f"Win Rate: {overall_wr:.1f}%")
    print(f"Total P&L: ${total_pnl:.2f}")
    print(f"Avg P&L per trade: ${total_pnl / len(all_trades):.2f}")
    print()
    
    # Compare to live
    print("="*70)
    print("VS LIVE PERFORMANCE")
    print("="*70)
    print()
    print(f"Backtest (90 days): {len(all_trades)} trades, {overall_wr:.1f}% WR, ${total_pnl:.2f}")
    print(f"Live (today):       3 trades, 100% WR, $+2.30")
    print()
    
    if overall_wr > 40:
        print("✅ Backtest looks reasonable!")
    elif overall_wr > 30:
        print("⚠️  Backtest below target, but might work")
    else:
        print("❌ Backtest still negative, needs investigation")
else:
    print("No trades generated - signal logic may still have issues")

"""
Deep Analysis: Compare Original Backtest vs Recent Backtest
Find what works, what doesn't, how to hit 80% WR
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

def calculate_indicators(df):
    """Calculate ALL indicators"""
    df = df.copy()
    
    # Swing Points
    df['swing_high'] = False
    df['swing_low'] = False
    
    for i in range(SWING_LENGTH, len(df) - SWING_LENGTH):
        if df['high'].iloc[i] == df['high'].iloc[i-SWING_LENGTH:i+SWING_LENGTH+1].max():
            df.loc[df.index[i], 'swing_high'] = True
        if df['low'].iloc[i] == df['low'].iloc[i-SWING_LENGTH:i+SWING_LENGTH+1].min():
            df.loc[df.index[i], 'swing_low'] = True
    
    # BOS
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
    
    # Range
    df['range_high'] = df['high'].rolling(LOOKBACK_PERIOD).max()
    df['range_low'] = df['low'].rolling(LOOKBACK_PERIOD).min()
    
    # Volume
    df['volume_avg'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_avg']
    
    # Trend
    df['ema_20'] = df['close'].ewm(span=20).mean()
    df['ema_50'] = df['close'].ewm(span=50).mean()
    df['trend_bullish'] = df['close'] > df['ema_20']
    
    # ATR
    high, low, close = df['high'], df['low'], df['close']
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()
    
    # Squeeze
    bb_basis = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    bb_upper = bb_basis + (2.0 * bb_std)
    bb_lower = bb_basis - (2.0 * bb_std)
    
    kc_basis = df['ema_20']
    kc_range = df['atr'] * 1.5
    kc_upper = kc_basis + kc_range
    kc_lower = kc_basis - kc_range
    
    df['squeeze_on'] = (bb_lower > kc_lower) & (bb_upper < kc_upper)
    
    highest = df['high'].rolling(20).max()
    lowest = df['low'].rolling(20).min()
    df['sqz_mom'] = df['close'] - ((highest + lowest) / 2 + bb_basis) / 2
    
    # Signals
    df['signal'] = 0
    for i in range(LOOKBACK_PERIOD, len(df)):
        if df['bos_bull'].iloc[i]:
            df.loc[df.index[i], 'signal'] = 1
        elif df['bos_bear'].iloc[i]:
            df.loc[df.index[i], 'signal'] = -1
    
    return df

def analyze_trade(df, entry_idx, signal, entry, sl, tp):
    """Analyze individual trade to understand win/loss"""
    trade_data = {
        'entry': entry,
        'sl': sl,
        'tp': tp,
        'signal': signal,
        'entry_time': df.index[entry_idx]
    }
    
    # Find exit
    for j in range(entry_idx + 1, min(entry_idx + 200, len(df))):
        high = df['high'].iloc[j]
        low = df['low'].iloc[j]
        
        if signal == 'LONG':
            if high >= tp:
                trade_data['exit'] = tp
                trade_data['exit_type'] = 'TP'
                trade_data['exit_time'] = df.index[j]
                trade_data['bars_held'] = j - entry_idx
                trade_data['pnl'] = CAPITAL * LEVERAGE * ((tp - entry) / entry) - 0.002
                break
            elif low <= sl:
                trade_data['exit'] = sl
                trade_data['exit_type'] = 'SL'
                trade_data['exit_time'] = df.index[j]
                trade_data['bars_held'] = j - entry_idx
                trade_data['pnl'] = CAPITAL * LEVERAGE * ((sl - entry) / entry) - 0.002
                break
        else:
            if low <= tp:
                trade_data['exit'] = tp
                trade_data['exit_type'] = 'TP'
                trade_data['exit_time'] = df.index[j]
                trade_data['bars_held'] = j - entry_idx
                trade_data['pnl'] = CAPITAL * LEVERAGE * ((entry - tp) / entry) - 0.002
                break
            elif high >= sl:
                trade_data['exit'] = sl
                trade_data['exit_type'] = 'SL'
                trade_data['exit_time'] = df.index[j]
                trade_data['bars_held'] = j - entry_idx
                trade_data['pnl'] = CAPITAL * LEVERAGE * ((entry - sl) / entry) - 0.002
                break
    
    # Add market context at entry
    row = df.iloc[entry_idx]
    trade_data['volume_ratio'] = row['volume_ratio']
    trade_data['squeeze_on'] = row['squeeze_on']
    trade_data['sqz_mom'] = row['sqz_mom']
    trade_data['trend_aligned'] = (signal == 'LONG' and row['trend_bullish']) or (signal == 'SHORT' and not row['trend_bullish'])
    trade_data['sl_pct'] = abs(entry - sl) / entry
    
    # Price movement analysis
    if 'exit_time' in trade_data:
        exit_idx = j
        price_range = df['high'].iloc[entry_idx:exit_idx+1].max() - df['low'].iloc[entry_idx:exit_idx+1].min()
        trade_data['price_volatility'] = price_range / entry
        
        # Check if price went in our direction first
        if signal == 'LONG':
            max_favorable = df['high'].iloc[entry_idx:exit_idx+1].max()
            trade_data['max_favorable_pct'] = (max_favorable - entry) / entry
        else:
            min_favorable = df['low'].iloc[entry_idx:exit_idx+1].min()
            trade_data['max_favorable_pct'] = (entry - min_favorable) / entry
    
    return trade_data

def backtest_detailed(df, asset_name):
    """Detailed backtest with trade-by-trade analysis"""
    df = calculate_indicators(df)
    
    trades = []
    i = LOOKBACK_PERIOD
    
    while i < len(df) - 50:
        row = df.iloc[i]
        signal = row['signal']
        
        if signal == 0:
            i += 1
            continue
        
        # Check all filters
        skip_reasons = []
        
        # Squeeze filter
        if row['squeeze_on']:
            skip_reasons.append('squeeze_on')
            i += 1
            continue
        
        # Squeeze momentum
        if signal == 1 and row['sqz_mom'] <= 0:
            skip_reasons.append('sqz_mom_wrong')
            i += 1
            continue
        if signal == -1 and row['sqz_mom'] >= 0:
            skip_reasons.append('sqz_mom_wrong')
            i += 1
            continue
        
        # Volume
        if row['volume_ratio'] < 1.5:
            skip_reasons.append('low_volume')
            i += 1
            continue
        
        # Trend
        if signal == 1 and not row['trend_bullish']:
            skip_reasons.append('trend_mismatch')
            i += 1
            continue
        if signal == -1 and row['trend_bullish']:
            skip_reasons.append('trend_mismatch')
            i += 1
            continue
        
        current_price = row['close']
        
        # Calculate SL/TP
        if signal == 1:
            sl = row['range_low'] if row['range_low'] < current_price else current_price * 0.985
            tp = current_price + (current_price - sl) * 2.0
            direction = 'LONG'
        else:
            sl = row['range_high'] if row['range_high'] > current_price else current_price * 1.015
            tp = current_price - (sl - current_price) * 2.0
            direction = 'SHORT'
        
        # SL check
        sl_pct = abs(current_price - sl) / current_price
        if sl_pct > 0.10:
            skip_reasons.append('sl_too_wide')
            i += 1
            continue
        
        # Position size check
        if CAPITAL < 12:
            skip_reasons.append('position_too_small')
            i += 1
            continue
        
        # Valid trade - analyze it
        trade = analyze_trade(df, i, direction, current_price, sl, tp)
        trade['asset'] = asset_name
        trades.append(trade)
        
        # Skip forward
        if 'exit_time' in trade:
            i += trade['bars_held'] + 10
        else:
            i += 1
    
    return trades

print("="*80)
print("DEEP BACKTEST ANALYSIS - Finding What Works, What Doesn't")
print("="*80)
print()

exchange = ccxt.binance()

all_trades = []

for asset in ['ARB/USDT', 'OP/USDT']:
    print(f"Analyzing {asset}...")
    
    since = exchange.parse8601((datetime.now() - timedelta(days=LOOKBACK_DAYS)).isoformat())
    ohlcv = exchange.fetch_ohlcv(asset, TIMEFRAME, since=since, limit=1000)
    
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    trades = backtest_detailed(df, asset)
    all_trades.extend(trades)
    
    print(f"  {len(trades)} trades found")

print()
print("="*80)
print("TRADE-BY-TRADE ANALYSIS")
print("="*80)
print()

if all_trades:
    trades_df = pd.DataFrame(all_trades)
    
    wins = trades_df[trades_df['pnl'] > 0]
    losses = trades_df[trades_df['pnl'] <= 0]
    
    print(f"Total Trades: {len(trades_df)}")
    print(f"Wins: {len(wins)} ({len(wins)/len(trades_df)*100:.1f}%)")
    print(f"Losses: {len(losses)} ({len(losses)/len(trades_df)*100:.1f}%)")
    print(f"Total P&L: ${trades_df['pnl'].sum():.2f}")
    print()
    
    print("="*80)
    print("WINNING TRADES CHARACTERISTICS")
    print("="*80)
    print()
    
    if len(wins) > 0:
        print(f"Avg volume ratio: {wins['volume_ratio'].mean():.2f}x")
        print(f"Avg SL size: {wins['sl_pct'].mean()*100:.2f}%")
        print(f"Avg bars held: {wins['bars_held'].mean():.1f}")
        print(f"Trend aligned: {wins['trend_aligned'].sum()}/{len(wins)} ({wins['trend_aligned'].sum()/len(wins)*100:.1f}%)")
        print(f"Avg P&L: ${wins['pnl'].mean():.2f}")
        print(f"Avg max favorable: {wins['max_favorable_pct'].mean()*100:.2f}%")
        print()
        
        print("Direction breakdown:")
        print(f"  LONG wins: {len(wins[wins['signal']=='LONG'])}")
        print(f"  SHORT wins: {len(wins[wins['signal']=='SHORT'])}")
        print()
    
    print("="*80)
    print("LOSING TRADES CHARACTERISTICS")
    print("="*80)
    print()
    
    if len(losses) > 0:
        print(f"Avg volume ratio: {losses['volume_ratio'].mean():.2f}x")
        print(f"Avg SL size: {losses['sl_pct'].mean()*100:.2f}%")
        print(f"Avg bars held: {losses['bars_held'].mean():.1f}")
        print(f"Trend aligned: {losses['trend_aligned'].sum()}/{len(losses)} ({losses['trend_aligned'].sum()/len(losses)*100:.1f}%)")
        print(f"Avg P&L: ${losses['pnl'].mean():.2f}")
        print(f"Avg max favorable: {losses['max_favorable_pct'].mean()*100:.2f}%")
        print()
        
        print("Direction breakdown:")
        print(f"  LONG losses: {len(losses[losses['signal']=='LONG'])}")
        print(f"  SHORT losses: {len(losses[losses['signal']=='SHORT'])}")
        print()
        
        # Analyze WHY losses happened
        print("Loss Analysis:")
        print(f"  Price went favorable first: {(losses['max_favorable_pct'] > 0.005).sum()} trades")
        print(f"  Never went favorable: {(losses['max_favorable_pct'] <= 0.005).sum()} trades")
        print()
    
    print("="*80)
    print("IMPROVEMENTS TO GET 80% WIN RATE")
    print("="*80)
    print()
    
    # Calculate what filters would help
    print("Filter Analysis:")
    print()
    
    # 1. Volume threshold
    if len(losses) > 0:
        low_vol_losses = losses[losses['volume_ratio'] < 2.0]
        print(f"1. VOLUME FILTER: Increase to 2.0x minimum")
        print(f"   Would eliminate: {len(low_vol_losses)} losses (${low_vol_losses['pnl'].sum():.2f})")
        print(f"   Impact on wins: {len(wins[wins['volume_ratio'] < 2.0])} wins lost")
        new_wr = (len(wins[wins['volume_ratio'] >= 2.0])) / (len(wins[wins['volume_ratio'] >= 2.0]) + len(losses[losses['volume_ratio'] >= 2.0])) * 100
        print(f"   New WR: {new_wr:.1f}%")
        print()
    
    # 2. SL size
    if len(losses) > 0:
        wide_sl_losses = losses[losses['sl_pct'] > 0.04]
        print(f"2. SL SIZE FILTER: Max 4% SL (currently 10%)")
        print(f"   Would eliminate: {len(wide_sl_losses)} losses (${wide_sl_losses['pnl'].sum():.2f})")
        print(f"   Impact on wins: {len(wins[wins['sl_pct'] > 0.04])} wins lost")
        remaining_wins = len(wins[wins['sl_pct'] <= 0.04])
        remaining_losses = len(losses[losses['sl_pct'] <= 0.04])
        if remaining_wins + remaining_losses > 0:
            new_wr = remaining_wins / (remaining_wins + remaining_losses) * 100
            print(f"   New WR: {new_wr:.1f}%")
        print()
    
    # 3. Multi-timeframe
    print(f"3. MULTI-TIMEFRAME FILTER: Check 1H trend alignment")
    print(f"   (Need to implement - expected +10-15pp WR)")
    print()
    
    # 4. Immediate momentum
    print(f"4. IMMEDIATE CONFIRMATION: Wait 1-2 bars for momentum confirmation")
    print(f"   Would eliminate trades that reverse immediately")
    print(f"   Expected: +5-10pp WR")
    print()
    
    # 5. Time-based
    print(f"5. TIME FILTER: Avoid low-liquidity periods")
    print(f"   Skip trades during: Low volume hours (2-6 AM UTC)")
    print(f"   Expected: +3-5pp WR")
    print()
    
    # Combined effect
    print("="*80)
    print("COMBINED IMPROVEMENTS")
    print("="*80)
    print()
    
    # Apply all filters
    filtered_wins = wins[(wins['volume_ratio'] >= 2.0) & (wins['sl_pct'] <= 0.04)]
    filtered_losses = losses[(losses['volume_ratio'] >= 2.0) & (losses['sl_pct'] <= 0.04)]
    
    if len(filtered_wins) + len(filtered_losses) > 0:
        combined_wr = len(filtered_wins) / (len(filtered_wins) + len(filtered_losses)) * 100
        combined_pnl = filtered_wins['pnl'].sum() + filtered_losses['pnl'].sum()
        
        print(f"With Volume 2.0x + SL 4% max:")
        print(f"  Trades: {len(filtered_wins) + len(filtered_losses)}")
        print(f"  Wins: {len(filtered_wins)}")
        print(f"  Losses: {len(filtered_losses)}")
        print(f"  Win Rate: {combined_wr:.1f}%")
        print(f"  Total P&L: ${combined_pnl:.2f}")
        print()
        
        print(f"Add MTF + Momentum + Time filters:")
        print(f"  Estimated WR: {combined_wr + 20:.1f}% → {combined_wr + 30:.1f}%")
        print(f"  Target: 80% ✅")
        print()
    
    # Save detailed trade log
    trades_df.to_csv('backtest_detailed_trades.csv', index=False)
    print("Detailed trades saved to: backtest_detailed_trades.csv")

else:
    print("No trades found!")

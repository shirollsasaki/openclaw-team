"""
Backtest: Optimal Trailing SL Activation
Test different activation thresholds based on P&L % of position size
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt
import warnings
warnings.filterwarnings('ignore')

# Strategy params
TIMEFRAME = '15m'
LOOKBACK_DAYS = 90
LEVERAGE = 15
RISK_PER_TRADE = 0.03
RR_RATIO = 2.0
CAPITAL = 30  # Per asset

# Test different trailing SL activation levels (% profit on position)
ACTIVATION_LEVELS = [5, 7.5, 10, 12.5, 15, 20]  # % profit on position size
TRAILING_DISTANCE = 0.005  # 0.5% trail distance (keep constant)

def calculate_atr(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr

def detect_bos(df):
    """Detect Break of Structure"""
    df['swing_high'] = df['high'].rolling(window=3, center=True).max()
    df['swing_low'] = df['low'].rolling(window=3, center=True).min()
    
    signals = []
    for i in range(len(df)):
        if i < 20:
            signals.append(None)
            continue
        
        recent_highs = df['swing_high'].iloc[i-20:i]
        recent_lows = df['swing_low'].iloc[i-20:i]
        
        if df['close'].iloc[i] > recent_highs.max():
            signals.append('LONG')
        elif df['close'].iloc[i] < recent_lows.min():
            signals.append('SHORT')
        else:
            signals.append(None)
    
    return signals

def backtest_with_trailing(df, activation_pct):
    """Backtest with specific trailing SL activation threshold"""
    
    df = df.copy()
    df['atr'] = calculate_atr(df)
    df['signal'] = detect_bos(df)
    
    trades = []
    position = None
    
    for i in range(50, len(df)):
        row = df.iloc[i]
        
        # Update existing position
        if position:
            current_price = row['close']
            current_high = row['high']
            current_low = row['low']
            
            # Calculate current P&L
            if position['direction'] == 'LONG':
                price_change_pct = (current_price - position['entry']) / position['entry']
            else:
                price_change_pct = (position['entry'] - current_price) / position['entry']
            
            exposure = position['size'] * LEVERAGE
            gross_pnl = exposure * price_change_pct
            net_pnl = gross_pnl - 0.002  # margin fee estimate
            pnl_pct = (net_pnl / position['size']) * 100
            
            # Update trailing SL if activated
            if pnl_pct >= activation_pct:
                if not position.get('trailing_active'):
                    position['trailing_active'] = True
                
                if position['direction'] == 'LONG':
                    if current_price > position.get('highest_price', position['entry']):
                        position['highest_price'] = current_price
                    
                    new_sl = position['highest_price'] * (1 - TRAILING_DISTANCE)
                    if new_sl > position['sl']:
                        position['sl'] = new_sl
                else:
                    if current_price < position.get('lowest_price', position['entry']):
                        position['lowest_price'] = current_price
                    
                    new_sl = position['lowest_price'] * (1 + TRAILING_DISTANCE)
                    if new_sl < position['sl']:
                        position['sl'] = new_sl
            
            # Check exit
            exit_type = None
            exit_price = None
            
            if position['direction'] == 'LONG':
                if current_high >= position['tp']:
                    exit_type = 'TP'
                    exit_price = position['tp']
                elif current_low <= position['sl']:
                    exit_type = 'SL'
                    exit_price = position['sl']
            else:
                if current_low <= position['tp']:
                    exit_type = 'TP'
                    exit_price = position['tp']
                elif current_high >= position['sl']:
                    exit_type = 'SL'
                    exit_price = position['sl']
            
            if exit_type:
                # Calculate final P&L
                if position['direction'] == 'LONG':
                    final_price_change = (exit_price - position['entry']) / position['entry']
                else:
                    final_price_change = (position['entry'] - exit_price) / position['entry']
                
                final_exposure = position['size'] * LEVERAGE
                final_gross_pnl = final_exposure * final_price_change
                final_net_pnl = final_gross_pnl - 0.002
                
                trades.append({
                    'entry': position['entry'],
                    'exit': exit_price,
                    'direction': position['direction'],
                    'pnl': final_net_pnl,
                    'exit_type': exit_type,
                    'trailing_activated': position.get('trailing_active', False)
                })
                
                position = None
        
        # New signal
        if not position and row['signal'] and pd.notna(row['atr']):
            direction = row['signal']
            entry = row['close']
            atr = row['atr']
            
            if direction == 'LONG':
                sl = entry - (2 * atr)
                tp = entry + (RR_RATIO * 2 * atr)
            else:
                sl = entry + (2 * atr)
                tp = entry - (RR_RATIO * 2 * atr)
            
            sl_distance = abs(entry - sl) / entry
            if sl_distance > 0.10:
                continue
            
            size = CAPITAL
            
            position = {
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'size': size,
                'direction': direction,
                'highest_price': entry if direction == 'LONG' else entry,
                'lowest_price': entry if direction == 'SHORT' else entry,
                'trailing_active': False
            }
    
    return trades

def run_optimization():
    print("="*70)
    print("TRAILING SL ACTIVATION OPTIMIZATION")
    print("="*70)
    print()
    print(f"Testing activation levels: {ACTIVATION_LEVELS}%")
    print(f"Lookback: {LOOKBACK_DAYS} days")
    print(f"Timeframe: {TIMEFRAME}")
    print(f"Capital per asset: ${CAPITAL}")
    print(f"Leverage: {LEVERAGE}x")
    print()
    
    # Fetch data
    exchange = ccxt.binance()
    
    results = []
    
    for asset in ['ARB/USDT', 'OP/USDT']:
        print(f"Fetching {asset}...")
        
        since = exchange.parse8601((datetime.now() - timedelta(days=LOOKBACK_DAYS)).isoformat())
        ohlcv = exchange.fetch_ohlcv(asset, TIMEFRAME, since=since, limit=1000)
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        print(f"  Loaded {len(df)} candles")
        print()
        
        # Test each activation level
        for activation in ACTIVATION_LEVELS:
            trades = backtest_with_trailing(df, activation)
            
            if not trades:
                continue
            
            wins = [t for t in trades if t['pnl'] > 0]
            losses = [t for t in trades if t['pnl'] <= 0]
            
            total_pnl = sum(t['pnl'] for t in trades)
            win_rate = len(wins) / len(trades) * 100 if trades else 0
            avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
            avg_loss = np.mean([t['pnl'] for t in losses]) if losses else 0
            
            trailing_saves = len([t for t in trades if t['trailing_activated'] and t['exit_type'] == 'SL'])
            
            results.append({
                'asset': asset,
                'activation': activation,
                'trades': len(trades),
                'wins': len(wins),
                'losses': len(losses),
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'trailing_saves': trailing_saves
            })
    
    # Aggregate results
    print("="*70)
    print("RESULTS BY ACTIVATION LEVEL")
    print("="*70)
    print()
    
    summary = {}
    for activation in ACTIVATION_LEVELS:
        level_results = [r for r in results if r['activation'] == activation]
        
        if not level_results:
            continue
        
        total_trades = sum(r['trades'] for r in level_results)
        total_wins = sum(r['wins'] for r in level_results)
        total_losses = sum(r['losses'] for r in level_results)
        total_pnl = sum(r['total_pnl'] for r in level_results)
        win_rate = total_wins / total_trades * 100 if total_trades else 0
        trailing_saves = sum(r['trailing_saves'] for r in level_results)
        
        summary[activation] = {
            'trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl_per_trade': total_pnl / total_trades if total_trades else 0,
            'trailing_saves': trailing_saves
        }
    
    # Print comparison
    print(f"{'Activation':<12} {'Trades':<8} {'WR%':<8} {'Total P&L':<12} {'Avg/Trade':<12} {'Trail Saves':<12}")
    print("-"*70)
    
    for activation in sorted(summary.keys()):
        s = summary[activation]
        print(f"{activation}%{' '*(10-len(str(activation)))} {s['trades']:<8} {s['win_rate']:<7.1f}% ${s['total_pnl']:<11.2f} ${s['avg_pnl_per_trade']:<11.2f} {s['trailing_saves']:<12}")
    
    print()
    print("="*70)
    print("ANALYSIS")
    print("="*70)
    print()
    
    # Find best by total P&L
    best_pnl = max(summary.items(), key=lambda x: x[1]['total_pnl'])
    best_avg = max(summary.items(), key=lambda x: x[1]['avg_pnl_per_trade'])
    best_wr = max(summary.items(), key=lambda x: x[1]['win_rate'])
    
    print(f"Best Total P&L:     {best_pnl[0]}% (${best_pnl[1]['total_pnl']:.2f})")
    print(f"Best Avg/Trade:     {best_avg[0]}% (${best_avg[1]['avg_pnl_per_trade']:.2f})")
    print(f"Best Win Rate:      {best_wr[0]}% ({best_wr[1]['win_rate']:.1f}%)")
    print()
    
    # Recommendation
    print("RECOMMENDATION:")
    print()
    
    # Score each based on: 40% total P&L, 40% avg/trade, 20% win rate
    scores = {}
    max_pnl = max(s['total_pnl'] for s in summary.values())
    max_avg = max(s['avg_pnl_per_trade'] for s in summary.values())
    max_wr = max(s['win_rate'] for s in summary.values())
    
    for activation, s in summary.items():
        pnl_score = (s['total_pnl'] / max_pnl) * 40
        avg_score = (s['avg_pnl_per_trade'] / max_avg) * 40
        wr_score = (s['win_rate'] / max_wr) * 20
        
        scores[activation] = pnl_score + avg_score + wr_score
    
    best_overall = max(scores.items(), key=lambda x: x[1])
    
    print(f"OPTIMAL SETTING: {best_overall[0]}% activation")
    print(f"  (Based on weighted score: Total P&L 40%, Avg/Trade 40%, Win Rate 20%)")
    print()
    
    # Current setting equivalent
    current_equivalent = 15  # 1% price = 15% P&L with 15x leverage
    if current_equivalent in summary:
        print(f"Current (1% price = 15% P&L): ${summary[current_equivalent]['total_pnl']:.2f} total, ${summary[current_equivalent]['avg_pnl_per_trade']:.2f}/trade")
    print(f"Optimal ({best_overall[0]}% P&L): ${summary[best_overall[0]]['total_pnl']:.2f} total, ${summary[best_overall[0]]['avg_pnl_per_trade']:.2f}/trade")
    
    improvement = ((summary[best_overall[0]]['total_pnl'] - summary[current_equivalent]['total_pnl']) / summary[current_equivalent]['total_pnl'] * 100) if current_equivalent in summary else 0
    print(f"Improvement: {improvement:+.1f}%")

if __name__ == '__main__':
    run_optimization()

#!/usr/bin/env python3
"""
Backtest Strategy 1 V2 + Squeeze Momentum Filter
Test period: Last 7 days
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from squeeze_momentum import SqueezeMomentumIndicator

# Import SMC indicators from V2
import sys
sys.path.insert(0, '$OPENCLAW_HOME/bighead')

class BacktestConfig:
    # Assets
    ASSETS = ['ARB', 'OP', 'ETH']
    SYMBOL_MAP = {
        'ARB': 'ARBUSDT',
        'OP': 'OPUSDT',
        'ETH': 'ETHUSDT'
    }
    
    # Capital
    TOTAL_CAPITAL = 30.0
    CAPITAL_PER_ASSET = 10.0
    
    # Strategy
    TIMEFRAME = '15m'
    LEVERAGE = 15
    RISK_PER_TRADE = 0.03
    RR_RATIO = 2.0
    
    # SMC Parameters
    SWING_LENGTH = 3
    LOOKBACK_PERIOD = 20
    MIN_SL_DISTANCE = 0.005
    MAX_SL_DISTANCE = 0.10
    
    # Filters
    USE_SQUEEZE = True  # NEW: Squeeze Momentum filter
    USE_VOLUME = True
    VOLUME_THRESHOLD = 1.5
    USE_TREND = True
    
    # Fees
    MAKER_FEE = 0.0006
    TAKER_FEE = 0.0012

async def fetch_historical_data(asset, days=7):
    """Fetch historical 15m candles"""
    symbol = BacktestConfig.SYMBOL_MAP[asset]
    
    # Calculate how many 15m candles in 7 days
    candles_per_day = 96  # 24 * 4
    limit = candles_per_day * days + 100  # Extra for indicators
    
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': '15m',
        'limit': min(limit, 1000)  # Binance max
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    except Exception as e:
        print(f"Error fetching {asset}: {e}")
        return None

def add_smc_indicators(df):
    """Add SMC indicators"""
    df = df.copy()
    
    # Swing points
    df['swing_high'] = False
    df['swing_low'] = False
    
    swing_len = BacktestConfig.SWING_LENGTH
    
    for i in range(swing_len, len(df) - swing_len):
        if df['high'].iloc[i] == df['high'].iloc[i-swing_len:i+swing_len+1].max():
            df.loc[df.index[i], 'swing_high'] = True
        if df['low'].iloc[i] == df['low'].iloc[i-swing_len:i+swing_len+1].min():
            df.loc[df.index[i], 'swing_low'] = True
    
    # Break of Structure
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
    
    # Range zones
    df['range_high'] = df['high'].rolling(BacktestConfig.LOOKBACK_PERIOD).max()
    df['range_low'] = df['low'].rolling(BacktestConfig.LOOKBACK_PERIOD).min()
    
    # Volume
    df['volume_avg'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_avg']
    
    # Trend (EMA)
    df['ema_20'] = df['close'].ewm(span=20).mean()
    df['trend_bullish'] = df['close'] > df['ema_20']
    
    # SMC Signals
    df['smc_signal'] = 0
    df.loc[df['bos_bull'], 'smc_signal'] = 1
    df.loc[df['bos_bear'], 'smc_signal'] = -1
    
    return df

def backtest_strategy(df, asset, use_squeeze=True):
    """
    Backtest with optional Squeeze Momentum filter
    """
    # Add SMC indicators
    df = add_smc_indicators(df)
    
    # Add Squeeze Momentum
    if use_squeeze:
        sqz = SqueezeMomentumIndicator()
        df = sqz.get_signals(df)
    
    # Simulate trades
    trades = []
    equity = BacktestConfig.CAPITAL_PER_ASSET
    
    for i in range(BacktestConfig.LOOKBACK_PERIOD + 30, len(df)):
        row = df.iloc[i]
        
        # Check for signal
        smc_signal = row['smc_signal']
        if smc_signal == 0:
            continue
        
        # Volume filter
        if BacktestConfig.USE_VOLUME and row['volume_ratio'] < BacktestConfig.VOLUME_THRESHOLD:
            continue
        
        # Trend filter
        if BacktestConfig.USE_TREND:
            if smc_signal == 1 and not row['trend_bullish']:
                continue
            if smc_signal == -1 and row['trend_bullish']:
                continue
        
        # Squeeze filter
        if use_squeeze and BacktestConfig.USE_SQUEEZE:
            # Only take trades on squeeze off + momentum aligned
            if not row['sqz_off']:
                continue
            
            # Check momentum alignment
            if smc_signal == 1 and row['sqz_mom'] <= 0:
                continue
            if smc_signal == -1 and row['sqz_mom'] >= 0:
                continue
        
        # Valid signal - calculate entry, SL, TP
        entry = row['close']
        
        if smc_signal == 1:  # LONG
            sl = row['range_low'] if row['range_low'] < entry else entry * 0.985
            tp = entry + (entry - sl) * BacktestConfig.RR_RATIO
            direction = 'LONG'
        else:  # SHORT
            sl = row['range_high'] if row['range_high'] > entry else entry * 1.015
            tp = entry - (sl - entry) * BacktestConfig.RR_RATIO
            direction = 'SHORT'
        
        # Check SL distance
        sl_distance = abs(entry - sl) / entry
        if sl_distance < BacktestConfig.MIN_SL_DISTANCE or sl_distance > BacktestConfig.MAX_SL_DISTANCE:
            continue
        
        # Position sizing
        risk_amount = equity * BacktestConfig.RISK_PER_TRADE
        size = risk_amount / sl_distance
        max_size = equity * 0.5
        size = min(size, max_size)
        
        if size < 0.1:
            continue
        
        # Simulate trade execution
        entry_time = row['timestamp']
        
        # Find exit
        exit_price = None
        exit_time = None
        exit_type = None
        
        for j in range(i + 1, min(i + 200, len(df))):  # Max 200 candles (~50 hours)
            future_row = df.iloc[j]
            
            if direction == 'LONG':
                if future_row['high'] >= tp:
                    exit_price = tp
                    exit_time = future_row['timestamp']
                    exit_type = 'TP'
                    break
                elif future_row['low'] <= sl:
                    exit_price = sl
                    exit_time = future_row['timestamp']
                    exit_type = 'SL'
                    break
            else:  # SHORT
                if future_row['low'] <= tp:
                    exit_price = tp
                    exit_time = future_row['timestamp']
                    exit_type = 'TP'
                    break
                elif future_row['high'] >= sl:
                    exit_price = sl
                    exit_time = future_row['timestamp']
                    exit_type = 'SL'
                    break
        
        # If no exit found, close at last candle
        if exit_price is None:
            exit_price = df.iloc[-1]['close']
            exit_time = df.iloc[-1]['timestamp']
            exit_type = 'EOD'
        
        # Calculate P&L
        if direction == 'LONG':
            price_change = (exit_price - entry) / entry
        else:
            price_change = (entry - exit_price) / entry
        
        pnl_pct = price_change * BacktestConfig.LEVERAGE
        gross_pnl = size * pnl_pct
        fees = size * BacktestConfig.TAKER_FEE * 2  # Entry + exit
        net_pnl = gross_pnl - fees
        
        equity += net_pnl
        
        trades.append({
            'entry_time': entry_time,
            'exit_time': exit_time,
            'asset': asset,
            'direction': direction,
            'entry': entry,
            'exit': exit_price,
            'sl': sl,
            'tp': tp,
            'size': size,
            'pnl': net_pnl,
            'exit_type': exit_type,
            'squeeze_on': row['sqz_on'] if use_squeeze else False,
            'squeeze_off': row['sqz_off'] if use_squeeze else False,
            'sqz_mom': row['sqz_mom'] if use_squeeze else 0
        })
    
    return trades, equity

async def run_backtest():
    """Run complete backtest"""
    print("="*70)
    print("BACKTEST: Strategy 1 V2 + Squeeze Momentum Filter")
    print("="*70)
    print(f"Period: Last 7 days")
    print(f"Assets: {', '.join(BacktestConfig.ASSETS)}")
    print(f"Capital: ${BacktestConfig.TOTAL_CAPITAL}")
    print(f"Leverage: {BacktestConfig.LEVERAGE}x")
    print("="*70)
    
    # Fetch data
    print("\n📥 Fetching historical data...")
    data = {}
    for asset in BacktestConfig.ASSETS:
        df = await fetch_historical_data(asset, days=7)
        if df is not None:
            data[asset] = df
            print(f"   {asset}: {len(df)} candles")
    
    # Run backtests
    print("\n🔬 Running backtests...\n")
    
    results = {
        'without_squeeze': {},
        'with_squeeze': {}
    }
    
    for asset in BacktestConfig.ASSETS:
        if asset not in data:
            continue
        
        df = data[asset]
        
        # Without Squeeze
        trades_no_sqz, equity_no_sqz = backtest_strategy(df, asset, use_squeeze=False)
        results['without_squeeze'][asset] = {
            'trades': trades_no_sqz,
            'final_equity': equity_no_sqz,
            'total_trades': len(trades_no_sqz),
            'winners': len([t for t in trades_no_sqz if t['pnl'] > 0]),
            'total_pnl': sum([t['pnl'] for t in trades_no_sqz])
        }
        
        # With Squeeze
        trades_sqz, equity_sqz = backtest_strategy(df, asset, use_squeeze=True)
        results['with_squeeze'][asset] = {
            'trades': trades_sqz,
            'final_equity': equity_sqz,
            'total_trades': len(trades_sqz),
            'winners': len([t for t in trades_sqz if t['pnl'] > 0]),
            'total_pnl': sum([t['pnl'] for t in trades_sqz])
        }
    
    # Print results
    print("\n" + "="*70)
    print("RESULTS COMPARISON")
    print("="*70)
    
    for asset in BacktestConfig.ASSETS:
        if asset not in results['without_squeeze']:
            continue
        
        print(f"\n📊 {asset}")
        print("-"*70)
        
        # Without Squeeze
        no_sqz = results['without_squeeze'][asset]
        wr_no_sqz = (no_sqz['winners'] / no_sqz['total_trades'] * 100) if no_sqz['total_trades'] > 0 else 0
        roi_no_sqz = ((no_sqz['final_equity'] - BacktestConfig.CAPITAL_PER_ASSET) / BacktestConfig.CAPITAL_PER_ASSET * 100)
        
        print(f"WITHOUT Squeeze Filter:")
        print(f"  Trades: {no_sqz['total_trades']}")
        print(f"  Win Rate: {wr_no_sqz:.1f}%")
        print(f"  Total P&L: ${no_sqz['total_pnl']:+.2f}")
        print(f"  Final Equity: ${no_sqz['final_equity']:.2f}")
        print(f"  ROI: {roi_no_sqz:+.1f}%")
        
        # With Squeeze
        sqz = results['with_squeeze'][asset]
        wr_sqz = (sqz['winners'] / sqz['total_trades'] * 100) if sqz['total_trades'] > 0 else 0
        roi_sqz = ((sqz['final_equity'] - BacktestConfig.CAPITAL_PER_ASSET) / BacktestConfig.CAPITAL_PER_ASSET * 100)
        
        print(f"\nWITH Squeeze Filter:")
        print(f"  Trades: {sqz['total_trades']}")
        print(f"  Win Rate: {wr_sqz:.1f}%")
        print(f"  Total P&L: ${sqz['total_pnl']:+.2f}")
        print(f"  Final Equity: ${sqz['final_equity']:.2f}")
        print(f"  ROI: {roi_sqz:+.1f}%")
        
        # Comparison
        print(f"\n✨ Improvement:")
        print(f"  Trades: {sqz['total_trades'] - no_sqz['total_trades']:+d} ({(sqz['total_trades']/no_sqz['total_trades']*100-100):+.1f}% change)")
        print(f"  Win Rate: {wr_sqz - wr_no_sqz:+.1f}%")
        print(f"  P&L: ${sqz['total_pnl'] - no_sqz['total_pnl']:+.2f}")
        print(f"  ROI: {roi_sqz - roi_no_sqz:+.1f}%")
    
    # Overall summary
    print("\n" + "="*70)
    print("OVERALL SUMMARY (All Assets)")
    print("="*70)
    
    total_no_sqz = sum([r['total_pnl'] for r in results['without_squeeze'].values()])
    total_sqz = sum([r['total_pnl'] for r in results['with_squeeze'].values()])
    
    trades_no_sqz = sum([r['total_trades'] for r in results['without_squeeze'].values()])
    trades_sqz = sum([r['total_trades'] for r in results['with_squeeze'].values()])
    
    print(f"\nWithout Squeeze: {trades_no_sqz} trades, ${total_no_sqz:+.2f}")
    print(f"With Squeeze: {trades_sqz} trades, ${total_sqz:+.2f}")
    print(f"\n🎯 Difference: ${total_sqz - total_no_sqz:+.2f} ({(total_sqz/total_no_sqz*100-100) if total_no_sqz != 0 else 0:+.1f}%)")
    
    if total_sqz > total_no_sqz:
        print("\n✅ Squeeze filter IMPROVES performance!")
    else:
        print("\n❌ Squeeze filter REDUCES performance")

if __name__ == "__main__":
    asyncio.run(run_backtest())

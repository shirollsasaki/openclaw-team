#!/usr/bin/env python3
"""
Smart Money Concepts Strategy Optimization
Tests multiple timeframes and parameters to find best configuration
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
import json
from itertools import product

class StrategyOptimizer:
    def __init__(self):
        self.results = []
        
    async def fetch_ohlcv(self, interval, hours=168):  # 7 days
        """Fetch OHLCV data from Binance"""
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)
        
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': 'ETHUSDT',
            'interval': interval,
            'startTime': start_time,
            'endTime': end_time,
            'limit': 1000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        return df
    
    def detect_swing_points(self, df, length):
        """Detect swing highs and lows"""
        df = df.copy()
        df['swing_high'] = False
        df['swing_low'] = False
        
        for i in range(length, len(df) - length):
            if df['high'].iloc[i] == df['high'].iloc[i-length:i+length+1].max():
                df.loc[df.index[i], 'swing_high'] = True
            if df['low'].iloc[i] == df['low'].iloc[i-length:i+length+1].min():
                df.loc[df.index[i], 'swing_low'] = True
        
        return df
    
    def detect_structure_breaks(self, df):
        """Detect BOS and CHoCH"""
        df = df.copy()
        df['bos_bull'] = False
        df['bos_bear'] = False
        df['trend'] = 0
        
        last_high = None
        last_low = None
        trend = 0
        
        for i in range(len(df)):
            if df['swing_high'].iloc[i]:
                last_high = df['high'].iloc[i]
            if df['swing_low'].iloc[i]:
                last_low = df['low'].iloc[i]
            
            if last_high is not None and last_low is not None:
                if df['close'].iloc[i] > last_high:
                    df.loc[df.index[i], 'bos_bull'] = True
                    trend = 1
                elif df['close'].iloc[i] < last_low:
                    df.loc[df.index[i], 'bos_bear'] = True
                    trend = -1
            
            df.loc[df.index[i], 'trend'] = trend
        
        return df
    
    def calculate_zones(self, df, lookback):
        """Calculate premium/discount zones"""
        df = df.copy()
        df['range_high'] = df['high'].rolling(lookback).max()
        df['range_low'] = df['low'].rolling(lookback).min()
        df['equilibrium'] = (df['range_high'] + df['range_low']) / 2
        
        df['premium_zone'] = df['equilibrium'] + (df['range_high'] - df['equilibrium']) * 0.5
        df['discount_zone'] = df['equilibrium'] - (df['equilibrium'] - df['range_low']) * 0.5
        
        df['in_premium'] = df['close'] > df['premium_zone']
        df['in_discount'] = df['close'] < df['discount_zone']
        df['in_equilibrium'] = (~df['in_premium']) & (~df['in_discount'])
        
        return df
    
    def detect_order_blocks(self, df):
        """Detect order blocks"""
        df = df.copy()
        df['bullish_ob'] = False
        df['bearish_ob'] = False
        
        for i in range(3, len(df)):
            # Bullish OB
            if (df['close'].iloc[i] > df['close'].iloc[i-1] and
                df['close'].iloc[i-1] < df['open'].iloc[i-1] and
                df['close'].iloc[i] - df['close'].iloc[i-3] > df['close'].iloc[i] * 0.003):
                df.loc[df.index[i], 'bullish_ob'] = True
            
            # Bearish OB
            if (df['close'].iloc[i] < df['close'].iloc[i-1] and
                df['close'].iloc[i-1] > df['open'].iloc[i-1] and
                df['close'].iloc[i-3] - df['close'].iloc[i] > df['close'].iloc[i] * 0.003):
                df.loc[df.index[i], 'bearish_ob'] = True
        
        return df
    
    def generate_signals(self, df, use_zones=True, use_ob=True, use_trend=True):
        """Generate signals with configurable filters"""
        df = df.copy()
        df['signal'] = 0
        
        for i in range(10, len(df)):
            # LONG conditions
            long_structure = df['bos_bull'].iloc[i]
            long_zone = not use_zones or df['in_discount'].iloc[i] or df['in_equilibrium'].iloc[i]
            long_ob = not use_ob or df['bullish_ob'].iloc[i-2:i+1].any()
            long_trend = not use_trend or df['trend'].iloc[i] >= 0
            
            if long_structure and long_zone and long_ob and long_trend:
                df.loc[df.index[i], 'signal'] = 1
            
            # SHORT conditions
            short_structure = df['bos_bear'].iloc[i]
            short_zone = not use_zones or df['in_premium'].iloc[i] or df['in_equilibrium'].iloc[i]
            short_ob = not use_ob or df['bearish_ob'].iloc[i-2:i+1].any()
            short_trend = not use_trend or df['trend'].iloc[i] <= 0
            
            if short_structure and short_zone and short_ob and short_trend:
                df.loc[df.index[i], 'signal'] = -1
        
        return df
    
    def backtest(self, df, config):
        """Run backtest with given configuration"""
        capital = 10.0
        starting_capital = capital
        risk_pct = config['risk_pct']
        leverage = config['leverage']
        rr_ratio = config['rr_ratio']
        
        trades = []
        open_positions = []
        max_positions = 2
        
        for i in range(10, len(df)):
            # Update open positions
            closed = []
            for pos in open_positions:
                high = df['high'].iloc[i]
                low = df['low'].iloc[i]
                
                if pos['direction'] == 'LONG':
                    if high >= pos['tp']:
                        pos['exit_price'] = pos['tp']
                        pos['exit_reason'] = 'TP'
                        closed.append(pos)
                    elif low <= pos['sl']:
                        pos['exit_price'] = pos['sl']
                        pos['exit_reason'] = 'SL'
                        closed.append(pos)
                else:
                    if low <= pos['tp']:
                        pos['exit_price'] = pos['tp']
                        pos['exit_reason'] = 'TP'
                        closed.append(pos)
                    elif high >= pos['sl']:
                        pos['exit_price'] = pos['sl']
                        pos['exit_reason'] = 'SL'
                        closed.append(pos)
            
            for pos in closed:
                if pos['direction'] == 'LONG':
                    pnl_pct = (pos['exit_price'] - pos['entry']) / pos['entry']
                else:
                    pnl_pct = (pos['entry'] - pos['exit_price']) / pos['entry']
                
                pnl_pct *= leverage
                pnl_usd = pos['size'] * pnl_pct
                fee = pos['size'] * 0.002
                pnl_usd -= fee
                
                capital += pnl_usd
                pos['pnl'] = pnl_usd
                trades.append(pos)
                open_positions.remove(pos)
            
            # Check for new signals
            if df['signal'].iloc[i] != 0 and len(open_positions) < max_positions and capital > 0.1:
                signal = df['signal'].iloc[i]
                entry = df['close'].iloc[i]
                
                if signal == 1:  # LONG
                    sl = df['range_low'].iloc[i]
                    if sl >= entry:
                        sl = entry * 0.98
                    tp = entry + (entry - sl) * rr_ratio
                    direction = 'LONG'
                else:  # SHORT
                    sl = df['range_high'].iloc[i]
                    if sl <= entry:
                        sl = entry * 1.02
                    tp = entry - (sl - entry) * rr_ratio
                    direction = 'SHORT'
                
                sl_distance = abs(entry - sl) / entry
                if sl_distance > 0.001:  # Min 0.1% SL
                    risk_amount = capital * risk_pct
                    size = min(risk_amount / sl_distance, capital)
                    
                    if size >= 0.1:
                        open_positions.append({
                            'entry': entry,
                            'sl': sl,
                            'tp': tp,
                            'size': size,
                            'direction': direction
                        })
        
        # Close remaining positions
        for pos in open_positions:
            pos['exit_price'] = df['close'].iloc[-1]
            pos['exit_reason'] = 'EOD'
            
            if pos['direction'] == 'LONG':
                pnl_pct = (pos['exit_price'] - pos['entry']) / pos['entry']
            else:
                pnl_pct = (pos['entry'] - pos['exit_price']) / pos['entry']
            
            pnl_pct *= leverage
            pnl_usd = pos['size'] * pnl_pct - pos['size'] * 0.002
            capital += pnl_usd
            pos['pnl'] = pnl_usd
            trades.append(pos)
        
        # Calculate metrics
        if not trades:
            return None
        
        wins = [t for t in trades if t['pnl'] > 0]
        losses = [t for t in trades if t['pnl'] <= 0]
        
        win_rate = len(wins) / len(trades) if trades else 0
        avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
        profit_factor = abs(sum(t['pnl'] for t in wins) / sum(t['pnl'] for t in losses)) if losses and sum(t['pnl'] for t in losses) != 0 else 0
        
        return {
            'config': config,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'final_capital': capital,
            'pnl': capital - starting_capital,
            'pnl_pct': (capital / starting_capital - 1) * 100,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'wins': len(wins),
            'losses': len(losses)
        }
    
    async def optimize(self):
        """Test multiple configurations"""
        # Timeframes to test
        timeframes = [
            ('5m', 5),
            ('15m', 15),
            ('30m', 30),
            ('1h', 60),
        ]
        
        # Parameter grid
        swing_lengths = [3, 5]
        lookbacks = [10, 20, 30]
        leverages = [5, 10, 15]
        risk_pcts = [0.01, 0.02, 0.03]  # 1%, 2%, 3%
        rr_ratios = [1.5, 2, 2.5]
        filter_combinations = [
            {'zones': True, 'ob': True, 'trend': True},
            {'zones': True, 'ob': False, 'trend': True},
            {'zones': False, 'ob': True, 'trend': True},
        ]
        
        print("🔄 Starting optimization across timeframes...\n")
        
        for interval, tf_mins in timeframes:
            print(f"📊 Testing {interval} timeframe...")
            
            try:
                df = await self.fetch_ohlcv(interval, hours=168)
                print(f"   Loaded {len(df)} candles")
                
                best_result = None
                best_pnl = -float('inf')
                
                # Test configurations
                for swing_len, lookback, leverage, risk_pct, rr, filters in product(
                    swing_lengths, lookbacks, leverages, risk_pcts, rr_ratios, filter_combinations
                ):
                    # Prepare data
                    test_df = df.copy()
                    test_df = self.detect_swing_points(test_df, swing_len)
                    test_df = self.detect_structure_breaks(test_df)
                    test_df = self.calculate_zones(test_df, lookback)
                    test_df = self.detect_order_blocks(test_df)
                    test_df = self.generate_signals(test_df, filters['zones'], filters['ob'], filters['trend'])
                    
                    config = {
                        'timeframe': interval,
                        'swing_length': swing_len,
                        'lookback': lookback,
                        'leverage': leverage,
                        'risk_pct': risk_pct,
                        'rr_ratio': rr,
                        'use_zones': filters['zones'],
                        'use_ob': filters['ob'],
                        'use_trend': filters['trend']
                    }
                    
                    result = self.backtest(test_df, config)
                    
                    if result and result['pnl'] > best_pnl:
                        best_pnl = result['pnl']
                        best_result = result
                
                if best_result:
                    self.results.append(best_result)
                    print(f"   ✅ Best: {best_result['pnl_pct']:+.2f}% | {best_result['total_trades']} trades | {best_result['win_rate']*100:.1f}% WR")
                else:
                    print(f"   ❌ No profitable configs found")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n" + "="*80)
        
    def print_results(self):
        """Print optimization results"""
        if not self.results:
            print("❌ No results to display")
            return
        
        # Sort by P&L
        self.results.sort(key=lambda x: x['pnl'], reverse=True)
        
        print("📊 OPTIMIZATION RESULTS - TOP 5 CONFIGURATIONS")
        print("="*80)
        
        for i, result in enumerate(self.results[:5], 1):
            config = result['config']
            
            print(f"\n#{i} RANK — {config['timeframe'].upper()} TIMEFRAME")
            print(f"   💰 P&L: ${result['pnl']:+.2f} ({result['pnl_pct']:+.2f}%)")
            print(f"   📈 Trades: {result['total_trades']} | Win Rate: {result['win_rate']*100:.1f}%")
            print(f"   📊 Profit Factor: {result['profit_factor']:.2f}")
            print(f"   💵 Avg Win: ${result['avg_win']:.2f} | Avg Loss: ${result['avg_loss']:.2f}")
            print(f"   ⚙️  Settings:")
            print(f"      - Swing Length: {config['swing_length']}")
            print(f"      - Lookback: {config['lookback']}")
            print(f"      - Leverage: {config['leverage']}x")
            print(f"      - Risk per Trade: {config['risk_pct']*100:.1f}%")
            print(f"      - Risk:Reward: {config['rr_ratio']}:1")
            print(f"      - Filters: Zones={config['use_zones']}, OB={config['use_ob']}, Trend={config['use_trend']}")
        
        print("\n" + "="*80)
        
        # Best overall
        best = self.results[0]
        print(f"\n🏆 RECOMMENDED CONFIGURATION")
        print(f"   Timeframe: {best['config']['timeframe']}")
        print(f"   Expected Return: {best['pnl_pct']:+.2f}% over 7 days")
        print(f"   Trade Frequency: ~{best['total_trades']/7:.1f} trades per day")
        print(f"   Win Rate: {best['win_rate']*100:.1f}%")

async def main():
    optimizer = StrategyOptimizer()
    await optimizer.optimize()
    optimizer.print_results()

if __name__ == "__main__":
    asyncio.run(main())

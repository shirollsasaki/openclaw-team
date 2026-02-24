#!/usr/bin/env python3
"""
Smart Money Concepts Backtest - Last 5 Hours
Simulates trading strategy on ETH/USD with $10 starting capital
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
import json

class SMCBacktester:
    def __init__(self, starting_capital=10):
        self.starting_capital = starting_capital
        self.capital = starting_capital
        self.trades = []
        self.open_positions = []
        self.max_positions = 2
        self.risk_per_trade = 0.02  # 2% risk
        self.leverage = 10
        
    async def fetch_ohlcv(self, hours=5):
        """Fetch 5-min OHLCV data from Binance"""
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)
        
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': 'ETHUSDT',
            'interval': '5m',
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
    
    def detect_swing_points(self, df, length=3):
        """Detect swing highs and lows"""
        df['swing_high'] = False
        df['swing_low'] = False
        df['swing_high_price'] = None
        df['swing_low_price'] = None
        
        for i in range(length, len(df) - length):
            # Swing high
            if df['high'].iloc[i] == df['high'].iloc[i-length:i+length+1].max():
                df.loc[df.index[i], 'swing_high'] = True
                df.loc[df.index[i], 'swing_high_price'] = df['high'].iloc[i]
            
            # Swing low
            if df['low'].iloc[i] == df['low'].iloc[i-length:i+length+1].min():
                df.loc[df.index[i], 'swing_low'] = True
                df.loc[df.index[i], 'swing_low_price'] = df['low'].iloc[i]
        
        return df
    
    def detect_structure_breaks(self, df):
        """Detect BOS and CHoCH"""
        df['bos_bull'] = False
        df['bos_bear'] = False
        df['choch_bull'] = False
        df['choch_bear'] = False
        df['trend'] = 0  # 1 = bullish, -1 = bearish
        
        last_high = None
        last_low = None
        trend = 0
        
        for i in range(len(df)):
            # Update last swing points
            if df['swing_high'].iloc[i]:
                last_high = df['high'].iloc[i]
            if df['swing_low'].iloc[i]:
                last_low = df['low'].iloc[i]
            
            if last_high is not None and last_low is not None:
                # Bullish break of structure
                if df['close'].iloc[i] > last_high:
                    if trend == -1:
                        df.loc[df.index[i], 'choch_bull'] = True
                    else:
                        df.loc[df.index[i], 'bos_bull'] = True
                    trend = 1
                
                # Bearish break of structure
                elif df['close'].iloc[i] < last_low:
                    if trend == 1:
                        df.loc[df.index[i], 'choch_bear'] = True
                    else:
                        df.loc[df.index[i], 'bos_bear'] = True
                    trend = -1
            
            df.loc[df.index[i], 'trend'] = trend
        
        return df
    
    def calculate_premium_discount(self, df, lookback=20):
        """Calculate premium/discount zones"""
        df['range_high'] = df['high'].rolling(lookback).max()
        df['range_low'] = df['low'].rolling(lookback).min()
        df['equilibrium'] = (df['range_high'] + df['range_low']) / 2
        
        # Wider zones: top 40% is premium, bottom 40% is discount
        df['premium_zone'] = df['range_high'] - (df['range_high'] - df['equilibrium']) * 0.6
        df['discount_zone'] = df['range_low'] + (df['equilibrium'] - df['range_low']) * 0.6
        
        df['in_premium'] = df['close'] > df['premium_zone']
        df['in_discount'] = df['close'] < df['discount_zone']
        
        return df
    
    def detect_order_blocks(self, df):
        """Simplified order block detection"""
        df['bullish_ob'] = False
        df['bearish_ob'] = False
        
        for i in range(3, len(df)):
            # Bullish OB: strong up move after down candle
            if (df['close'].iloc[i] > df['close'].iloc[i-1] and
                df['close'].iloc[i-1] < df['open'].iloc[i-1] and
                df['close'].iloc[i] - df['close'].iloc[i-3] > df['close'].iloc[i] * 0.005):  # 0.5% move
                df.loc[df.index[i], 'bullish_ob'] = True
            
            # Bearish OB: strong down move after up candle
            if (df['close'].iloc[i] < df['close'].iloc[i-1] and
                df['close'].iloc[i-1] > df['open'].iloc[i-1] and
                df['close'].iloc[i-3] - df['close'].iloc[i] > df['close'].iloc[i] * 0.005):
                df.loc[df.index[i], 'bearish_ob'] = True
        
        return df
    
    def generate_signals(self, df):
        """Generate entry signals based on SMC logic"""
        df['signal'] = 0  # 1 = long, -1 = short, 0 = no signal
        
        for i in range(10, len(df)):
            # LONG signal: bullish structure break (simplified - no zone filter for testing)
            if df['bos_bull'].iloc[i] or df['choch_bull'].iloc[i]:
                # But check we're not in extreme premium
                if df['close'].iloc[i] < df['range_high'].iloc[i]:
                    df.loc[df.index[i], 'signal'] = 1
            
            # SHORT signal: bearish structure break
            elif df['bos_bear'].iloc[i] or df['choch_bear'].iloc[i]:
                # But check we're not in extreme discount
                if df['close'].iloc[i] > df['range_low'].iloc[i]:
                    df.loc[df.index[i], 'signal'] = -1
        
        return df
    
    def calculate_position_size(self, entry_price, sl_price):
        """Calculate position size based on risk management"""
        risk_amount = self.capital * self.risk_per_trade
        sl_distance = abs(entry_price - sl_price) / entry_price
        
        if sl_distance == 0:
            return 0
        
        position_size = risk_amount / sl_distance
        position_size = min(position_size, self.capital)  # Cap at available capital
        
        return round(position_size, 2)
    
    def simulate_trade(self, df, i):
        """Simulate a trade"""
        signal = df['signal'].iloc[i]
        if signal == 0 or len(self.open_positions) >= self.max_positions:
            return
        
        entry_price = df['close'].iloc[i]
        
        if signal == 1:  # LONG
            sl_price = df['range_low'].iloc[i]  # SL at discount zone low
            tp_price = entry_price + (entry_price - sl_price) * 2  # 2:1 RR
            direction = 'LONG'
        else:  # SHORT
            sl_price = df['range_high'].iloc[i]  # SL at premium zone high
            tp_price = entry_price - (sl_price - entry_price) * 2  # 2:1 RR
            direction = 'SHORT'
        
        position_size = self.calculate_position_size(entry_price, sl_price)
        
        if position_size < 0.1:  # Min position size
            return
        
        trade = {
            'entry_time': df['timestamp'].iloc[i],
            'entry_index': i,
            'direction': direction,
            'entry_price': entry_price,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'position_size': position_size,
            'status': 'open'
        }
        
        self.open_positions.append(trade)
    
    def update_positions(self, df, i):
        """Update open positions and check for exits"""
        closed_positions = []
        
        for pos in self.open_positions:
            current_price = df['close'].iloc[i]
            high = df['high'].iloc[i]
            low = df['low'].iloc[i]
            
            # Check TP/SL
            if pos['direction'] == 'LONG':
                if high >= pos['tp_price']:
                    pos['exit_price'] = pos['tp_price']
                    pos['exit_reason'] = 'TP'
                    pos['status'] = 'closed'
                elif low <= pos['sl_price']:
                    pos['exit_price'] = pos['sl_price']
                    pos['exit_reason'] = 'SL'
                    pos['status'] = 'closed'
            else:  # SHORT
                if low <= pos['tp_price']:
                    pos['exit_price'] = pos['tp_price']
                    pos['exit_reason'] = 'TP'
                    pos['status'] = 'closed'
                elif high >= pos['sl_price']:
                    pos['exit_price'] = pos['sl_price']
                    pos['exit_reason'] = 'SL'
                    pos['status'] = 'closed'
            
            if pos['status'] == 'closed':
                pos['exit_time'] = df['timestamp'].iloc[i]
                
                # Calculate PnL
                if pos['direction'] == 'LONG':
                    pnl_pct = (pos['exit_price'] - pos['entry_price']) / pos['entry_price']
                else:
                    pnl_pct = (pos['entry_price'] - pos['exit_price']) / pos['entry_price']
                
                pnl_pct *= self.leverage  # Apply leverage
                pnl_usd = pos['position_size'] * pnl_pct
                
                # Deduct fees (0.1% per trade, twice for entry+exit)
                fee = pos['position_size'] * 0.002
                pnl_usd -= fee
                
                pos['pnl_usd'] = round(pnl_usd, 2)
                pos['pnl_pct'] = round(pnl_pct * 100, 2)
                
                self.capital += pnl_usd
                self.trades.append(pos)
                closed_positions.append(pos)
        
        # Remove closed positions
        self.open_positions = [p for p in self.open_positions if p['status'] == 'open']
    
    def run_backtest(self, df):
        """Run full backtest"""
        print("🔄 Running Smart Money Concepts backtest...")
        
        # Apply indicators
        df = self.detect_swing_points(df, length=3)
        df = self.detect_structure_breaks(df)
        df = self.calculate_premium_discount(df, lookback=12)
        df = self.detect_order_blocks(df)
        df = self.generate_signals(df)
        
        # Debug: count signals
        bull_signals = df['signal'].eq(1).sum()
        bear_signals = df['signal'].eq(-1).sum()
        bos_bull_count = df['bos_bull'].sum()
        bos_bear_count = df['bos_bear'].sum()
        choch_bull_count = df['choch_bull'].sum()
        choch_bear_count = df['choch_bear'].sum()
        
        print(f"📊 Signal Analysis:")
        print(f"  BOS Bull: {bos_bull_count}, BOS Bear: {bos_bear_count}")
        print(f"  CHoCH Bull: {choch_bull_count}, CHoCH Bear: {choch_bear_count}")
        print(f"  Long Signals: {bull_signals}, Short Signals: {bear_signals}")
        
        # Simulate trading
        for i in range(12, len(df)):
            self.update_positions(df, i)
            self.simulate_trade(df, i)
        
        # Close any remaining positions at last price
        if self.open_positions:
            for pos in self.open_positions:
                pos['exit_price'] = df['close'].iloc[-1]
                pos['exit_time'] = df['timestamp'].iloc[-1]
                pos['exit_reason'] = 'EOD'
                pos['status'] = 'closed'
                
                if pos['direction'] == 'LONG':
                    pnl_pct = (pos['exit_price'] - pos['entry_price']) / pos['entry_price']
                else:
                    pnl_pct = (pos['entry_price'] - pos['exit_price']) / pos['entry_price']
                
                pnl_pct *= self.leverage
                pnl_usd = pos['position_size'] * pnl_pct
                fee = pos['position_size'] * 0.002
                pnl_usd -= fee
                
                pos['pnl_usd'] = round(pnl_usd, 2)
                pos['pnl_pct'] = round(pnl_pct * 100, 2)
                
                self.capital += pnl_usd
                self.trades.append(pos)
        
        return df
    
    def print_results(self):
        """Print backtest results"""
        print("\n" + "="*70)
        print("📊 SMART MONEY CONCEPTS BACKTEST RESULTS - LAST 5 HOURS")
        print("="*70)
        
        print(f"\n💰 CAPITAL")
        print(f"  Starting: ${self.starting_capital:.2f}")
        print(f"  Ending:   ${self.capital:.2f}")
        print(f"  P&L:      ${self.capital - self.starting_capital:.2f} ({((self.capital/self.starting_capital - 1) * 100):.2f}%)")
        
        if not self.trades:
            print("\n❌ No trades executed")
            return
        
        wins = [t for t in self.trades if t['pnl_usd'] > 0]
        losses = [t for t in self.trades if t['pnl_usd'] <= 0]
        
        print(f"\n📈 TRADES")
        print(f"  Total:    {len(self.trades)}")
        print(f"  Wins:     {len(wins)}")
        print(f"  Losses:   {len(losses)}")
        print(f"  Win Rate: {(len(wins)/len(self.trades)*100):.1f}%")
        
        if wins:
            avg_win = sum([t['pnl_usd'] for t in wins]) / len(wins)
            print(f"  Avg Win:  ${avg_win:.2f}")
        
        if losses:
            avg_loss = sum([t['pnl_usd'] for t in losses]) / len(losses)
            print(f"  Avg Loss: ${avg_loss:.2f}")
        
        print(f"\n🎯 TRADE LOG")
        print(f"  {'Time':<20} {'Dir':<6} {'Entry':<10} {'Exit':<10} {'Reason':<4} {'P&L':<10}")
        print(f"  {'-'*70}")
        
        for t in self.trades:
            time_str = t['entry_time'].strftime('%H:%M')
            pnl_str = f"${t['pnl_usd']:+.2f}"
            color = "✅" if t['pnl_usd'] > 0 else "❌"
            print(f"  {time_str:<20} {t['direction']:<6} ${t['entry_price']:<9.2f} ${t['exit_price']:<9.2f} {t['exit_reason']:<4} {color} {pnl_str:<10}")
        
        print("\n" + "="*70)
        
        # Risk metrics
        pnls = [t['pnl_usd'] for t in self.trades]
        max_drawdown = 0
        peak = self.starting_capital
        running_capital = self.starting_capital
        
        for pnl in pnls:
            running_capital += pnl
            if running_capital > peak:
                peak = running_capital
            drawdown = (peak - running_capital) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        print(f"\n⚠️  RISK METRICS")
        print(f"  Max Drawdown: {max_drawdown:.2f}%")
        
        if wins and losses:
            profit_factor = abs(sum([t['pnl_usd'] for t in wins]) / sum([t['pnl_usd'] for t in losses]))
            print(f"  Profit Factor: {profit_factor:.2f}")

async def main():
    backtester = SMCBacktester(starting_capital=10)
    
    # Fetch data (get 24h but only use last 5 hours for backtest)
    print("📡 Fetching ETH/USD 5-min data from Binance...")
    df = await backtester.fetch_ohlcv(hours=24)
    
    # Take only last 5 hours (60 candles)
    df = df.tail(60).reset_index(drop=True)
    print(f"✅ Loaded {len(df)} candles (last 5 hours)")
    
    # Run backtest
    df = backtester.run_backtest(df)
    
    # Print results
    backtester.print_results()
    
    # Save trade log
    if backtester.trades:
        trades_df = pd.DataFrame(backtester.trades)
        trades_df.to_csv('backtest_trades.csv', index=False)
        print(f"\n💾 Trade log saved to: backtest_trades.csv")

if __name__ == "__main__":
    asyncio.run(main())

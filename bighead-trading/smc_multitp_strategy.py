#!/usr/bin/env python3
"""
SMC Multi-TP Strategy (Simplified from Pine Script)
Core Logic:
- Signal: ALMA crossover/crossunder
- Multiple TPs: TP1 (1%), TP2 (1.5%), TP3 (2%)
- SL: 0.5%
- Partial exits at each TP level
"""

import pandas as pd
import numpy as np

class SMCMultiTPStrategy:
    """
    Simplified version of the Pine Script strategy
    
    Key Features:
    - ALMA(2) crossover for entry signals
    - 3 Take Profit levels with partial exits
    - 0.5% Stop Loss
    """
    
    def __init__(self):
        # MA Settings
        self.ma_type = 'ALMA'
        self.ma_period = 2
        self.alma_offset = 0.85
        self.alma_sigma = 5
        
        # Risk Management
        self.tp1_pct = 1.0    # 1%
        self.tp2_pct = 1.5    # 1.5%
        self.tp3_pct = 2.0    # 2%
        self.sl_pct = 0.5     # 0.5%
        
        # Position sizing at each TP
        self.tp1_qty = 50  # Close 50% at TP1
        self.tp2_qty = 30  # Close 30% at TP2
        self.tp3_qty = 20  # Close 20% at TP3
        
        self.leverage = 15
        self.fee_rate = 0.0012
    
    def alma(self, series, period=2, offset=0.85, sigma=5):
        """
        Arnaud Legoux Moving Average
        """
        m = offset * (period - 1)
        s = period / sigma
        
        weights = []
        for i in range(period):
            weights.append(np.exp(-((i - m) ** 2) / (2 * s ** 2)))
        
        weights = np.array(weights) / sum(weights)
        
        result = pd.Series(index=series.index, dtype=float)
        
        for i in range(period - 1, len(series)):
            window = series.iloc[i - period + 1:i + 1].values
            result.iloc[i] = np.sum(window * weights[::-1])
        
        return result
    
    def add_indicators(self, df):
        """Add ALMA indicators"""
        df = df.copy()
        
        # ALMA of close and open
        df['alma_close'] = self.alma(df['close'], self.ma_period, self.alma_offset, self.alma_sigma)
        df['alma_open'] = self.alma(df['open'], self.ma_period, self.alma_offset, self.alma_sigma)
        
        # Signals
        df['signal'] = 0
        
        # Long: ALMA close crosses over ALMA open
        df.loc[(df['alma_close'] > df['alma_open']) & 
               (df['alma_close'].shift(1) <= df['alma_open'].shift(1)), 'signal'] = 1
        
        # Short: ALMA close crosses under ALMA open
        df.loc[(df['alma_close'] < df['alma_open']) & 
               (df['alma_close'].shift(1) >= df['alma_open'].shift(1)), 'signal'] = -1
        
        return df
    
    def calculate_tp_sl(self, entry, direction):
        """Calculate TP and SL levels"""
        if direction == 'LONG':
            tp1 = entry * (1 + self.tp1_pct / 100)
            tp2 = entry * (1 + self.tp2_pct / 100)
            tp3 = entry * (1 + self.tp3_pct / 100)
            sl = entry * (1 - self.sl_pct / 100)
        else:  # SHORT
            tp1 = entry * (1 - self.tp1_pct / 100)
            tp2 = entry * (1 - self.tp2_pct / 100)
            tp3 = entry * (1 - self.tp3_pct / 100)
            sl = entry * (1 + self.sl_pct / 100)
        
        return tp1, tp2, tp3, sl
    
    def backtest(self, df, capital=10.0):
        """
        Backtest with multi-TP exits
        """
        df = self.add_indicators(df)
        
        trades = []
        equity = capital
        
        position = None
        
        for i in range(self.ma_period + 10, len(df)):
            row = df.iloc[i]
            
            # Check for exits if in position
            if position:
                current_price = row['close']
                high = row['high']
                low = row['low']
                
                # Track remaining position size
                remaining_size = position['size']
                
                # Check TP1
                if not position['tp1_hit']:
                    if (position['direction'] == 'LONG' and high >= position['tp1']) or \
                       (position['direction'] == 'SHORT' and low <= position['tp1']):
                        # Hit TP1
                        exit_size = position['original_size'] * (self.tp1_qty / 100)
                        pnl = self.calculate_pnl(position['entry'], position['tp1'], 
                                                 position['direction'], exit_size)
                        equity += pnl
                        remaining_size -= exit_size
                        position['tp1_hit'] = True
                        position['size'] = remaining_size
                
                # Check TP2
                if position['tp1_hit'] and not position['tp2_hit']:
                    if (position['direction'] == 'LONG' and high >= position['tp2']) or \
                       (position['direction'] == 'SHORT' and low <= position['tp2']):
                        # Hit TP2
                        exit_size = position['original_size'] * (self.tp2_qty / 100)
                        pnl = self.calculate_pnl(position['entry'], position['tp2'], 
                                                 position['direction'], exit_size)
                        equity += pnl
                        remaining_size -= exit_size
                        position['tp2_hit'] = True
                        position['size'] = remaining_size
                
                # Check TP3
                if position['tp2_hit'] and not position['tp3_hit']:
                    if (position['direction'] == 'LONG' and high >= position['tp3']) or \
                       (position['direction'] == 'SHORT' and low <= position['tp3']):
                        # Hit TP3
                        exit_size = remaining_size
                        pnl = self.calculate_pnl(position['entry'], position['tp3'], 
                                                 position['direction'], exit_size)
                        equity += pnl
                        
                        # Close trade
                        trades.append({
                            'entry_time': position['entry_time'],
                            'exit_time': row['timestamp'],
                            'direction': position['direction'],
                            'entry': position['entry'],
                            'exit': position['tp3'],
                            'exit_type': 'TP3',
                            'pnl': position['total_pnl'] + pnl
                        })
                        
                        position['total_pnl'] += pnl
                        position = None
                        continue
                
                # Check SL
                if (position['direction'] == 'LONG' and low <= position['sl']) or \
                   (position['direction'] == 'SHORT' and high >= position['sl']):
                    # Hit SL
                    pnl = self.calculate_pnl(position['entry'], position['sl'], 
                                             position['direction'], remaining_size)
                    equity += pnl
                    
                    # Close trade
                    exit_type = 'SL'
                    if position['tp1_hit']:
                        exit_type = 'SL_after_TP1'
                    if position['tp2_hit']:
                        exit_type = 'SL_after_TP2'
                    
                    trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': row['timestamp'],
                        'direction': position['direction'],
                        'entry': position['entry'],
                        'exit': position['sl'],
                        'exit_type': exit_type,
                        'pnl': position['total_pnl'] + pnl
                    })
                    
                    position = None
                    continue
            
            # Check for new signals
            if row['signal'] == 0:
                continue
            
            if position:
                continue  # Already in position
            
            # Open new position
            direction = 'LONG' if row['signal'] == 1 else 'SHORT'
            entry = row['close']
            
            tp1, tp2, tp3, sl = self.calculate_tp_sl(entry, direction)
            
            size = capital * 0.5  # Use 50% of capital per trade
            
            position = {
                'entry_time': row['timestamp'],
                'direction': direction,
                'entry': entry,
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'sl': sl,
                'size': size,
                'original_size': size,
                'tp1_hit': False,
                'tp2_hit': False,
                'tp3_hit': False,
                'total_pnl': 0
            }
        
        # Close any remaining position at last candle
        if position:
            exit_price = df.iloc[-1]['close']
            pnl = self.calculate_pnl(position['entry'], exit_price, 
                                     position['direction'], position['size'])
            equity += pnl
            
            trades.append({
                'entry_time': position['entry_time'],
                'exit_time': df.iloc[-1]['timestamp'],
                'direction': position['direction'],
                'entry': position['entry'],
                'exit': exit_price,
                'exit_type': 'EOD',
                'pnl': position['total_pnl'] + pnl
            })
        
        return trades, equity
    
    def calculate_pnl(self, entry, exit, direction, size):
        """Calculate P&L for a trade"""
        if direction == 'LONG':
            price_change = (exit - entry) / entry
        else:
            price_change = (entry - exit) / entry
        
        pnl_pct = price_change * self.leverage
        gross_pnl = size * pnl_pct
        fees = size * self.fee_rate * 2  # Entry + exit
        
        return gross_pnl - fees

# Quick test
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='15T')
    df = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    strategy = SMCMultiTPStrategy()
    trades, final_equity = strategy.backtest(df)
    
    print("SMC Multi-TP Strategy Test")
    print("="*70)
    print(f"Trades: {len(trades)}")
    print(f"Final Equity: ${final_equity:.2f}")
    print(f"ROI: {(final_equity - 10) / 10 * 100:.1f}%")
    
    if trades:
        winners = len([t for t in trades if t['pnl'] > 0])
        print(f"Win Rate: {winners / len(trades) * 100:.1f}%")

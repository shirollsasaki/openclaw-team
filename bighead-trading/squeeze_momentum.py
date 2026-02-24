#!/usr/bin/env python3
"""
Squeeze Momentum Indicator (LazyBear)
Ported from TradingView Pine Script
"""

import pandas as pd
import numpy as np

class SqueezeMomentumIndicator:
    """
    Squeeze Momentum Indicator by LazyBear
    
    Detects:
    - Squeeze On: Bollinger Bands inside Keltner Channels (consolidation)
    - Squeeze Off: Bollinger Bands outside Keltner Channels (breakout)
    - Momentum: Linear regression of price deviation
    """
    
    def __init__(self, bb_length=20, bb_mult=2.0, kc_length=20, kc_mult=1.5, use_true_range=True):
        self.bb_length = bb_length
        self.bb_mult = bb_mult
        self.kc_length = kc_length
        self.kc_mult = kc_mult
        self.use_true_range = use_true_range
    
    def calculate(self, df):
        """
        Calculate Squeeze Momentum on a dataframe
        
        Parameters:
        - df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        
        Returns:
        - df with additional columns:
          - sqz_on: True when squeeze is on (consolidation)
          - sqz_off: True when squeeze is off (breakout)
          - sqz_mom: Momentum value (positive = bullish, negative = bearish)
          - sqz_mom_color: 'lime', 'green', 'red', or 'maroon'
          - sqz_color: 'blue' (no squeeze), 'black' (squeeze on), 'gray' (squeeze off)
        """
        df = df.copy()
        
        # Calculate Bollinger Bands
        df['bb_basis'] = df['close'].rolling(self.bb_length).mean()
        df['bb_dev'] = self.bb_mult * df['close'].rolling(self.bb_length).std()
        df['bb_upper'] = df['bb_basis'] + df['bb_dev']
        df['bb_lower'] = df['bb_basis'] - df['bb_dev']
        
        # Calculate Keltner Channels
        df['kc_ma'] = df['close'].rolling(self.kc_length).mean()
        
        if self.use_true_range:
            # True Range
            df['tr'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['close'].shift(1)),
                    abs(df['low'] - df['close'].shift(1))
                )
            )
            df['kc_range'] = df['tr'].rolling(self.kc_length).mean()
        else:
            df['kc_range'] = (df['high'] - df['low']).rolling(self.kc_length).mean()
        
        df['kc_upper'] = df['kc_ma'] + df['kc_range'] * self.kc_mult
        df['kc_lower'] = df['kc_ma'] - df['kc_range'] * self.kc_mult
        
        # Determine Squeeze Status
        df['sqz_on'] = (df['bb_lower'] > df['kc_lower']) & (df['bb_upper'] < df['kc_upper'])
        df['sqz_off'] = (df['bb_lower'] < df['kc_lower']) & (df['bb_upper'] > df['kc_upper'])
        df['no_sqz'] = ~df['sqz_on'] & ~df['sqz_off']
        
        # Calculate Momentum (linear regression)
        # This is the LazyBear formula
        highest = df['high'].rolling(self.kc_length).max()
        lowest = df['low'].rolling(self.kc_length).min()
        avg_hl = (highest + lowest) / 2
        sma_close = df['close'].rolling(self.kc_length).mean()
        basis_for_mom = (avg_hl + sma_close) / 2
        
        # Linear regression of (close - basis)
        df['sqz_mom'] = self._linreg(df['close'] - basis_for_mom, self.kc_length)
        
        # Momentum color (histogram color in TV)
        df['sqz_mom_increasing'] = df['sqz_mom'] > df['sqz_mom'].shift(1)
        df['sqz_mom_color'] = 'gray'  # default
        
        df.loc[(df['sqz_mom'] > 0) & df['sqz_mom_increasing'], 'sqz_mom_color'] = 'lime'
        df.loc[(df['sqz_mom'] > 0) & ~df['sqz_mom_increasing'], 'sqz_mom_color'] = 'green'
        df.loc[(df['sqz_mom'] < 0) & ~df['sqz_mom_increasing'], 'sqz_mom_color'] = 'red'
        df.loc[(df['sqz_mom'] < 0) & df['sqz_mom_increasing'], 'sqz_mom_color'] = 'maroon'
        
        # Squeeze color
        df['sqz_color'] = 'blue'  # default (no squeeze)
        df.loc[df['sqz_on'], 'sqz_color'] = 'black'  # squeeze on
        df.loc[df['sqz_off'], 'sqz_color'] = 'gray'  # squeeze off
        
        return df
    
    def _linreg(self, series, length):
        """Linear regression calculation"""
        result = pd.Series(index=series.index, dtype=float)
        
        for i in range(length - 1, len(series)):
            y = series.iloc[i - length + 1:i + 1].values
            x = np.arange(length)
            
            # Simple linear regression
            if len(y) == length:
                slope = np.polyfit(x, y, 1)[0]
                result.iloc[i] = slope * (length - 1) + np.mean(y)
        
        return result
    
    def get_signals(self, df):
        """
        Generate trading signals from Squeeze Momentum
        
        Returns:
        - 1: Bullish signal (squeeze off + momentum turning positive)
        - -1: Bearish signal (squeeze off + momentum turning negative)
        - 0: No signal
        """
        df = self.calculate(df)
        
        df['sqz_signal'] = 0
        
        # Bullish: Squeeze just turned off + momentum is positive and increasing
        bullish_condition = (
            df['sqz_off'] &
            (df['sqz_mom'] > 0) &
            (df['sqz_mom_color'].isin(['lime', 'green']))
        )
        
        # Bearish: Squeeze just turned off + momentum is negative and decreasing
        bearish_condition = (
            df['sqz_off'] &
            (df['sqz_mom'] < 0) &
            (df['sqz_mom_color'].isin(['red', 'maroon']))
        )
        
        df.loc[bullish_condition, 'sqz_signal'] = 1
        df.loc[bearish_condition, 'sqz_signal'] = -1
        
        return df

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
    
    sqz = SqueezeMomentumIndicator()
    df_with_sqz = sqz.get_signals(df)
    
    print("Squeeze Momentum Indicator Test")
    print("="*70)
    print(df_with_sqz[['timestamp', 'close', 'sqz_on', 'sqz_off', 'sqz_mom', 'sqz_signal']].tail(10))
    print("\nSignals found:", df_with_sqz['sqz_signal'].abs().sum())

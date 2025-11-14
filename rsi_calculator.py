"""
RSI (Relative Strength Index) calculator
Calculates RSI and identifies overbought/oversold conditions
"""

import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from config.settings import RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD

class RSICalculator:
    """Calculates RSI with safe handling and alignment"""

    def calculate_rsi(self, df, column='close'):
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in dataframe")

        # Calculate RSI using ta library
        rsi = RSIIndicator(close=df[column], window=14).rsi()

        # Add RSI to dataframe and align
        df['rsi'] = rsi
        df = df.dropna(subset=['rsi'])
        df = df.reset_index(drop=True)
        return df

    
    def get_rsi_zone(self, rsi_value):
        """
        Determine RSI zone (oversold, neutral, overbought)
        
        Args:
            rsi_value: Current RSI value
        
        Returns:
            String: 'oversold', 'neutral', or 'overbought'
        """
        if rsi_value <= RSI_OVERSOLD:
            return 'oversold'
        elif rsi_value >= RSI_OVERBOUGHT:
            return 'overbought'
        else:
            return 'neutral'
    
    def is_oversold(self, rsi_value):
        """Check if RSI is in oversold zone"""
        return rsi_value <= RSI_OVERSOLD
    
    def is_overbought(self, rsi_value):
        """Check if RSI is in overbought zone"""
        return rsi_value >= RSI_OVERBOUGHT
    
    def get_rsi_extremes(self, df, lookback=50):
        """
        Find RSI highs and lows in recent period
        
        Args:
            df: DataFrame with RSI values
            lookback: Number of candles to look back
        
        Returns:
            Dictionary with highest and lowest RSI values
        """
        if df is None or 'rsi' not in df.columns:
            return None
        
        recent_df = df.tail(lookback)
        
        return {
            'highest_rsi': recent_df['rsi'].max(),
            'lowest_rsi': recent_df['rsi'].min(),
            'current_rsi': df['rsi'].iloc[-1],
            'avg_rsi': recent_df['rsi'].mean()
        }
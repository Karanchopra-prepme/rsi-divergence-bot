"""
REDESIGNED DIVERGENCE DETECTOR - Human-Like Visual Pattern Matching

Key Improvements:
1. Compares ACTUAL peaks/troughs like humans do
2. Validates divergence by checking visual alignment
3. Requires CLEAR, OBVIOUS divergence patterns
4. Multiple confirmation layers
5. Tests against price action after detection

This detector mimics how a human trader would spot divergences on a chart.
"""

import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
from datetime import datetime


class HumanLikeDivergenceDetector:
    """
    Detect divergences the way humans do - by visual pattern recognition
    
    CRITICAL DIFFERENCES FROM OLD DETECTOR:
    1. Finds PROMINENT peaks/troughs (not just any swing)
    2. Validates that price and RSI are VISUALLY aligned
    3. Requires CLEAR divergence (not subtle differences)
    4. Checks that divergence makes LOGICAL sense
    5. Multiple filters prevent false positives
    """
    
    def __init__(self,
                 min_peak_prominence=2.0,      # Minimum % move to count as peak
                 min_rsi_divergence=5.0,       # Minimum RSI difference
                 lookback_candles=50,          # How far back to look
                 require_confirmation=True,    # Wait for confirmation candle
                 min_time_between_peaks=5):    # Minimum candles between peaks
        
        self.min_peak_prominence = min_peak_prominence
        self.min_rsi_divergence = min_rsi_divergence
        self.lookback_candles = lookback_candles
        self.require_confirmation = require_confirmation
        self.min_time_between_peaks = min_time_between_peaks
    
    def find_prominent_peaks(self, df, column='high'):
        """
        Find PROMINENT peaks - ones a human would actually notice
        
        Not just any local maximum - must be significant enough to see on chart
        """
        if len(df) < 20:
            return []
        
        data = df[column].values
        
        # Find local maxima
        peaks = argrelextrema(data, np.greater, order=3)[0]
        
        prominent_peaks = []
        
        for peak_idx in peaks:
            if peak_idx < 5 or peak_idx >= len(data) - 5:
                continue  # Skip edges
            
            peak_value = data[peak_idx]
            
            # Check prominence: peak must be X% higher than surrounding area
            left_min = np.min(data[max(0, peak_idx-10):peak_idx])
            right_min = np.min(data[peak_idx+1:min(len(data), peak_idx+10)])
            
            left_prominence = ((peak_value - left_min) / left_min * 100) if left_min > 0 else 0
            right_prominence = ((peak_value - right_min) / right_min * 100) if right_min > 0 else 0
            
            # Must be prominent on both sides
            if left_prominence >= self.min_peak_prominence and right_prominence >= self.min_peak_prominence:
                prominent_peaks.append({
                    'index': peak_idx,
                    'value': peak_value,
                    'prominence': min(left_prominence, right_prominence)
                })
        
        return prominent_peaks
    
    def find_prominent_troughs(self, df, column='low'):
        """
        Find PROMINENT troughs - ones a human would actually notice
        """
        if len(df) < 20:
            return []
        
        data = df[column].values
        
        # Find local minima
        troughs = argrelextrema(data, np.less, order=3)[0]
        
        prominent_troughs = []
        
        for trough_idx in troughs:
            if trough_idx < 5 or trough_idx >= len(data) - 5:
                continue
            
            trough_value = data[trough_idx]
            
            # Check prominence: trough must be X% lower than surrounding area
            left_max = np.max(data[max(0, trough_idx-10):trough_idx])
            right_max = np.max(data[trough_idx+1:min(len(data), trough_idx+10)])
            
            left_prominence = ((left_max - trough_value) / trough_value * 100) if trough_value > 0 else 0
            right_prominence = ((right_max - trough_value) / trough_value * 100) if trough_value > 0 else 0
            
            if left_prominence >= self.min_peak_prominence and right_prominence >= self.min_peak_prominence:
                prominent_troughs.append({
                    'index': trough_idx,
                    'value': trough_value,
                    'prominence': min(left_prominence, right_prominence)
                })
        
        return prominent_troughs
    
    def get_rsi_at_peaks(self, df, price_peaks):
        """Get RSI values at price peaks"""
        rsi_at_peaks = []
        for peak in price_peaks:
            idx = peak['index']
            if idx < len(df):
                rsi_at_peaks.append({
                    'index': idx,
                    'price': peak['value'],
                    'rsi': df['rsi'].iloc[idx],
                    'prominence': peak['prominence']
                })
        return rsi_at_peaks
    
    def validate_divergence_alignment(self, peak1, peak2, divergence_type):
        """
        Validate that divergence makes visual sense
        
        A human checks:
        1. Are the peaks reasonably close in time?
        2. Is the divergence CLEAR and OBVIOUS?
        3. Does the pattern look right?
        """
        
        # Check time distance
        time_distance = abs(peak2['index'] - peak1['index'])
        if time_distance < self.min_time_between_peaks:
            return False, "Peaks too close together"
        
        if time_distance > self.lookback_candles:
            return False, "Peaks too far apart"
        
        # Check price difference
        price_change_pct = abs((peak2['price'] - peak1['price']) / peak1['price'] * 100)
        if price_change_pct < 0.5:
            return False, "Price difference too small"
        
        # Check RSI difference
        rsi_diff = abs(peak2['rsi'] - peak1['rsi'])
        if rsi_diff < self.min_rsi_divergence:
            return False, f"RSI divergence too small: {rsi_diff:.1f}"
        
        # Validate divergence direction
        if divergence_type == 'BEARISH':
            # Price should make higher high, RSI lower high
            price_higher = peak2['price'] > peak1['price']
            rsi_lower = peak2['rsi'] < peak1['rsi']
            
            if not (price_higher and rsi_lower):
                return False, "Pattern doesn't match bearish divergence"
            
            # RSI should be clearly lower (not just by 1-2 points)
            if rsi_diff < self.min_rsi_divergence:
                return False, f"RSI drop not significant enough: {rsi_diff:.1f}"
        
        elif divergence_type == 'BULLISH':
            # Price should make lower low, RSI higher low
            price_lower = peak2['price'] < peak1['price']
            rsi_higher = peak2['rsi'] > peak1['rsi']
            
            if not (price_lower and rsi_higher):
                return False, "Pattern doesn't match bullish divergence"
            
            if rsi_diff < self.min_rsi_divergence:
                return False, f"RSI rise not significant enough: {rsi_diff:.1f}"
        
        return True, "Valid"
    
    def check_price_action_confirms(self, df, divergence, current_idx):
        """
        Check if price action AFTER divergence confirms the signal
        
        A real divergence should lead to reversal soon after
        """
        if self.require_confirmation:
            # Look at next 3 candles
            if current_idx + 3 >= len(df):
                return False, "Not enough candles after signal"
            
            current_price = df['close'].iloc[current_idx]
            next_prices = df['close'].iloc[current_idx+1:current_idx+4]
            
            if divergence == 'BEARISH':
                # After bearish divergence, price should start falling
                falling_candles = sum(1 for p in next_prices if p < current_price)
                if falling_candles < 2:
                    return False, "Price not falling after bearish divergence"
            
            elif divergence == 'BULLISH':
                # After bullish divergence, price should start rising
                rising_candles = sum(1 for p in next_prices if p > current_price)
                if rising_candles < 2:
                    return False, "Price not rising after bullish divergence"
        
        return True, "Confirmed"
    
    def detect_bearish_divergence(self, df):
        """
        Detect BEARISH divergence like a human would
        
        Visual pattern:
        - Price makes higher high (clearly visible)
        - RSI makes lower high (clearly visible)
        - The two peaks should be "obvious" on a chart
        """
        if df is None or 'rsi' not in df.columns or len(df) < 30:
            return None
        
        # Find prominent price peaks
        price_peaks = self.find_prominent_peaks(df, 'high')
        
        if len(price_peaks) < 2:
            return None
        
        # Get RSI at those peaks
        peaks_with_rsi = self.get_rsi_at_peaks(df, price_peaks)
        
        if len(peaks_with_rsi) < 2:
            return None
        
        # Look at last 2 prominent peaks
        peak1 = peaks_with_rsi[-2]
        peak2 = peaks_with_rsi[-1]
        
        # Validate this is actual bearish divergence
        is_valid, reason = self.validate_divergence_alignment(peak1, peak2, 'BEARISH')
        
        if not is_valid:
            return None
        
        # Check price action confirmation
        is_confirmed, conf_reason = self.check_price_action_confirms(df, 'BEARISH', peak2['index'])
        
        if not is_confirmed and self.require_confirmation:
            return None
        
        # Calculate quality score
        price_change_pct = ((peak2['price'] - peak1['price']) / peak1['price'] * 100)
        rsi_change = peak1['rsi'] - peak2['rsi']
        
        # Quality must be high - obvious divergence
        quality = self._calculate_quality_score(
            price_change_pct=price_change_pct,
            rsi_change=rsi_change,
            prominence=min(peak1['prominence'], peak2['prominence']),
            confirmed=is_confirmed
        )
        
        # Only return if quality is high
        if quality < 60:
            return None
        
        return {
            'type': 'BEARISH',
            'peak1_idx': peak1['index'],
            'peak2_idx': peak2['index'],
            'price1': float(peak1['price']),
            'price2': float(peak2['price']),
            'rsi1': float(peak1['rsi']),
            'rsi2': float(peak2['rsi']),
            'price_change_pct': round(price_change_pct, 2),
            'rsi_change': round(rsi_change, 2),
            'current_price': float(df['close'].iloc[-1]),
            'current_rsi': round(df['rsi'].iloc[-1], 2),
            'timestamp': df['timestamp'].iloc[-1],
            'quality': quality,
            'quality_label': self._get_quality_label(quality),
            'confirmed': is_confirmed,
            'validation': reason,
            'explanation': f"Price peaked at ${peak2['price']:.4f} (higher than ${peak1['price']:.4f}), but RSI dropped from {peak1['rsi']:.1f} to {peak2['rsi']:.1f}"
        }
    
    def detect_bullish_divergence(self, df):
        """
        Detect BULLISH divergence like a human would
        
        Visual pattern:
        - Price makes lower low (clearly visible)
        - RSI makes higher low (clearly visible)
        """
        if df is None or 'rsi' not in df.columns or len(df) < 30:
            return None
        
        # Find prominent price troughs
        price_troughs = self.find_prominent_troughs(df, 'low')
        
        if len(price_troughs) < 2:
            return None
        
        # Get RSI at those troughs
        troughs_with_rsi = []
        for trough in price_troughs:
            idx = trough['index']
            if idx < len(df):
                troughs_with_rsi.append({
                    'index': idx,
                    'price': trough['value'],
                    'rsi': df['rsi'].iloc[idx],
                    'prominence': trough['prominence']
                })
        
        if len(troughs_with_rsi) < 2:
            return None
        
        # Look at last 2 prominent troughs
        trough1 = troughs_with_rsi[-2]
        trough2 = troughs_with_rsi[-1]
        
        # Validate alignment
        # For bullish: price lower, RSI higher
        price_change_pct = ((trough1['price'] - trough2['price']) / trough1['price'] * 100)
        rsi_change = trough2['rsi'] - trough1['rsi']
        
        # Check it's actual bullish divergence
        if not (trough2['price'] < trough1['price'] and trough2['rsi'] > trough1['rsi']):
            return None
        
        if abs(rsi_change) < self.min_rsi_divergence:
            return None
        
        # Validate
        is_valid, reason = self.validate_divergence_alignment(trough1, trough2, 'BULLISH')
        if not is_valid:
            return None
        
        # Check confirmation
        is_confirmed, conf_reason = self.check_price_action_confirms(df, 'BULLISH', trough2['index'])
        if not is_confirmed and self.require_confirmation:
            return None
        
        # Calculate quality
        quality = self._calculate_quality_score(
            price_change_pct=abs(price_change_pct),
            rsi_change=abs(rsi_change),
            prominence=min(trough1['prominence'], trough2['prominence']),
            confirmed=is_confirmed
        )
        
        if quality < 60:
            return None
        
        return {
            'type': 'BULLISH',
            'trough1_idx': trough1['index'],
            'trough2_idx': trough2['index'],
            'price1': float(trough1['price']),
            'price2': float(trough2['price']),
            'rsi1': float(trough1['rsi']),
            'rsi2': float(trough2['rsi']),
            'price_change_pct': round(abs(price_change_pct), 2),
            'rsi_change': round(rsi_change, 2),
            'current_price': float(df['close'].iloc[-1]),
            'current_rsi': round(df['rsi'].iloc[-1], 2),
            'timestamp': df['timestamp'].iloc[-1],
            'quality': quality,
            'quality_label': self._get_quality_label(quality),
            'confirmed': is_confirmed,
            'validation': reason,
            'explanation': f"Price dropped to ${trough2['price']:.4f} (lower than ${trough1['price']:.4f}), but RSI rose from {trough1['rsi']:.1f} to {trough2['rsi']:.1f}"
        }
    
    def detect_all_divergences(self, df):
        """Detect both types"""
        divergences = []
        
        bullish = self.detect_bullish_divergence(df)
        if bullish:
            divergences.append(bullish)
        
        bearish = self.detect_bearish_divergence(df)
        if bearish:
            divergences.append(bearish)
        
        return divergences
    
    def _calculate_quality_score(self, price_change_pct, rsi_change, prominence, confirmed):
        """
        Calculate quality score (0-100)
        
        High quality = obvious divergence that's likely to work
        """
        # Price movement score (30 points max)
        price_score = min(abs(price_change_pct) * 6, 30)
        
        # RSI divergence score (30 points max)
        rsi_score = min(abs(rsi_change) * 3, 30)
        
        # Prominence score (20 points max)
        prominence_score = min(prominence * 4, 20)
        
        # Confirmation bonus (20 points)
        confirmation_score = 20 if confirmed else 0
        
        total = price_score + rsi_score + prominence_score + confirmation_score
        
        return min(round(total, 1), 100)
    
    def _get_quality_label(self, quality):
        """Convert quality to label"""
        if quality >= 85:
            return "Excellent ⭐⭐⭐⭐⭐"
        elif quality >= 75:
            return "Very Good ⭐⭐⭐⭐"
        elif quality >= 65:
            return "Good ⭐⭐⭐"
        else:
            return "Fair ⭐⭐"
    
    def format_divergence_alert(self, divergence, symbol, timeframe):
        """Format alert with visual description"""
        emoji = "🟢" if divergence['type'] == 'BULLISH' else "🔴"
        
        message = f"""
{emoji} {divergence['type']} DIVERGENCE (HUMAN-VALIDATED)

📊 Coin: {symbol}
⏰ Timeframe: {timeframe}
💰 Current Price: ${divergence['current_price']:,.4f}
📈 Current RSI: {divergence['current_rsi']}

🔍 VISUAL PATTERN:
  Peak 1: ${divergence.get('price1', divergence.get('price1')):,.4f} | RSI {divergence.get('rsi1', divergence.get('rsi1')):.1f}
  Peak 2: ${divergence.get('price2', divergence.get('price2')):,.4f} | RSI {divergence.get('rsi2', divergence.get('rsi2')):.1f}
  
  Price: {divergence['price_change_pct']:+.2f}%
  RSI: {divergence['rsi_change']:+.1f}

💎 Quality: {divergence['quality_label']} ({divergence['quality']}/100)
✅ Confirmed: {'Yes' if divergence['confirmed'] else 'No'}

📝 {divergence['explanation']}

🕐 {divergence['timestamp'].strftime('%Y-%m-%d %H:%M')}

⚠️ HUMAN-VALIDATED PATTERN - Visual divergence detected
"""
        return message.strip()


# Test
if __name__ == "__main__":
    from analyzer.data_fetcher import DataFetcher
    from analyzer.rsi_calculator import RSICalculator
    
    print("=" * 70)
    print("TESTING HUMAN-LIKE DIVERGENCE DETECTOR")
    print("=" * 70)
    
    fetcher = DataFetcher()
    rsi_calc = RSICalculator()
    
    # Use STRICT parameters
    detector = HumanLikeDivergenceDetector(
        min_peak_prominence=2.0,      # Must be 2% prominent
        min_rsi_divergence=5.0,       # Must have 5+ RSI difference
        lookback_candles=50,
        require_confirmation=True,     # Wait for price confirmation
        min_time_between_peaks=5
    )
    
    test_coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    
    for symbol in test_coins:
        print(f"\n{'='*70}")
        print(f"Analyzing {symbol}")
        print('='*70)
        
        df = fetcher.fetch_ohlcv(symbol, '15m', limit=200)
        if df is not None:
            df = rsi_calc.calculate_rsi(df)
            
            divs = detector.detect_all_divergences(df)
            
            if divs:
                for div in divs:
                    print(detector.format_divergence_alert(div, symbol, '15m'))
            else:
                print("No CLEAR, OBVIOUS divergences detected")
                print("(This is GOOD - means no false signals!)")
    
    print("\n✓ Human-like detection complete!")
"""
RSI Support/Resistance Trend Reversal Detector - ENHANCED VERSION
Strict filters to ensure only high-quality signals
"""

import pandas as pd
import numpy as np
from scipy.signal import argrelextrema


class RSISupportResistanceDetector:
    """
    Detect high-quality trend reversals with strict filters
    
    MAJOR IMPROVEMENTS:
    - Stricter RSI zones (tighter ranges)
    - Volume confirmation required
    - Price momentum validation
    - Multiple consecutive touches required
    - Stronger bounce/rejection requirements
    - Better strength calculation
    """
    
    def __init__(self,
                 rsi_support_zone=(28, 38),       # Tighter support zone
                 rsi_resistance_zone=(62, 72),    # Tighter resistance zone
                 min_touches=3,                   # Need 3+ touches (was 2)
                 price_trend_candles=7,           # More candles to confirm
                 min_price_trend=2.0,             # Stronger trend required (was 1.5)
                 rsi_bounce_threshold=8,          # Stronger bounce (was 5)
                 volume_multiplier=1.1,           # Volume confirmation
                 max_rsi_variance=5):             # RSI must be consistent
        
        self.rsi_support_zone = rsi_support_zone
        self.rsi_resistance_zone = rsi_resistance_zone
        self.min_touches = min_touches
        self.price_trend_candles = price_trend_candles
        self.min_price_trend = min_price_trend
        self.rsi_bounce_threshold = rsi_bounce_threshold
        self.volume_multiplier = volume_multiplier
        self.max_rsi_variance = max_rsi_variance
    
    def detect_rsi_support_reversal(self, df):
        """
        Detect BULLISH reversal with STRICT filters
        
        Requirements:
        1. Price in clear downtrend (2%+ drop)
        2. RSI touched support 3+ times
        3. RSI bounce strength 8+ points
        4. Volume increasing on bounce
        5. RSI touches within tight range (low variance)
        """
        if df is None or 'rsi' not in df.columns or len(df) < 40:
            return None
        
        current_rsi = df['rsi'].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        # FILTER 1: Check if RSI recently touched support zone
        recent_rsi = df['rsi'].iloc[-15:]
        min_recent_rsi = min(recent_rsi)
        
        # Must have touched support zone
        if not (self.rsi_support_zone[0] <= min_recent_rsi <= self.rsi_support_zone[1]):
            return None
        
        # FILTER 2: Current RSI must be bouncing (not still at bottom)
        if current_rsi <= self.rsi_support_zone[0]:
            return None
        
        # FILTER 3: Must be well above support now (confirming bounce)
        if current_rsi < min_recent_rsi + self.rsi_bounce_threshold:
            return None
        
        # FILTER 4: Find all support touches
        support_touches = self._find_rsi_support_touches(df)
        if len(support_touches) < self.min_touches:
            return None
        
        # FILTER 5: Support touches must be consistent (low variance)
        touch_rsi_values = [t['rsi'] for t in support_touches[-5:]]  # Last 5 touches
        rsi_variance = np.std(touch_rsi_values)
        if rsi_variance > self.max_rsi_variance:
            return None  # Touches too scattered, not a strong support
        
        # FILTER 6: Price must be in CLEAR downtrend
        price_trend = self._check_price_trend(df, direction='down')
        if not price_trend:
            return None
        
        # Additional: Downtrend must be strong enough
        if abs(price_trend['percent_change']) < self.min_price_trend:
            return None
        
        # FILTER 7: Volume confirmation
        volume_confirmed = self._check_volume_surge(df)
        if not volume_confirmed:
            return None  # No volume surge on bounce = weak signal
        
        # FILTER 8: Price momentum check (price must be stabilizing/turning)
        price_momentum = self._check_price_momentum(df)
        if price_momentum == 'strongly_down':
            return None  # Still falling hard, too early
        
        # Calculate bounce strength
        bounce_strength = current_rsi - min_recent_rsi
        
        # Calculate high-quality strength score
        strength = self._calculate_support_strength(
            support_touches, 
            price_trend['percent_change'],
            bounce_strength,
            rsi_variance,
            volume_confirmed
        )
        
        # FILTER 9: Minimum strength threshold
        if strength < 50:  # Only strong signals
            return None
        
        return {
            'type': 'RSI_SUPPORT_REVERSAL',
            'direction': 'BULLISH',
            'current_price': float(current_price),
            'current_rsi': round(current_rsi, 2),
            'rsi_support_level': round(min_recent_rsi, 2),
            'support_touches': len(support_touches),
            'price_trend': f"{price_trend['percent_change']:.2f}% down",
            'rsi_bounce': round(bounce_strength, 2),
            'rsi_variance': round(rsi_variance, 2),
            'strength': strength,
            'strength_label': self._get_strength_label(strength),
            'timestamp': df['timestamp'].iloc[-1],
            'explanation': f"RSI bounced {bounce_strength:.1f} pts from {min_recent_rsi:.1f} support ({len(support_touches)} touches) while price fell {abs(price_trend['percent_change']):.1f}%",
            'volume_confirmed': True,
            'filters_passed': ['support_touches', 'rsi_variance', 'price_trend', 'bounce_strength', 'volume', 'momentum']
        }
    
    def detect_rsi_resistance_reversal(self, df):
        """
        Detect BEARISH reversal with STRICT filters
        
        Requirements:
        1. Price in clear uptrend (2%+ rise)
        2. RSI touched resistance 3+ times
        3. RSI rejection strength 8+ points
        4. Volume increasing on rejection
        5. RSI touches within tight range (low variance)
        """
        if df is None or 'rsi' not in df.columns or len(df) < 40:
            return None
        
        current_rsi = df['rsi'].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        # FILTER 1: Check if RSI recently touched resistance zone
        recent_rsi = df['rsi'].iloc[-15:]
        max_recent_rsi = max(recent_rsi)
        
        # Must have touched resistance zone
        if not (self.rsi_resistance_zone[0] <= max_recent_rsi <= self.rsi_resistance_zone[1]):
            return None
        
        # FILTER 2: Current RSI must be rejecting (not still at top)
        if current_rsi >= self.rsi_resistance_zone[1]:
            return None
        
        # FILTER 3: Must be well below resistance now (confirming rejection)
        if current_rsi > max_recent_rsi - self.rsi_bounce_threshold:
            return None
        
        # FILTER 4: Find all resistance touches
        resistance_touches = self._find_rsi_resistance_touches(df)
        if len(resistance_touches) < self.min_touches:
            return None
        
        # FILTER 5: Resistance touches must be consistent
        touch_rsi_values = [t['rsi'] for t in resistance_touches[-5:]]
        rsi_variance = np.std(touch_rsi_values)
        if rsi_variance > self.max_rsi_variance:
            return None
        
        # FILTER 6: Price must be in CLEAR uptrend
        price_trend = self._check_price_trend(df, direction='up')
        if not price_trend:
            return None
        
        if abs(price_trend['percent_change']) < self.min_price_trend:
            return None
        
        # FILTER 7: Volume confirmation
        volume_confirmed = self._check_volume_surge(df)
        if not volume_confirmed:
            return None
        
        # FILTER 8: Price momentum check
        price_momentum = self._check_price_momentum(df)
        if price_momentum == 'strongly_up':
            return None  # Still rising hard, too early
        
        # Calculate rejection strength
        rejection_strength = max_recent_rsi - current_rsi
        
        # Calculate strength
        strength = self._calculate_resistance_strength(
            resistance_touches,
            price_trend['percent_change'],
            rejection_strength,
            rsi_variance,
            volume_confirmed
        )
        
        # FILTER 9: Minimum strength threshold
        if strength < 50:
            return None
        
        return {
            'type': 'RSI_RESISTANCE_REVERSAL',
            'direction': 'BEARISH',
            'current_price': float(current_price),
            'current_rsi': round(current_rsi, 2),
            'rsi_resistance_level': round(max_recent_rsi, 2),
            'resistance_touches': len(resistance_touches),
            'price_trend': f"{price_trend['percent_change']:.2f}% up",
            'rsi_rejection': round(rejection_strength, 2),
            'rsi_variance': round(rsi_variance, 2),
            'strength': strength,
            'strength_label': self._get_strength_label(strength),
            'timestamp': df['timestamp'].iloc[-1],
            'explanation': f"RSI rejected {rejection_strength:.1f} pts from {max_recent_rsi:.1f} resistance ({len(resistance_touches)} touches) while price rose {price_trend['percent_change']:.1f}%",
            'volume_confirmed': True,
            'filters_passed': ['resistance_touches', 'rsi_variance', 'price_trend', 'rejection_strength', 'volume', 'momentum']
        }
    
    def detect_all_reversals(self, df):
        """Detect both support and resistance reversals"""
        reversals = []
        
        support_reversal = self.detect_rsi_support_reversal(df)
        if support_reversal:
            reversals.append(support_reversal)
        
        resistance_reversal = self.detect_rsi_resistance_reversal(df)
        if resistance_reversal:
            reversals.append(resistance_reversal)
        
        return reversals
    
    def _find_rsi_support_touches(self, df, lookback=60):
        """Find where RSI touched support zone"""
        recent_df = df.tail(lookback)
        touches = []
        
        for i, row in recent_df.iterrows():
            rsi = row['rsi']
            if self.rsi_support_zone[0] <= rsi <= self.rsi_support_zone[1]:
                # Only count if not consecutive (avoid counting same touch multiple times)
                if not touches or i - touches[-1]['index'] > 3:
                    touches.append({'index': i, 'rsi': rsi})
        
        return touches
    
    def _find_rsi_resistance_touches(self, df, lookback=60):
        """Find where RSI touched resistance zone"""
        recent_df = df.tail(lookback)
        touches = []
        
        for i, row in recent_df.iterrows():
            rsi = row['rsi']
            if self.rsi_resistance_zone[0] <= rsi <= self.rsi_resistance_zone[1]:
                if not touches or i - touches[-1]['index'] > 3:
                    touches.append({'index': i, 'rsi': rsi})
        
        return touches
    
    def _check_price_trend(self, df, direction='down'):
        """Check if price has a STRONG clear trend"""
        if len(df) < self.price_trend_candles:
            return None
        
        recent_prices = df['close'].tail(self.price_trend_candles)
        start_price = recent_prices.iloc[0]
        end_price = recent_prices.iloc[-1]
        
        percent_change = ((end_price - start_price) / start_price) * 100
        
        # Check trend consistency (not just endpoints)
        if direction == 'down':
            # Count lower lows
            lower_count = sum(1 for i in range(1, len(recent_prices)) 
                            if recent_prices.iloc[i] < recent_prices.iloc[i-1])
            consistency = lower_count / (len(recent_prices) - 1)
            
            if percent_change < -self.min_price_trend and consistency > 0.5:
                return {
                    'direction': 'down',
                    'percent_change': percent_change,
                    'consistency': consistency,
                    'start_price': start_price,
                    'end_price': end_price
                }
        elif direction == 'up':
            # Count higher highs
            higher_count = sum(1 for i in range(1, len(recent_prices)) 
                             if recent_prices.iloc[i] > recent_prices.iloc[i-1])
            consistency = higher_count / (len(recent_prices) - 1)
            
            if percent_change > self.min_price_trend and consistency > 0.5:
                return {
                    'direction': 'up',
                    'percent_change': percent_change,
                    'consistency': consistency,
                    'start_price': start_price,
                    'end_price': end_price
                }
        
        return None
    
    def _check_volume_surge(self, df):
        """Check if there's a volume surge on recent candles"""
        if 'volume' not in df.columns or len(df) < 20:
            return False  # No volume data = reject signal
        
        # Compare recent volume to average
        recent_volume = df['volume'].iloc[-3:].mean()
        avg_volume = df['volume'].iloc[-20:-3].mean()
        
        return recent_volume > (avg_volume * self.volume_multiplier)
    
    def _check_price_momentum(self, df):
        """Check recent price momentum (last 3 candles)"""
        if len(df) < 5:
            return 'unknown'
        
        recent_prices = df['close'].tail(3)
        price_change = ((recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]) * 100
        
        if price_change < -1.5:
            return 'strongly_down'
        elif price_change > 1.5:
            return 'strongly_up'
        else:
            return 'stabilizing'
    
    def _calculate_support_strength(self, touches, price_change, bounce, rsi_variance, volume_conf):
        """
        Calculate REALISTIC strength score
        
        Components:
        - Touch quality (30 pts): More touches + low variance = stronger
        - Price trend (25 pts): Stronger downtrend = better setup
        - Bounce strength (25 pts): Bigger bounce = stronger signal
        - Volume (20 pts): Volume surge = confirmation
        """
        # Touch quality score
        touch_count = min(len(touches), 5)
        variance_penalty = min(rsi_variance * 2, 10)
        touch_score = (touch_count * 6) - variance_penalty  # Max 30
        touch_score = max(0, min(touch_score, 30))
        
        # Price trend score
        price_score = min(abs(price_change) * 5, 25)
        
        # Bounce strength score
        bounce_score = min((bounce - 8) * 3, 25)  # Penalty if below 8
        bounce_score = max(0, bounce_score)
        
        # Volume score
        volume_score = 20 if volume_conf else 0
        
        total = touch_score + price_score + bounce_score + volume_score
        return min(round(total, 1), 100)
    
    def _calculate_resistance_strength(self, touches, price_change, rejection, rsi_variance, volume_conf):
        """Calculate REALISTIC strength for resistance"""
        touch_count = min(len(touches), 5)
        variance_penalty = min(rsi_variance * 2, 10)
        touch_score = (touch_count * 6) - variance_penalty
        touch_score = max(0, min(touch_score, 30))
        
        price_score = min(abs(price_change) * 5, 25)
        rejection_score = min((rejection - 8) * 3, 25)
        rejection_score = max(0, rejection_score)
        volume_score = 20 if volume_conf else 0
        
        total = touch_score + price_score + rejection_score + volume_score
        return min(round(total, 1), 100)
    
    def _get_strength_label(self, strength):
        """Convert strength to label"""
        if strength >= 85:
            return "Extremely Strong ⭐⭐⭐⭐⭐"
        elif strength >= 70:
            return "Very Strong ⭐⭐⭐⭐"
        elif strength >= 55:
            return "Strong ⭐⭐⭐"
        else:
            return "Moderate ⭐⭐"
    
    def format_reversal_alert(self, reversal, symbol, timeframe):
        """Format alert message"""
        emoji = "🟢" if reversal['direction'] == 'BULLISH' else "🔴"
        type_name = "RSI SUPPORT" if reversal['direction'] == 'BULLISH' else "RSI RESISTANCE"
        
        message = f"""
{emoji} {type_name} REVERSAL

📊 Coin: {symbol}
⏰ Timeframe: {timeframe}
💰 Price: ${reversal['current_price']:,.2f}
📈 RSI: {reversal['current_rsi']}

🎯 PATTERN:
  Level: {reversal.get('rsi_support_level') or reversal.get('rsi_resistance_level')}
  Touches: {reversal.get('support_touches') or reversal.get('resistance_touches')}x (variance: {reversal['rsi_variance']})
  Price Trend: {reversal['price_trend']}
  RSI Move: {reversal.get('rsi_bounce') or reversal.get('rsi_rejection')} pts

💪 Strength: {reversal['strength_label']} ({reversal['strength']}/100)
✅ Filters: {', '.join(reversal['filters_passed'])}

📝 {reversal['explanation']}

⚡ Expected: {reversal['direction']} reversal

🕐 {reversal['timestamp'].strftime('%Y-%m-%d %H:%M')}
"""
        return message.strip()


# Test with strict filters
if __name__ == "__main__":
    from analyzer.data_fetcher import DataFetcher
    from analyzer.rsi_calculator import RSICalculator
    
    print("=" * 70)
    print("TESTING ENHANCED RSI S/R DETECTOR (STRICT FILTERS)")
    print("=" * 70)
    
    fetcher = DataFetcher()
    rsi_calc = RSICalculator()
    
    # Initialize with STRICT parameters
    detector = RSISupportResistanceDetector(
        rsi_support_zone=(28, 38),
        rsi_resistance_zone=(62, 72),
        min_touches=3,
        price_trend_candles=7,
        min_price_trend=2.0,
        rsi_bounce_threshold=8,
        volume_multiplier=1.1,
        max_rsi_variance=5
    )
    
    test_coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
    
    for symbol in test_coins:
        print(f"\n{'='*70}")
        print(f"Analyzing {symbol}")
        print('='*70)
        
        df = fetcher.fetch_ohlcv(symbol, '15m', limit=200)
        if df is not None:
            df = rsi_calc.calculate_rsi(df)
            
            reversals = detector.detect_all_reversals(df)
            
            if reversals:
                for rev in reversals:
                    print(detector.format_reversal_alert(rev, symbol, '15m'))
                    print()
            else:
                print("No high-quality RSI S/R reversals (strict filters)")
        else:
            print("⚠️ No data")
    
    print("\n✓ Enhanced detection complete - only quality signals!")
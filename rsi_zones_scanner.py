"""
RSI Overbought/Oversold Zone Scanner - ENHANCED
Now supports: 15m, 30m, 1h, 4h timeframes
Fixed: XMR/USDT data issue handling
"""

from datetime import datetime
import asyncio
from analyzer.data_fetcher import DataFetcher
from analyzer.rsi_calculator import RSICalculator
from config.coin_list import DEFAULT_WATCHLIST


class RSIZoneScanner:
    """
    Scan and categorize coins by RSI levels across multiple timeframes
    
    Features:
    - Multi-timeframe scanning (15m, 30m, 1h, 4h)
    - 7 RSI zones with color coding
    - Sorted by RSI extremes
    - Trend indication (rising/falling)
    - Error handling for problematic coins (XMR/USDT fix)
    """
    
    def __init__(self,
                 extreme_oversold=25,    # Extremely oversold
                 oversold=30,            # Oversold threshold
                 neutral_low=40,         # Neutral zone lower bound
                 neutral_high=60,        # Neutral zone upper bound
                 overbought=70,          # Overbought threshold
                 extreme_overbought=75): # Extremely overbought
        
        self.extreme_oversold = extreme_oversold
        self.oversold = oversold
        self.neutral_low = neutral_low
        self.neutral_high = neutral_high
        self.overbought = overbought
        self.extreme_overbought = extreme_overbought
        
        self.fetcher = DataFetcher()
        self.rsi_calc = RSICalculator()
        
        # Track problematic coins for debugging
        self.problematic_coins = []
    
    def get_rsi_zone(self, rsi):
        """Determine which RSI zone a value belongs to"""
        if rsi <= self.extreme_oversold:
            return 'EXTREME_OVERSOLD'
        elif rsi <= self.oversold:
            return 'OVERSOLD'
        elif rsi <= self.neutral_low:
            return 'OVERSOLD_ZONE'
        elif rsi <= self.neutral_high:
            return 'NEUTRAL'
        elif rsi <= self.overbought:
            return 'OVERBOUGHT_ZONE'
        elif rsi <= self.extreme_overbought:
            return 'OVERBOUGHT'
        else:
            return 'EXTREME_OVERBOUGHT'
    
    def get_rsi_trend(self, df):
        """Determine if RSI is rising or falling"""
        if len(df) < 5:
            return 'unknown'
        
        recent_rsi = df['rsi'].tail(5)
        
        # Compare last 3 vs previous 2
        recent_avg = recent_rsi.tail(3).mean()
        previous_avg = recent_rsi.head(2).mean()
        
        if recent_avg > previous_avg + 2:
            return 'rising'
        elif recent_avg < previous_avg - 2:
            return 'falling'
        else:
            return 'stable'
    
    def _validate_rsi_data(self, df, symbol):
        """
        Validate RSI data to catch false/corrupted data
        
        Fixes XMR/USDT and similar issues where:
        - RSI shows extreme values incorrectly
        - Data has gaps or corrupted candles
        - RSI calculation fails
        """
        if df is None or len(df) < 20:
            return False, "Insufficient data"
        
        # Check if RSI column exists
        if 'rsi' not in df.columns:
            return False, "RSI not calculated"
        
        # Get current RSI
        current_rsi = df['rsi'].iloc[-1]
        
        # Check for NaN or invalid RSI
        if pd.isna(current_rsi) or current_rsi < 0 or current_rsi > 100:
            return False, f"Invalid RSI value: {current_rsi}"
        
        # Check recent RSI history for consistency
        recent_rsi = df['rsi'].tail(10)
        
        # Count NaN values
        nan_count = recent_rsi.isna().sum()
        if nan_count > 3:  # More than 3 NaN in last 10 candles
            return False, f"Too many NaN RSI values: {nan_count}/10"
        
        # Check for extreme volatility (potential data corruption)
        # RSI shouldn't swing more than 50 points in 1 candle normally
        rsi_diffs = recent_rsi.diff().abs()
        max_diff = rsi_diffs.max()
        if max_diff > 50:
            return False, f"Extreme RSI volatility detected: {max_diff:.1f}"
        
        # Check price data quality
        recent_prices = df['close'].tail(10)
        if recent_prices.isna().any():
            return False, "NaN in price data"
        
        # Check for zero or negative prices
        if (recent_prices <= 0).any():
            return False, "Invalid price data (<=0)"
        
        # All checks passed
        return True, "OK"
    
    async def scan_single_coin(self, symbol, timeframe):
        """
        Scan a single coin for RSI level with validation
        
        Returns:
            Dict with coin info or None if error/invalid data
        """
        try:
            # Fetch data with appropriate limit for timeframe
            limit_map = {
                '15m': 100,
                '30m': 100,
                '1h': 150,
                '4h': 200
            }
            limit = limit_map.get(timeframe, 100)
            
            df = self.fetcher.fetch_ohlcv(symbol, timeframe, limit=limit)
            if df is None or len(df) < 20:
                return None
            
            # Calculate RSI
            df = self.rsi_calc.calculate_rsi(df)
            
            # ✅ VALIDATE DATA (XMR/USDT fix)
            is_valid, validation_msg = self._validate_rsi_data(df, symbol)
            if not is_valid:
                if symbol not in self.problematic_coins:
                    self.problematic_coins.append(symbol)
                    print(f"⚠️ Skipping {symbol} ({timeframe}): {validation_msg}")
                return None
            
            # Get current values
            current_rsi = df['rsi'].iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # Get zone
            zone = self.get_rsi_zone(current_rsi)
            
            # Get trend
            trend = self.get_rsi_trend(df)
            
            # Calculate price change (last 24 hours approximation)
            timeframe_to_candles = {
                '15m': 96,   # 96 * 15min = 24h
                '30m': 48,   # 48 * 30min = 24h
                '1h': 24,    # 24 * 1h = 24h
                '4h': 6      # 6 * 4h = 24h
            }
            
            lookback = min(timeframe_to_candles.get(timeframe, 24), len(df))
            price_24h_ago = df['close'].iloc[-lookback]
            price_change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'rsi': round(current_rsi, 2),
                'zone': zone,
                'trend': trend,
                'price': float(current_price),
                'price_change_24h': round(price_change_24h, 2),
                'timestamp': df['timestamp'].iloc[-1]
            }
            
        except Exception as e:
            # Log error for debugging but continue scanning
            print(f"⚠️ Error scanning {symbol} ({timeframe}): {str(e)[:50]}")
            return None
    
    async def scan_all_coins(self, timeframes=['15m', '30m', '1h', '4h'], coins=None):
        """
        Scan all coins across multiple timeframes
        
        Args:
            timeframes: List of timeframes to scan (default: 15m, 30m, 1h, 4h)
            coins: List of coins (default: DEFAULT_WATCHLIST)
        
        Returns:
            Dict with results by timeframe
        """
        if coins is None:
            coins = DEFAULT_WATCHLIST
        
        results = {tf: [] for tf in timeframes}
        
        print(f"\n🔍 Scanning {len(coins)} coins across {len(timeframes)} timeframes...")
        print(f"   Timeframes: {', '.join(timeframes)}")
        
        # Reset problematic coins list
        self.problematic_coins = []
        
        for tf in timeframes:
            print(f"\nScanning {tf} timeframe...")
            
            for i, symbol in enumerate(coins, 1):
                result = await self.scan_single_coin(symbol, tf)
                if result:
                    results[tf].append(result)
                
                # Progress indicator every 20 coins
                if i % 20 == 0:
                    print(f"  Progress: {i}/{len(coins)} coins")
                
                # Rate limiting
                await asyncio.sleep(0.2)
            
            print(f"  ✓ Completed {tf}: {len(results[tf])} valid coins")
        
        # Report problematic coins
        if self.problematic_coins:
            print(f"\n⚠️ Skipped {len(set(self.problematic_coins))} problematic coins: {', '.join(set(self.problematic_coins)[:5])}")
        
        return results
    
    def categorize_results(self, results):
        """
        Categorize results by RSI zones
        
        Returns:
            Dict with categorized lists
        """
        categorized = {
            'extreme_oversold': [],
            'oversold': [],
            'oversold_zone': [],
            'neutral': [],
            'overbought_zone': [],
            'overbought': [],
            'extreme_overbought': []
        }
        
        for coin in results:
            zone_map = {
                'EXTREME_OVERSOLD': 'extreme_oversold',
                'OVERSOLD': 'oversold',
                'OVERSOLD_ZONE': 'oversold_zone',
                'NEUTRAL': 'neutral',
                'OVERBOUGHT_ZONE': 'overbought_zone',
                'OVERBOUGHT': 'overbought',
                'EXTREME_OVERBOUGHT': 'extreme_overbought'
            }
            
            category = zone_map.get(coin['zone'], 'neutral')
            categorized[category].append(coin)
        
        # Sort each category by RSI (extremes first)
        categorized['extreme_oversold'].sort(key=lambda x: x['rsi'])
        categorized['oversold'].sort(key=lambda x: x['rsi'])
        categorized['oversold_zone'].sort(key=lambda x: x['rsi'])
        categorized['overbought_zone'].sort(key=lambda x: x['rsi'], reverse=True)
        categorized['overbought'].sort(key=lambda x: x['rsi'], reverse=True)
        categorized['extreme_overbought'].sort(key=lambda x: x['rsi'], reverse=True)
        
        return categorized
    
    def format_zone_report(self, timeframe, categorized):
        """Format a detailed report for a timeframe"""
        
        trend_emoji = {
            'rising': '📈',
            'falling': '📉',
            'stable': '➡️',
            'unknown': '❓'
        }
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║  RSI ZONE ANALYSIS - {timeframe.upper()} TIMEFRAME
╚══════════════════════════════════════════════════════════════╝

"""
        
        # Extreme Oversold (< 25)
        if categorized['extreme_oversold']:
            report += "🟣 EXTREME OVERSOLD (RSI < 25) - STRONG BUY ZONE\n"
            report += "─" * 62 + "\n"
            for coin in categorized['extreme_oversold']:
                report += f"  {coin['symbol']:12} RSI: {coin['rsi']:5.1f} {trend_emoji[coin['trend']]} "
                report += f"Price: ${coin['price']:>10,.4f} ({coin['price_change_24h']:+.2f}%)\n"
            report += "\n"
        
        # Oversold (25-30)
        if categorized['oversold']:
            report += "🔵 OVERSOLD (RSI 25-30) - BUY ZONE\n"
            report += "─" * 62 + "\n"
            for coin in categorized['oversold']:
                report += f"  {coin['symbol']:12} RSI: {coin['rsi']:5.1f} {trend_emoji[coin['trend']]} "
                report += f"Price: ${coin['price']:>10,.4f} ({coin['price_change_24h']:+.2f}%)\n"
            report += "\n"
        
        # Approaching Oversold (30-40)
        if categorized['oversold_zone']:
            report += "🟢 APPROACHING OVERSOLD (RSI 30-40)\n"
            report += "─" * 62 + "\n"
            for coin in categorized['oversold_zone'][:10]:  # Show top 10
                report += f"  {coin['symbol']:12} RSI: {coin['rsi']:5.1f} {trend_emoji[coin['trend']]} "
                report += f"Price: ${coin['price']:>10,.4f} ({coin['price_change_24h']:+.2f}%)\n"
            if len(categorized['oversold_zone']) > 10:
                report += f"  ... and {len(categorized['oversold_zone']) - 10} more\n"
            report += "\n"
        
        # Approaching Overbought (60-70)
        if categorized['overbought_zone']:
            report += "🟡 APPROACHING OVERBOUGHT (RSI 60-70)\n"
            report += "─" * 62 + "\n"
            for coin in categorized['overbought_zone'][:10]:
                report += f"  {coin['symbol']:12} RSI: {coin['rsi']:5.1f} {trend_emoji[coin['trend']]} "
                report += f"Price: ${coin['price']:>10,.4f} ({coin['price_change_24h']:+.2f}%)\n"
            if len(categorized['overbought_zone']) > 10:
                report += f"  ... and {len(categorized['overbought_zone']) - 10} more\n"
            report += "\n"
        
        # Overbought (70-75)
        if categorized['overbought']:
            report += "🟠 OVERBOUGHT (RSI 70-75) - SELL ZONE\n"
            report += "─" * 62 + "\n"
            for coin in categorized['overbought']:
                report += f"  {coin['symbol']:12} RSI: {coin['rsi']:5.1f} {trend_emoji[coin['trend']]} "
                report += f"Price: ${coin['price']:>10,.4f} ({coin['price_change_24h']:+.2f}%)\n"
            report += "\n"
        
        # Extreme Overbought (> 75)
        if categorized['extreme_overbought']:
            report += "🔴 EXTREME OVERBOUGHT (RSI > 75) - STRONG SELL ZONE\n"
            report += "─" * 62 + "\n"
            for coin in categorized['extreme_overbought']:
                report += f"  {coin['symbol']:12} RSI: {coin['rsi']:5.1f} {trend_emoji[coin['trend']]} "
                report += f"Price: ${coin['price']:>10,.4f} ({coin['price_change_24h']:+.2f}%)\n"
            report += "\n"
        
        # Summary
        total = sum(len(v) for v in categorized.values())
        report += "📊 SUMMARY\n"
        report += "─" * 62 + "\n"
        report += f"  Extreme Oversold:     {len(categorized['extreme_oversold']):3d} coins\n"
        report += f"  Oversold:             {len(categorized['oversold']):3d} coins\n"
        report += f"  Approaching Oversold: {len(categorized['oversold_zone']):3d} coins\n"
        report += f"  Neutral:              {len(categorized['neutral']):3d} coins\n"
        report += f"  Approaching Overbought:{len(categorized['overbought_zone']):3d} coins\n"
        report += f"  Overbought:           {len(categorized['overbought']):3d} coins\n"
        report += f"  Extreme Overbought:   {len(categorized['extreme_overbought']):3d} coins\n"
        report += f"  Total Scanned:        {total:3d} coins\n"
        
        return report
    
    def format_telegram_message(self, timeframe, categorized):
        """Format a Telegram-friendly message"""
        
        message = f"""
<b>📊 RSI ZONES - {timeframe.upper()}</b>

"""
        
        # Only show interesting zones (not neutral)
        has_content = False
        
        if categorized['extreme_oversold']:
            has_content = True
            message += f"<b>🟣 EXTREME OVERSOLD ({len(categorized['extreme_oversold'])})</b>\n"
            for coin in categorized['extreme_oversold'][:5]:
                trend = '📈' if coin['trend'] == 'rising' else '📉' if coin['trend'] == 'falling' else '➡️'
                message += f"  {coin['symbol']} - RSI {coin['rsi']} {trend}\n"
            message += "\n"
        
        if categorized['oversold']:
            has_content = True
            message += f"<b>🔵 OVERSOLD ({len(categorized['oversold'])})</b>\n"
            for coin in categorized['oversold'][:5]:
                trend = '📈' if coin['trend'] == 'rising' else '📉' if coin['trend'] == 'falling' else '➡️'
                message += f"  {coin['symbol']} - RSI {coin['rsi']} {trend}\n"
            message += "\n"
        
        if categorized['overbought']:
            has_content = True
            message += f"<b>🟠 OVERBOUGHT ({len(categorized['overbought'])})</b>\n"
            for coin in categorized['overbought'][:5]:
                trend = '📈' if coin['trend'] == 'rising' else '📉' if coin['trend'] == 'falling' else '➡️'
                message += f"  {coin['symbol']} - RSI {coin['rsi']} {trend}\n"
            message += "\n"
        
        if categorized['extreme_overbought']:
            has_content = True
            message += f"<b>🔴 EXTREME OVERBOUGHT ({len(categorized['extreme_overbought'])})</b>\n"
            for coin in categorized['extreme_overbought'][:5]:
                trend = '📈' if coin['trend'] == 'rising' else '📉' if coin['trend'] == 'falling' else '➡️'
                message += f"  {coin['symbol']} - RSI {coin['rsi']} {trend}\n"
            message += "\n"
        
        if not has_content:
            message += "<i>No extreme zones detected in this timeframe</i>\n\n"
        
        message += f"<i>Scan time: {datetime.now().strftime('%H:%M:%S')}</i>"
        
        return message.strip()


# Add missing pandas import
import pandas as pd


# Standalone test
async def main():
    """Test the RSI zone scanner with all timeframes"""
    print("=" * 70)
    print("RSI OVERBOUGHT/OVERSOLD ZONE SCANNER")
    print("Enhanced: 15m, 30m, 1h, 4h timeframes")
    print("=" * 70)
    
    scanner = RSIZoneScanner(
        extreme_oversold=25,
        oversold=30,
        neutral_low=40,
        neutral_high=60,
        overbought=70,
        extreme_overbought=75
    )
    
    # Scan all timeframes
    results = await scanner.scan_all_coins(
        timeframes=['15m', '30m', '1h', '4h'],
        coins=DEFAULT_WATCHLIST[:30]  # Test with first 30 coins
    )
    
    # Generate reports for each timeframe
    for timeframe in ['15m', '30m', '1h', '4h']:
        categorized = scanner.categorize_results(results[timeframe])
        report = scanner.format_zone_report(timeframe, categorized)
        print(report)
    
    print("\n✓ RSI zone scanning complete!")


if __name__ == "__main__":
    asyncio.run(main())
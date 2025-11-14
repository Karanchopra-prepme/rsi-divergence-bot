"""
Multi-coin scanner - UPDATED for structural divergence detection
Scans multiple coins across multiple timeframes using NEW detector
"""

import time
from datetime import datetime
from analyzer.data_fetcher import DataFetcher
from analyzer.rsi_calculator import RSICalculator
from analyzer.divergence_detector import StructuralDivergenceDetector  # NEW
from config.settings import TIMEFRAMES, MAX_COINS_PER_SCAN
from config.coin_list import DEFAULT_WATCHLIST

class Scanner:
    """Scan multiple coins for RSI divergences using STRUCTURAL detection"""
    
    def __init__(self):
        self.fetcher = DataFetcher()
        self.rsi_calc = RSICalculator()
        
        # Use NEW structural detector
        self.detector = StructuralDivergenceDetector(
            swing_window=3,
            rsi_bull_threshold=45,
            rsi_bear_threshold=55,
            min_price_move_pct=0.4,
            volume_multiplier=1.05,
            use_ema_filter=False,
            ema_period=50
        )
        
        self.scan_count = 0
        self.total_divergences_found = 0
    
    def scan_single_coin(self, symbol, timeframe='15m'):
        """
        Scan a single coin for STRUCTURAL divergences
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe
        
        Returns:
            List of divergences or None
        """
        try:
            # Fetch data
            df = self.fetcher.fetch_ohlcv(symbol, timeframe, limit=200)
            
            if df is None or len(df) < 50:
                return None
            
            # Calculate RSI
            df = self.rsi_calc.calculate_rsi(df)
            
            if df is None or 'rsi' not in df.columns:
                return None
            
            # Detect STRUCTURAL divergences
            divergences = self.detector.detect_all_divergences(df)
            
            if divergences:
                # Add symbol and timeframe info
                for div in divergences:
                    div['symbol'] = symbol
                    div['timeframe'] = timeframe
                
                return divergences
            
            return None
            
        except Exception as e:
            print(f"Error scanning {symbol} on {timeframe}: {e}")
            return None
    
    def scan_coin_multi_timeframe(self, symbol, timeframes=None):
        """
        Scan a coin across multiple timeframes
        
        Args:
            symbol: Trading pair
            timeframes: List of timeframes (uses config default if None)
        
        Returns:
            List of divergences found across all timeframes
        """
        if timeframes is None:
            timeframes = TIMEFRAMES
        
        all_divergences = []
        
        for tf in timeframes:
            divergences = self.scan_single_coin(symbol, tf)
            
            if divergences:
                all_divergences.extend(divergences)
            
            # Rate limiting
            time.sleep(0.3)
        
        return all_divergences if all_divergences else None
    
    def scan_multiple_coins(self, symbols, timeframe='15m', max_coins=None):
        """
        Scan multiple coins on a single timeframe
        
        Args:
            symbols: List of trading pairs
            timeframe: Candle timeframe
            max_coins: Maximum number of coins to scan
        
        Returns:
            List of all divergences found
        """
        if max_coins is None:
            max_coins = MAX_COINS_PER_SCAN
        
        # Limit coin count
        symbols = symbols[:max_coins]
        
        all_divergences = []
        scanned = 0
        
        print(f"\n{'='*60}")
        print(f"STRUCTURAL Scanning {len(symbols)} coins on {timeframe}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print('='*60)
        
        for i, symbol in enumerate(symbols, 1):
            try:
                print(f"[{i}/{len(symbols)}] Scanning {symbol}...", end=' ')
                
                divergences = self.scan_single_coin(symbol, timeframe)
                
                if divergences:
                    print(f"✓ Found {len(divergences)} divergence(s)!")
                    all_divergences.extend(divergences)
                    self.total_divergences_found += len(divergences)
                else:
                    print("—")
                
                scanned += 1
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"✗ Error: {e}")
                continue
        
        self.scan_count += 1
        
        print('='*60)
        print(f"Scan complete: {scanned}/{len(symbols)} coins scanned")
        print(f"STRUCTURAL divergences found: {len(all_divergences)}")
        print('='*60)
        
        return all_divergences
    
    def scan_multiple_coins_multi_timeframe(self, symbols, timeframes=None):
        """
        Scan multiple coins across multiple timeframes
        
        Args:
            symbols: List of trading pairs
            timeframes: List of timeframes
        
        Returns:
            Dictionary with results organized by symbol and timeframe
        """
        if timeframes is None:
            timeframes = TIMEFRAMES
        
        results = {}
        total_divergences = 0
        
        print(f"\n{'='*60}")
        print(f"STRUCTURAL SCAN - Multi-Timeframe")
        print(f"Coins: {len(symbols)} | Timeframes: {timeframes}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print('='*60)
        
        for symbol in symbols:
            symbol_results = []
            
            for tf in timeframes:
                try:
                    print(f"Scanning {symbol} on {tf}...", end=' ')
                    
                    divergences = self.scan_single_coin(symbol, tf)
                    
                    if divergences:
                        print(f"✓ {len(divergences)} found")
                        symbol_results.extend(divergences)
                        total_divergences += len(divergences)
                    else:
                        print("—")
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"✗ Error: {e}")
                    continue
            
            if symbol_results:
                results[symbol] = symbol_results
        
        print('='*60)
        print(f"Multi-timeframe scan complete!")
        print(f"Total STRUCTURAL divergences: {total_divergences}")
        print(f"Coins with divergences: {len(results)}")
        print('='*60)
        
        self.scan_count += 1
        self.total_divergences_found += total_divergences
        
        return results
    
    def check_multi_timeframe_confluence(self, symbol, timeframes=['15m', '30m']):
        """
        Check if divergence exists on multiple timeframes (stronger signal)
        
        Args:
            symbol: Trading pair
            timeframes: List of timeframes to check
        
        Returns:
            Dictionary with confluence info or None
        """
        divergences_by_tf = {}
        
        for tf in timeframes:
            divs = self.scan_single_coin(symbol, tf)
            if divs:
                divergences_by_tf[tf] = divs
            time.sleep(0.3)
        
        if len(divergences_by_tf) >= 2:
            # Found divergence on multiple timeframes!
            return {
                'symbol': symbol,
                'confluence': True,
                'timeframes': list(divergences_by_tf.keys()),
                'divergences': divergences_by_tf,
                'strength': 'VERY HIGH (Multi-timeframe confluence)'
            }
        
        return None
    
    def get_scan_statistics(self):
        """Get scanner statistics"""
        return {
            'total_scans': self.scan_count,
            'total_divergences': self.total_divergences_found,
            'avg_per_scan': round(self.total_divergences_found / max(self.scan_count, 1), 2)
        }
    
    def quick_scan(self, category='top', timeframe='15m'):
        """
        Quick scan of predefined coin categories
        
        Args:
            category: 'top', 'mid', 'defi', 'layer1', 'meme', 'gaming', 'ai', 'all'
            timeframe: Timeframe to scan
        
        Returns:
            List of divergences found
        """
        from config.coin_list import get_coins_by_category
        
        coins = get_coins_by_category(category)
        print(f"\nQuick STRUCTURAL scan: {category.upper()} ({len(coins)} coins)")
        
        return self.scan_multiple_coins(coins, timeframe)
    
    def format_alert(self, divergence):
        """Format divergence alert using detector's format method"""
        return self.detector.format_divergence_alert(
            divergence,
            divergence['symbol'],
            divergence['timeframe']
        )


# Test the updated scanner
if __name__ == "__main__":
    print("=" * 60)
    print("Testing STRUCTURAL Scanner")
    print("=" * 60)
    
    scanner = Scanner()
    
    # Test 1: Scan single coin
    print("\n1. Single coin STRUCTURAL scan (BTC/USDT on 4h):")
    result = scanner.scan_single_coin('BTC/USDT', '15m')
    if result:
        for div in result:
            print(scanner.format_alert(div))
    else:
        print("No structural divergences found (filters working!)")
    
    # Test 2: Quick scan top coins
    print("\n2. Quick scan - Top 5 coins:")
    from config.coin_list import TOP_COINS
    results = scanner.scan_multiple_coins(TOP_COINS[:5], '15m')
    
    if results:
        print(f"\n✓ Found {len(results)} STRUCTURAL divergences:")
        for div in results:
            print(f"  - {div['symbol']} ({div['type']}) Strength: {div['strength']}")
    else:
        print("No structural divergences (this is good - filters working!)")
    
    # Statistics
    print("\n" + "="*60)
    stats = scanner.get_scan_statistics()
    print("Scanner Statistics:")
    print(f"  Total scans: {stats['total_scans']}")
    print(f"  Total divergences: {stats['total_divergences']}")
    print(f"  Average per scan: {stats['avg_per_scan']}")
    print("="*60)
    
    print("\n✓ STRUCTURAL scanner test complete!")
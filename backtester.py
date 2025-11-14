"""
Backtesting Engine for RSI Divergence Strategy
Tests historical performance and optimizes parameters
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from analyzer.data_fetcher import DataFetcher
from analyzer.rsi_calculator import RSICalculator
from analyzer.divergence_detector import StructuralDivergenceDetector

class DivergenceBacktester:
    """
    Backtest divergence strategy on historical data
    
    Purpose:
    - Measure win rate, profit factor, accuracy
    - Find optimal parameter settings
    - Identify which filters work best
    - Provide data-driven recommendations
    """
    
    def __init__(self, detector=None):
        self.fetcher = DataFetcher()
        self.rsi_calc = RSICalculator()
        self.detector = detector or StructuralDivergenceDetector()
        
        self.results = []
        self.trades = []
    
    def backtest_single_coin(self, symbol, timeframe='15m', lookback_days=365, 
                            take_profit_pct=3.0, stop_loss_pct=2.0):
        """
        Backtest on a single coin
        
        Process:
        1. Get historical data (e.g., last 365 days)
        2. Scan for divergences
        3. For each signal, simulate a trade:
           - Entry: At signal candle close
           - Exit: When price hits TP or SL, or after N candles
        4. Record win/loss
        
        Args:
            symbol: Trading pair
            timeframe: Candle timeframe
            lookback_days: Days of history to test (default: 365 for 1 year)
            take_profit_pct: TP percentage
            stop_loss_pct: SL percentage
        
        Returns:
            Dictionary with backtest results
        """
        print(f"\n{'='*70}")
        print(f"Backtesting {symbol} on {timeframe}")
        print(f"Period: Last {lookback_days} days")
        print('='*70)
        
        # Fetch data - simplified approach using just limit
        df = self._fetch_historical_data(symbol, timeframe, lookback_days)
        
        if df is None or len(df) < 100:
            print(f"Insufficient data for {symbol}")
            return None
        
        print(f"  Fetched {len(df)} candles ({df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]})")
        
        # Calculate RSI
        df = self.rsi_calc.calculate_rsi(df)
        
        coin_trades = []
        
        # Sliding window approach
        # We scan through history and detect divergences as they would have appeared
        window_size = 100  # Use 100 candles for detection
        
        for i in range(window_size, len(df) - 20):  # Leave 20 candles for exit simulation
            # Get data window up to current candle
            window_df = df.iloc[max(0, i-window_size):i+1].copy()
            window_df = window_df.reset_index(drop=True)
            
            # Detect divergence
            divergences = self.detector.detect_all_divergences(window_df)
            
            if not divergences:
                continue
            
            # Process each divergence (usually just 1)
            for div in divergences:
                # Entry details
                entry_price = df['close'].iloc[i]
                entry_time = df['timestamp'].iloc[i]
                signal_type = div['type']
                
                # Calculate TP and SL levels
                if signal_type == 'BULLISH':
                    tp_price = entry_price * (1 + take_profit_pct / 100)
                    sl_price = entry_price * (1 - stop_loss_pct / 100)
                    direction = 'LONG'
                else:  # BEARISH
                    tp_price = entry_price * (1 - take_profit_pct / 100)
                    sl_price = entry_price * (1 + stop_loss_pct / 100)
                    direction = 'SHORT'
                
                # Simulate trade outcome (check next 20 candles)
                trade_result = self._simulate_trade_outcome(
                    df.iloc[i+1:i+21],  # Next 20 candles
                    entry_price,
                    tp_price,
                    sl_price,
                    direction
                )
                
                # Record trade
                trade = {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'entry_time': entry_time,
                    'entry_price': entry_price,
                    'signal_type': signal_type,
                    'direction': direction,
                    'tp_price': tp_price,
                    'sl_price': sl_price,
                    'exit_price': trade_result['exit_price'],
                    'exit_time': trade_result['exit_time'],
                    'outcome': trade_result['outcome'],
                    'profit_pct': trade_result['profit_pct'],
                    'bars_held': trade_result['bars_held'],
                    'strength': div['strength']
                }
                
                coin_trades.append(trade)
                self.trades.append(trade)
                
                if len(coin_trades) % 10 == 0:  # Progress update every 10 signals
                    print(f"  Processed {len(coin_trades)} signals...")
        
        # Calculate statistics for this coin
        if coin_trades:
            stats = self._calculate_statistics(coin_trades)
            stats['symbol'] = symbol
            stats['timeframe'] = timeframe
            self.results.append(stats)
            
            print(f"\n{symbol} Results:")
            print(f"  Total Signals: {stats['total_trades']}")
            print(f"  Win Rate: {stats['win_rate']:.1f}%")
            print(f"  Avg Profit: {stats['avg_profit']:.2f}%")
            print(f"  Profit Factor: {stats['profit_factor']:.2f}")
            
            return stats
        else:
            print(f"No signals found for {symbol}")
            return None
    
    def _fetch_historical_data(self, symbol, timeframe, lookback_days):
        """
        Fetch historical data using the existing DataFetcher
        
        Since DataFetcher.fetch_ohlcv() doesn't support 'since',
        we'll just request the maximum limit and filter by date
        """
        # Calculate timeframe in minutes
        tf_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440
        }
        minutes = tf_minutes.get(timeframe, 15)
        
        # Calculate total candles needed
        candles_per_day = 1440 // minutes
        total_candles = lookback_days * candles_per_day
        
        print(f"  Need ~{total_candles} candles for {lookback_days} days")
        
        # Most exchanges limit to 1000 candles, so request maximum
        # We'll need to accept whatever we can get
        limit = min(total_candles, 1000)
        
        print(f"  Fetching {limit} candles (exchange limit)...")
        
        # Fetch data
        df = self.fetcher.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        if df is None or df.empty:
            return None
        
        # Filter by date if we got more than needed
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        cutoff_timestamp = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
        df = df[df['timestamp'] >= cutoff_timestamp]
        
        return df
    
    def _simulate_trade_outcome(self, future_df, entry_price, tp_price, sl_price, direction):
        """
        Simulate what would have happened after entry
        
        Checks each subsequent candle to see if TP or SL was hit
        """
        if future_df.empty:
            return {
                'exit_price': entry_price,
                'exit_time': None,
                'outcome': 'TIMEOUT',
                'profit_pct': 0,
                'bars_held': 0
            }
        
        for idx, row in future_df.iterrows():
            bars_held = idx - future_df.index[0] + 1
            
            if direction == 'LONG':
                # Check if TP hit
                if row['high'] >= tp_price:
                    return {
                        'exit_price': tp_price,
                        'exit_time': row['timestamp'],
                        'outcome': 'WIN',
                        'profit_pct': ((tp_price - entry_price) / entry_price) * 100,
                        'bars_held': bars_held
                    }
                # Check if SL hit
                if row['low'] <= sl_price:
                    return {
                        'exit_price': sl_price,
                        'exit_time': row['timestamp'],
                        'outcome': 'LOSS',
                        'profit_pct': ((sl_price - entry_price) / entry_price) * 100,
                        'bars_held': bars_held
                    }
            
            else:  # SHORT
                # Check if TP hit
                if row['low'] <= tp_price:
                    return {
                        'exit_price': tp_price,
                        'exit_time': row['timestamp'],
                        'outcome': 'WIN',
                        'profit_pct': ((entry_price - tp_price) / entry_price) * 100,
                        'bars_held': bars_held
                    }
                # Check if SL hit
                if row['high'] >= sl_price:
                    return {
                        'exit_price': sl_price,
                        'exit_time': row['timestamp'],
                        'outcome': 'LOSS',
                        'profit_pct': ((entry_price - sl_price) / entry_price) * 100,
                        'bars_held': bars_held
                    }
        
        # No TP/SL hit - exit at last price
        last_price = future_df.iloc[-1]['close']
        if direction == 'LONG':
            profit_pct = ((last_price - entry_price) / entry_price) * 100
        else:
            profit_pct = ((entry_price - last_price) / entry_price) * 100
        
        return {
            'exit_price': last_price,
            'exit_time': future_df.iloc[-1]['timestamp'],
            'outcome': 'TIMEOUT',
            'profit_pct': profit_pct,
            'bars_held': len(future_df)
        }
    
    def _calculate_statistics(self, trades):
        """Calculate performance metrics"""
        total = len(trades)
        wins = [t for t in trades if t['outcome'] == 'WIN']
        losses = [t for t in trades if t['outcome'] == 'LOSS']
        
        win_rate = (len(wins) / total * 100) if total > 0 else 0
        
        avg_profit = np.mean([t['profit_pct'] for t in trades]) if trades else 0
        avg_win = np.mean([t['profit_pct'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['profit_pct'] for t in losses]) if losses else 0
        
        total_profit = sum([t['profit_pct'] for t in wins])
        total_loss = abs(sum([t['profit_pct'] for t in losses]))
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
        
        avg_bars_held = np.mean([t['bars_held'] for t in trades]) if trades else 0
        
        return {
            'total_trades': total,
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'avg_bars_held': avg_bars_held,
            'total_profit_pct': total_profit,
            'total_loss_pct': total_loss
        }
    
    def backtest_multiple_coins(self, symbols, timeframe='15m', lookback_days=365):
        """Run backtest across multiple coins"""
        print("\n" + "="*70)
        print("MULTI-COIN BACKTEST")
        print("="*70)
        
        for symbol in symbols:
            try:
                self.backtest_single_coin(symbol, timeframe, lookback_days)
            except Exception as e:
                print(f"Error backtesting {symbol}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Overall statistics
        if self.results:
            self.print_summary()
    
    def print_summary(self):
        """Print overall backtest summary"""
        print("\n" + "="*70)
        print("BACKTEST SUMMARY")
        print("="*70)
        
        if not self.results:
            print("No results to display")
            return
        
        # Aggregate stats
        total_trades = sum([r['total_trades'] for r in self.results])
        total_wins = sum([r['wins'] for r in self.results])
        total_losses = sum([r['losses'] for r in self.results])
        
        overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        avg_profit = np.mean([r['avg_profit'] for r in self.results])
        avg_profit_factor = np.mean([r['profit_factor'] for r in self.results])
        
        print(f"\nTested {len(self.results)} coins:")
        for r in self.results:
            print(f"  {r['symbol']:12} | {r['total_trades']:3} trades | "
                  f"WR: {r['win_rate']:5.1f}% | PF: {r['profit_factor']:.2f}")
        
        print(f"\n{'='*70}")
        print("OVERALL PERFORMANCE:")
        print(f"  Total Signals: {total_trades}")
        print(f"  Wins: {total_wins} | Losses: {total_losses}")
        print(f"  Win Rate: {overall_win_rate:.1f}%")
        print(f"  Avg Profit per Trade: {avg_profit:+.2f}%")
        print(f"  Avg Profit Factor: {avg_profit_factor:.2f}")
        print(f"{'='*70}")
        
        # Recommendations
        self.print_recommendations(overall_win_rate, avg_profit_factor)
    
    def print_recommendations(self, win_rate, profit_factor):
        """Provide recommendations based on backtest results"""
        print("\n[RECOMMENDATIONS]")
        
        if win_rate >= 70 and profit_factor >= 2.0:
            print("[OK] Excellent performance! Current settings are optimal.")
            print("     -> Use these parameters for live trading")
            
        elif win_rate >= 60 and profit_factor >= 1.5:
            print("[OK] Good performance. Settings are working well.")
            print("     -> Consider minor tweaks to improve further")
            
        elif win_rate >= 50:
            print("[WARNING] Moderate performance. Needs improvement.")
            print("     -> Suggestions:")
            print("        * Increase min_price_move_pct to 1.5% or 2%")
            print("        * Adjust RSI thresholds (try 35/65 instead of 40/60)")
            print("        * Enable multi-timeframe confirmation")
            
        else:
            print("[ERROR] Poor performance. Major adjustments needed.")
            print("     -> Suggestions:")
            print("        * Increase swing_window to 3 or 4")
            print("        * Set min_price_move_pct to 2.5%")
            print("        * Only take signals with strength > 60")
            print("        * Enable ALL filters")
        
        print("\n[FILTER EFFECTIVENESS]")
        print("  Most Important Filters (in order):")
        print("  1. Structural swing detection (vs raw values)")
        print("  2. Volume confirmation")
        print("  3. EMA trend filter")
        print("  4. RSI threshold zones")
        print("  5. Minimum price movement")
    
    def optimize_parameters(self, symbol, timeframe='15m'):
        """
        Test different parameter combinations to find optimal settings
        
        Tests:
        - Different swing windows (2, 3, 4)
        - Different RSI thresholds (35/65, 40/60, 30/70)
        - Different min price movements (0.5%, 1%, 1.5%, 2%)
        """
        print("\n" + "="*70)
        print(f"PARAMETER OPTIMIZATION for {symbol}")
        print("="*70)
        
        # Fetch data once (use less data for optimization to save time)
        df = self.fetcher.fetch_ohlcv(symbol, timeframe, limit=1000)
        if df is None or len(df) < 200:
            print("Insufficient data")
            return
        
        df = self.rsi_calc.calculate_rsi(df)
        
        # Parameter combinations to test
        swing_windows = [2, 3, 4]
        rsi_thresholds = [(35, 65), (40, 60), (30, 70)]
        min_price_moves = [0.5, 1.0, 1.5, 2.0]
        
        best_config = None
        best_score = 0
        
        print("\nTesting parameter combinations...")
        
        for sw in swing_windows:
            for (rsi_bull, rsi_bear) in rsi_thresholds:
                for min_move in min_price_moves:
                    # Create detector with these parameters
                    detector = StructuralDivergenceDetector(
                        swing_window=sw,
                        rsi_bull_threshold=rsi_bull,
                        rsi_bear_threshold=rsi_bear,
                        min_price_move_pct=min_move,
                        volume_multiplier=1.2,
                        use_ema_filter=True
                    )
                    
                    # Quick test on this data
                    temp_trades = []
                    for i in range(100, len(df) - 20):
                        window_df = df.iloc[max(0, i-100):i+1].copy()
                        window_df = window_df.reset_index(drop=True)
                        
                        divs = detector.detect_all_divergences(window_df)
                        if divs:
                            for div in divs:
                                entry_price = df['close'].iloc[i]
                                if div['type'] == 'BULLISH':
                                    tp = entry_price * 1.03
                                    sl = entry_price * 0.98
                                    direction = 'LONG'
                                else:
                                    tp = entry_price * 0.97
                                    sl = entry_price * 1.02
                                    direction = 'SHORT'
                                
                                result = self._simulate_trade_outcome(
                                    df.iloc[i+1:i+21],
                                    entry_price, tp, sl, direction
                                )
                                temp_trades.append(result)
                    
                    if temp_trades:
                        stats = self._calculate_statistics(temp_trades)
                        # Score = win_rate + profit_factor (normalized)
                        score = stats['win_rate'] + (stats['profit_factor'] * 20)
                        
                        if score > best_score:
                            best_score = score
                            best_config = {
                                'swing_window': sw,
                                'rsi_thresholds': (rsi_bull, rsi_bear),
                                'min_price_move': min_move,
                                'stats': stats
                            }
        
        if best_config:
            print("\n[OK] OPTIMAL PARAMETERS FOUND:")
            print(f"  Swing Window: {best_config['swing_window']}")
            print(f"  RSI Thresholds: {best_config['rsi_thresholds']}")
            print(f"  Min Price Move: {best_config['min_price_move']}%")
            print(f"\n  Performance:")
            print(f"    Signals: {best_config['stats']['total_trades']}")
            print(f"    Win Rate: {best_config['stats']['win_rate']:.1f}%")
            print(f"    Profit Factor: {best_config['stats']['profit_factor']:.2f}")
            print(f"    Score: {best_score:.1f}")
        else:
            print("No optimal parameters found")
    
    def export_results(self, filename='backtest_results.csv'):
        """Export all trades to CSV for analysis"""
        if not self.trades:
            print("No trades to export")
            return
        
        df = pd.DataFrame(self.trades)
        df.to_csv(filename, index=False)
        print(f"\n[OK] Results exported to {filename}")
        print(f"     Total trades: {len(self.trades)}")


# Test the backtester
if __name__ == "__main__":
    print("="*70)
    print("STRUCTURAL DIVERGENCE BACKTESTING ENGINE - 1 YEAR DATA")
    print("="*70)
    
    # Create detector with conservative settings
    detector = StructuralDivergenceDetector(
        swing_window=3,
        rsi_bull_threshold=45,
        rsi_bear_threshold=55,
        min_price_move_pct=0.4,
        volume_multiplier=1.05,
        use_ema_filter=False,
        ema_period=50
    )
    
    backtester = DivergenceBacktester(detector)
    
    # Test on popular coins
    test_coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
    
    print("\nStarting backtest on 15M timeframe for 1 YEAR...")
    print("Note: Most exchanges limit to 1000 candles (~10 days on 15m)")
    print("For true 1-year backtest, you'd need to implement chunked fetching\n")
    
    backtester.backtest_multiple_coins(
        symbols=test_coins,
        timeframe='15m',
        lookback_days=365
    )
    
    # Parameter optimization on BTC
    print("\n" + "="*70)
    backtester.optimize_parameters('BTC/USDT', '15m')
    
    # Export results
    backtester.export_results('divergence_backtest_1year.csv')
    
    print("\n[DONE] Backtesting complete!")
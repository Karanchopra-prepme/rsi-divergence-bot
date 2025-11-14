"""
Data fetcher for cryptocurrency market data
Handles fetching OHLCV data from exchanges
"""

import ccxt
import pandas as pd
from datetime import datetime
import time
from config.settings import EXCHANGE

class DataFetcher:
    """Fetch real-time market data from exchanges"""
    
    def __init__(self, exchange_name=EXCHANGE):
        """Initialize exchange connection"""
        self.exchange_name = exchange_name
        self.exchange = self._initialize_exchange(exchange_name)
        print(f"✓ Connected to {exchange_name}")
    
    def _initialize_exchange(self, exchange_name):
        """Create exchange instance with proper configuration"""
        try:
            exchange_class = getattr(ccxt, exchange_name)
            exchange = exchange_class({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True
                }
            })
            
            # Load markets
            exchange.load_markets()
            return exchange
            
        except Exception as e:
            print(f"❌ Error connecting to {exchange_name}: {e}")
            raise
    
    def fetch_ohlcv(self, symbol, timeframe='15m', limit=100):
        """
        Fetch OHLCV (Open, High, Low, Close, Volume) data
        with retry and fallback to Binance Futures on failure.
        """
        max_retries = 3
        delay = 3  # seconds between retries

        for attempt in range(1, max_retries + 1):
            try:
                # Try fetching data
                ohlcv = self.exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)

                # Convert to DataFrame
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

                # Ensure numeric data types
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                df = df.dropna()
                return df

            except ccxt.NetworkError as e:
                print(f"⚠️ Network error fetching {symbol} (attempt {attempt}/{max_retries}): {e}")
                time.sleep(delay)
            except ccxt.ExchangeError as e:
                print(f"⚠️ Exchange error fetching {symbol}: {e}")
                break
            except Exception as e:
                print(f"⚠️ Unexpected error fetching {symbol}: {e}")
                time.sleep(delay)

        # Optional fallback to Binance Futures if spot fails entirely
        if self.exchange_name == "binance":
            try:
                print(f"↩️ Retrying {symbol} via Binance Futures (USDM)...")
                futures = ccxt.binanceusdm({'enableRateLimit': True})
                ohlcv = futures.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)

                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                df = df.dropna()
                return df
            except Exception as e:
                print(f"❌ Failed fetching {symbol} even via Futures: {e}")

        print(f"❌ Failed to fetch {symbol} after {max_retries} attempts.")
        return None

    
    def fetch_current_price(self, symbol):
        """
        Fetch current price for a symbol
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
        
        Returns:
            Current price as float or None
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None
    
    def get_available_symbols(self):
        """
        Get list of available trading pairs on the exchange
        
        Returns:
            List of symbol strings
        """
        try:
            markets = self.exchange.load_markets()
            # Filter for USDT pairs only
            usdt_pairs = [
                symbol for symbol in markets.keys()
                if symbol.endswith('/USDT') and markets[symbol]['spot']
            ]
            return sorted(usdt_pairs)
        except Exception as e:
            print(f"Error getting symbols: {e}")
            return []
    
    def validate_symbol(self, symbol):
        """
        Check if a symbol is valid and tradable
        
        Args:
            symbol: Trading pair to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            markets = self.exchange.load_markets()
            return symbol in markets and markets[symbol]['spot']
        except:
            return False
    
    def fetch_24h_volume(self, symbol):
        """
        Fetch 24-hour trading volume
        
        Args:
            symbol: Trading pair
        
        Returns:
            24h volume in quote currency (USDT)
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker.get('quoteVolume', 0)
        except Exception as e:
            print(f"Error fetching volume for {symbol}: {e}")
            return 0
    
    def fetch_multiple_timeframes(self, symbol, timeframes=['15m', '30m'], limit=100):
        """
        Fetch data for multiple timeframes at once
        
        Args:
            symbol: Trading pair
            timeframes: List of timeframes to fetch
            limit: Number of candles per timeframe
        
        Returns:
            Dictionary with timeframe as key and DataFrame as value
        """
        result = {}
        
        for tf in timeframes:
            df = self.fetch_ohlcv(symbol, tf, limit)
            if df is not None and not df.empty:
                result[tf] = df
            time.sleep(0.2)  # Rate limiting
        
        return result
    
    def get_market_info(self, symbol):
        """
        Get detailed market information for a symbol
        
        Args:
            symbol: Trading pair
        
        Returns:
            Dictionary with market info
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            
            return {
                'symbol': symbol,
                'price': ticker['last'],
                'volume_24h': ticker.get('quoteVolume', 0),
                'change_24h': ticker.get('percentage', 0),
                'high_24h': ticker.get('high', 0),
                'low_24h': ticker.get('low', 0),
                'timestamp': datetime.now()
            }
        except Exception as e:
            print(f"Error getting market info for {symbol}: {e}")
            return None

# Test the data fetcher
if __name__ == "__main__":
    print("=" * 60)
    print("Testing Data Fetcher")
    print("=" * 60)
    
    # Initialize
    fetcher = DataFetcher()
    
    # Test single symbol
    print("\n1. Fetching BTC/USDT 4H data...")
    df = fetcher.fetch_ohlcv('BTC/USDT', '15m', limit=20)
    
    if df is not None:
        print(f"✓ Fetched {len(df)} candles")
        print(f"\nLatest data:")
        print(df.tail(3))
        print(f"\nCurrent price: ${df['close'].iloc[-1]:,.2f}")
    
    # Test current price
    print("\n2. Fetching current prices...")
    for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        price = fetcher.fetch_current_price(symbol)
        if price:
            print(f"{symbol}: ${price:,.2f}")
    
    # Test market info
    print("\n3. Getting market info for BTC/USDT...")
    info = fetcher.get_market_info('BTC/USDT')
    if info:
        print(f"Price: ${info['price']:,.2f}")
        print(f"24h Volume: ${info['volume_24h']:,.0f}")
        print(f"24h Change: {info['change_24h']:.2f}%")
    
    print("\n✓ Data fetcher test complete!")
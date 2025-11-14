"""
Complete system test script
Tests all components before running main bot
"""

import sys
import os

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_imports():
    """Test if all required packages are installed"""
    print_section("Testing Package Imports")
    
    packages = {
        'ccxt': 'Exchange API',
        'pandas': 'Data Processing',
        'numpy': 'Numerical Computing',
        'ta': 'Technical Analysis',
        'telegram': 'Telegram Bot',
        'sqlalchemy': 'Database',
        'dotenv': 'Environment Variables',
        'apscheduler': 'Task Scheduling'
    }
    
    failed = []
    
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"✓ {package:15} - {description}")
        except ImportError:
            print(f"✗ {package:15} - {description} (MISSING)")
            failed.append(package)
    
    if failed:
        print(f"\n❌ Missing packages: {', '.join(failed)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("\n✅ All packages installed!")
    return True

def test_config():
    """Test configuration"""
    print_section("Testing Configuration")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token:
        print("✗ TELEGRAM_BOT_TOKEN not found in .env")
        return False
    
    if not chat_id:
        print("✗ TELEGRAM_CHAT_ID not found in .env")
        return False
    
    print(f"✓ Bot Token: {token[:10]}...")
    print(f"✓ Chat ID: {chat_id}")
    print("\n✅ Configuration valid!")
    return True

def test_data_fetcher():
    """Test data fetching"""
    print_section("Testing Data Fetcher")
    
    try:
        from analyzer.data_fetcher import DataFetcher
        
        fetcher = DataFetcher()
        print("✓ Exchange connected")
        
        df = fetcher.fetch_ohlcv('BTC/USDT', '15m', limit=20)
        
        if df is not None and len(df) > 0:
            print(f"✓ Fetched {len(df)} candles")
            print(f"✓ Latest BTC price: ${df['close'].iloc[-1]:,.2f}")
            print("\n✅ Data fetcher working!")
            return True
        else:
            print("✗ No data returned")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_rsi_calculator():
    """Test RSI calculation"""
    print_section("Testing RSI Calculator")
    
    try:
        from analyzer.data_fetcher import DataFetcher
        from analyzer.rsi_calculator import RSICalculator
        
        fetcher = DataFetcher()
        calculator = RSICalculator()
        
        df = fetcher.fetch_ohlcv('ETH/USDT', '15m', limit=50)
        df = calculator.calculate_rsi(df)
        
        if df is not None and 'rsi' in df.columns:
            current_rsi = df['rsi'].iloc[-1]
            print(f"✓ RSI calculated: {current_rsi:.2f}")
            print(f"✓ Zone: {calculator.get_rsi_zone(current_rsi).upper()}")
            print("\n✅ RSI calculator working!")
            return True
        else:
            print("✗ RSI not calculated")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_divergence_detector():
    """Test divergence detection"""
    print_section("Testing Divergence Detector")
    
    try:
        from analyzer.data_fetcher import DataFetcher
        from analyzer.rsi_calculator import RSICalculator
        from analyzer.divergence_detector import DivergenceDetector
        
        fetcher = DataFetcher()
        rsi_calc = RSICalculator()
        detector = DivergenceDetector()
        
        # Test with BTC
        df = fetcher.fetch_ohlcv('BTC/USDT', '15m', limit=100)
        df = rsi_calc.calculate_rsi(df)
        
        divergences = detector.detect_all_divergences(df)
        
        if divergences:
            print(f"✓ Found {len(divergences)} divergence(s) in BTC!")
            for div in divergences:
                print(f"  - {div['type']} divergence (strength: {div['strength']})")
        else:
            print("✓ No divergences (this is normal)")
        
        print("\n✅ Divergence detector working!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_scanner():
    """Test multi-coin scanner"""
    print_section("Testing Scanner")
    
    try:
        from analyzer.scanner import Scanner
        
        scanner = Scanner()
        
        # Quick scan
        test_coins = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        print(f"Scanning {len(test_coins)} coins...")
        
        results = scanner.scan_multiple_coins(test_coins, '15m')
        
        if results:
            print(f"✓ Found {len(results)} divergence(s)!")
        else:
            print("✓ No divergences (normal)")
        
        print("\n✅ Scanner working!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_database():
    """Test database"""
    print_section("Testing Database")
    
    try:
        from database.db_manager import DatabaseManager
        
        db = DatabaseManager()
        
        # Test save
        test_div = {
            'symbol': 'TEST/USDT',
            'timeframe': '15m',
            'type': 'BULLISH',
            'current_price': 100.0,
            'current_rsi': 35.0,
            'strength': 50.0,
            'volume_confirmed': True
        }
        
        record_id = db.save_divergence(test_div)
        print(f"✓ Saved test record (ID: {record_id})")
        
        # Get stats
        stats = db.get_statistics()
        print(f"✓ Total records: {stats['total']}")
        
        print("\n✅ Database working!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_telegram():
    """Test Telegram bot connection"""
    print_section("Testing Telegram Bot")
    
    try:
        from bot.telegram_bot import TelegramBot
        
        bot = TelegramBot()
        print(f"✓ Bot initialized")
        print(f"✓ Token: {bot.token[:10]}...")
        print(f"✓ Chat ID: {bot.chat_id}")
        
        print("\n✅ Telegram bot ready!")
        print("\n⚠️  To fully test: Run 'python bot/telegram_bot.py' and send /start")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         RSI DIVERGENCE BOT - SYSTEM TEST                  ║
║         Testing all components...                         ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    tests = [
        ("Package Imports", test_imports),
        ("Configuration", test_config),
        ("Data Fetcher", test_data_fetcher),
        ("RSI Calculator", test_rsi_calculator),
        ("Divergence Detector", test_divergence_detector),
        ("Scanner", test_scanner),
        ("Database", test_database),
        ("Telegram Bot", test_telegram)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print("="*60)
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Bot is ready to run!")
        print("\nNext steps:")
        print("1. Run the bot: python main.py")
        print("2. Send /start to your bot in Telegram")
        print("3. Use /quick to test scanning")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Check .env file has correct values")
        print("- Verify internet connection")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
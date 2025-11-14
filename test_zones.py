"""
Test script to diagnose /zones command issues
Save as: test_zones.py
Run: python test_zones.py
"""

import sys
import os

print("=" * 70)
print("TESTING RSI ZONES FEATURE")
print("=" * 70)

# Test 1: Check if file exists
print("\n[1/6] Checking if rsi_zones_scanner.py exists...")
file_path = os.path.join('analyzer', 'rsi_zones_scanner.py')
if os.path.exists(file_path):
    print(f"✅ File exists: {file_path}")
else:
    print(f"❌ File NOT found: {file_path}")
    print("   FIX: Create analyzer/rsi_zones_scanner.py")
    sys.exit(1)

# Test 2: Check if file has correct content
print("\n[2/6] Checking file content...")
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'class RSIZoneScanner' in content:
            print("✅ RSIZoneScanner class found")
        else:
            print("❌ RSIZoneScanner class NOT found in file")
            print("   FIX: Make sure file has correct content")
            sys.exit(1)
except Exception as e:
    print(f"❌ Cannot read file: {e}")
    sys.exit(1)

# Test 3: Try to import
print("\n[3/6] Testing import...")
try:
    from analyzer.rsi_zones_scanner import RSIZoneScanner
    print("✅ Import successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("   FIX: Check file syntax and dependencies")
    sys.exit(1)

# Test 4: Initialize scanner
print("\n[4/6] Testing scanner initialization...")
try:
    scanner = RSIZoneScanner()
    print("✅ Scanner initialized")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Check telegram bot
print("\n[5/6] Checking Telegram bot integration...")
try:
    from bot.telegram_bot import TelegramBot
    
    # Create bot instance
    bot = TelegramBot()
    
    # Check zones_command
    if hasattr(bot, 'zones_command'):
        print("✅ zones_command method exists")
    else:
        print("❌ zones_command method NOT found")
        print("   FIX: Add zones_command to telegram_bot.py")
        sys.exit(1)
    
    # Check zone_scanner
    if hasattr(bot, 'zone_scanner'):
        print("✅ zone_scanner initialized in bot")
    else:
        print("❌ zone_scanner NOT initialized")
        print("   FIX: Add self.zone_scanner = RSIZoneScanner() to __init__")
        sys.exit(1)
    
    # Check command handler registration
    print("   Checking command handler...")
    # We can't easily test this without starting the bot
    # But if we got here, the method exists
    
except Exception as e:
    print(f"❌ Telegram bot check failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Quick functional test
print("\n[6/6] Testing scanner functionality...")
try:
    import asyncio
    
    async def quick_test():
        # Test single coin scan
        result = await scanner.scan_single_coin('BTC/USDT', '15m')
        if result:
            print(f"✅ Scanned BTC/USDT successfully")
            print(f"   RSI: {result['rsi']}")
            print(f"   Zone: {result['zone']}")
            print(f"   Trend: {result['trend']}")
            return True
        else:
            print("⚠️ Scan returned None (data issue, not code issue)")
            return False
    
    asyncio.run(quick_test())
    
except Exception as e:
    print(f"❌ Functional test failed: {e}")
    import traceback
    traceback.print_exc()

# Final summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print("""
✅ If all tests passed:
   1. Stop your bot (Ctrl+C)
   2. Restart: python main.py
   3. Wait for "Bot is fully operational"
   4. Try /zones in Telegram
   5. Check console for any errors

❌ If any test failed:
   1. Fix the issue shown above
   2. Run this test again
   3. All must pass before /zones will work

💡 Common issues:
   - File in wrong location
   - Bot not restarted after adding file
   - Missing imports in telegram_bot.py
   - Syntax errors in code
""")

print("\nTo test manually in Telegram:")
print("1. Make sure bot is running")
print("2. Type: /zones")
print("3. Check console output for errors")
print("\nIf /zones does nothing, check:")
print("- Bot console for errors")
print("- Telegram bot has /zones in command list")
print("- setup_handlers() registers zones_command")
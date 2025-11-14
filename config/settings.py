"""
Configuration settings for RSI Divergence Bot
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Exchange Configuration
EXCHANGE = 'binance'  # You can change to 'bybit', 'kucoin', etc.

# RSI Settings
RSI_PERIOD = 14  # Standard RSI period
RSI_OVERBOUGHT = 65  # Bearish divergence zone
RSI_OVERSOLD = 35  # Bullish divergence zone

# Divergence Detection Settings
PIVOT_WINDOW = 3  # Number of candles on each side to confirm pivot
MINIMUM_PIVOT_SEPARATION = 4  # Minimum candles between pivots
MINIMUM_PRICE_CHANGE = 0.7  # Minimum price change % for valid divergence
MINIMUM_RSI_CHANGE = 2  # Minimum RSI change for valid divergence

# Timeframes to Scan
TIMEFRAMES = ['15m', '30m'] # Scan multiple timeframes for better accuracy

# Scanning Settings
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', 120))  # 15 minutes default
MAX_COINS_PER_SCAN = 100  # Maximum coins to scan in one cycle

# Volume Settings (for volume confirmation)
VOLUME_THRESHOLD = 1.0  # Current volume should be 1.2x average volume

# Alert Settings
SEND_BULLISH_ALERTS = True
SEND_BEARISH_ALERTS = True
ALERT_COOLDOWN = 3600  # Don't send same alert within 1 hour (in seconds)

# Database Settings
DATABASE_PATH = 'database/divergences.db'

# Logging Settings
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = 'logs/bot.log'

# Validation
def validate_config():
    """Validate that all required settings are present"""
    errors = []
    
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN not found in .env file")
    
    if not TELEGRAM_CHAT_ID:
        errors.append("TELEGRAM_CHAT_ID not found in .env file")
    
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("✅ Configuration validated successfully")
    return True

if __name__ == "__main__":
    validate_config()

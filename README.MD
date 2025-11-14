# RSI Divergence Telegram Bot

A Telegram bot that automatically detects RSI divergences in cryptocurrency markets and sends real-time alerts.

## Features
- ✅ Real-time RSI divergence detection
- ✅ Multi-timeframe analysis (1h, 4h, 1d)
- ✅ Scans 100+ cryptocurrencies
- ✅ Telegram alerts with detailed information
- ✅ Volume confirmation
- ✅ False signal filtering

## Setup Instructions

1. Install Python 3.8+
2. Clone this repository
3. Install dependencies: `pip install -r requirements.txt`
4. Configure `.env` file with your Telegram bot token
5. Run: `python main.py`

## Bot Commands
- `/start` - Start the bot
- `/scan` - Manual scan for divergences
- `/status` - Check bot status
- `/coins` - List monitored coins
- `/help` - Show help message

## Accuracy
Expected accuracy: 75-85% with all filters enabled

## License
MIT
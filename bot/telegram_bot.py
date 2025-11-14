"""
Telegram Bot for RSI Divergence Alerts + RSI Zones Scanner
FIXED: Now properly receives Telegram commands
"""

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from analyzer.data_fetcher import DataFetcher
from analyzer.rsi_calculator import RSICalculator
from analyzer.divergence_detector import HumanLikeDivergenceDetector
from analyzer.rsi_zones_scanner import RSIZoneScanner
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from config.coin_list import get_coins_by_category, DEFAULT_WATCHLIST, get_coin_count
from datetime import datetime
import asyncio

class TelegramBot:
    """Telegram bot with divergence detection + RSI zone scanning"""
    
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Initialize components
        self.fetcher = DataFetcher()
        self.rsi_calc = RSICalculator()
        
        # Divergence detector
        # self.detector = ImprovedDivergenceDetector(
        #     swing_window=2,
        #     rsi_bull_threshold=55,
        #     rsi_bear_threshold=45,
        #     min_price_move_pct=0.3,
        #     volume_multiplier=0.6,
        #     use_ema_filter=False,
        #     divergence_tolerance=0.3
        # )
        self.detector = HumanLikeDivergenceDetector(
            min_peak_prominence=2.0,      # 2% minimum
            min_rsi_divergence=5.0,       # 5 RSI points minimum
            lookback_candles=50,
            require_confirmation=True,     # CRITICAL
            min_time_between_peaks=5
        ) 
        
        # RSI Zone Scanner
        self.zone_scanner = RSIZoneScanner(
            extreme_oversold=25,
            oversold=30,
            neutral_low=40,
            neutral_high=60,
            overbought=70,
            extreme_overbought=75
        )
        
        self.app = None
        self.is_running = False
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        print(f"✅ /start command received from {update.effective_user.first_name}")
        
        welcome_message = """
🤖 <b>Enhanced RSI Bot Started!</b>

I monitor cryptocurrency markets and alert you about:
• RSI Divergences
• RSI Support/Resistance Reversals
• Overbought/Oversold Zones

<b>📊 Features:</b>
• Scan 100+ cryptocurrencies
• Multi-timeframe analysis (15m, 30m)
• Real-time divergence alerts
• RSI zone monitoring

<b>🎯 Commands:</b>
/scan - Manual scan for divergences
/quick - Quick scan top 10 coins
/zones - RSI Overbought/Oversold zones
/status - Bot status & statistics
/coins - View monitored coins
/help - Show help message

<b>⚙️ Current Settings:</b>
• Timeframes: 15m, 30m
• Auto-scan: Every 15 minutes
• Detection: 3 methods

Ready to find opportunities! 🚀
"""
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.HTML)
    
    async def scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /scan command - full divergence scan"""
        print(f"✅ /scan command received from {update.effective_user.first_name}")
        await update.message.reply_text("🔍 Starting full scan... This may take 2-3 minutes.")
        
        try:
            found_divergences = []
            
            # Scan top 20 coins on 15m
            for i, symbol in enumerate(DEFAULT_WATCHLIST[:20], 1):
                try:
                    df = self.fetcher.fetch_ohlcv(symbol, '15m', limit=200)
                    if df is None or len(df) < 50:
                        continue
                    
                    df = self.rsi_calc.calculate_rsi(df)
                    divs = self.detector.detect_all_divergences(df)
                    
                    if divs:
                        for div in divs:
                            if div['strength'] >= 15:
                                div['symbol'] = symbol
                                div['timeframe'] = '15m'
                                found_divergences.append(div)
                    
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error scanning {symbol}: {e}")
                    continue
            
            if found_divergences:
                found_divergences.sort(key=lambda x: x['strength'], reverse=True)
                
                summary = f"✅ <b>Scan Complete!</b>\n\nFound {len(found_divergences)} divergence(s):\n\n"
                
                for div in found_divergences:
                    emoji = "🟢" if div['type'] == 'BULLISH' else "🔴"
                    summary += f"{emoji} {div['symbol']} - {div['strength_label']} ({div['strength']})\n"
                
                await update.message.reply_text(summary, parse_mode=ParseMode.HTML)
                
                # Send detailed alerts (max 5)
                for div in found_divergences[:5]:
                    alert = self.detector.format_divergence_alert(
                        div, div['symbol'], div['timeframe']
                    )
                    await update.message.reply_text(f"<pre>{alert}</pre>", parse_mode=ParseMode.HTML)
                    await asyncio.sleep(1)
                
                if len(found_divergences) > 5:
                    await update.message.reply_text(
                        f"📊 Showing top 5 strongest signals. "
                        f"{len(found_divergences) - 5} more available."
                    )
            else:
                await update.message.reply_text(
                    "No divergences detected at this time.\n\n"
                    "Try /zones to see RSI overbought/oversold coins!"
                )
        
        except Exception as e:
            await update.message.reply_text(f"❌ Error during scan: {str(e)}")
    
    async def quick_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quick command - quick scan top coins"""
        print(f"✅ /quick command received from {update.effective_user.first_name}")
        await update.message.reply_text("⚡ Quick scanning top 10 coins...")
        
        try:
            top_coins = DEFAULT_WATCHLIST[:10]
            found_divergences = []
            
            for symbol in top_coins:
                try:
                    df = self.fetcher.fetch_ohlcv(symbol, '15m', limit=200)
                    if df is None or len(df) < 50:
                        continue
                    
                    df = self.rsi_calc.calculate_rsi(df)
                    divs = self.detector.detect_all_divergences(df)
                    
                    if divs:
                        for div in divs:
                            if div['strength'] >= 20:
                                div['symbol'] = symbol
                                div['timeframe'] = '15m'
                                found_divergences.append(div)
                    
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    continue
            
            if found_divergences:
                found_divergences.sort(key=lambda x: x['strength'], reverse=True)
                
                for div in found_divergences[:3]:
                    alert = self.detector.format_divergence_alert(
                        div, div['symbol'], div['timeframe']
                    )
                    await update.message.reply_text(f"<pre>{alert}</pre>", parse_mode=ParseMode.HTML)
                    await asyncio.sleep(1)
            else:
                await update.message.reply_text("No strong divergences in top 10 coins.")
        
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def zones_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /zones command - show RSI overbought/oversold zones for all timeframes"""
        print(f"✅ /zones command received from {update.effective_user.first_name}")
        
        await update.message.reply_text(
            "🔍 Scanning RSI zones for 15m, 30m, 1h, and 4h timeframes...\n"
            "This will take 2-3 minutes. Please wait..."
        )
        
        try:
            # Scan all 4 timeframes
            results = await self.zone_scanner.scan_all_coins(
                timeframes=['15m', '30m', '1h', '4h'],
                coins=DEFAULT_WATCHLIST
            )
            
            # Send results for each timeframe
            for tf in ['15m', '30m', '1h', '4h']:
                categorized = self.zone_scanner.categorize_results(results[tf])
                message = self.zone_scanner.format_telegram_message(tf, categorized)
                
                if message.strip():
                    await update.message.reply_text(message, parse_mode=ParseMode.HTML)
                else:
                    await update.message.reply_text(f"📊 {tf}: No extreme RSI zones detected")
                
                await asyncio.sleep(1)  # Prevent rate limiting
            
            print(f"✅ /zones scan completed for all timeframes")
            
        except Exception as e:
            error_msg = f"❌ Error scanning zones: {str(e)}"
            print(error_msg)
            await update.message.reply_text(error_msg)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        print(f"✅ /status command received from {update.effective_user.first_name}")
        
        status_message = f"""
📊 <b>Bot Status</b>

<b>🤖 Status:</b> {'🟢 Running' if self.is_running else '🔴 Stopped'}
<b>⏰ Current Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>⚙️ Configuration:</b>
• Monitored Coins: {get_coin_count()}
• Timeframes: 15m, 30m
• Scan Interval: 15 minutes
• Detection: Enhanced (3 methods)

<b>🎯 Detection Methods:</b>
1. Regular Divergences
2. RSI Support/Resistance
3. RSI Zone Monitoring

<b>📈 Features:</b>
• Divergence alerts
• RSI reversal signals
• Zone scanning (/zones)
• Quality filters enabled

Bot is operational! ✅
"""
        await update.message.reply_text(status_message, parse_mode=ParseMode.HTML)
    
    async def coins_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /coins command"""
        print(f"✅ /coins command received from {update.effective_user.first_name}")
        
        top_coins = get_coins_by_category('top')
        
        coins_message = f"""
📋 <b>Monitored Cryptocurrencies</b>

<b>🏆 Top 10 Coins:</b>
{chr(10).join([f'• {coin}' for coin in top_coins[:10]])}

<b>📊 Total Coins:</b> {get_coin_count()}

<b>Categories:</b>
• Top Market Cap
• Mid-cap Altcoins
• DeFi Tokens
• Layer 1 Blockchains
• Meme Coins

<b>💡 Commands:</b>
/scan - Scan all for divergences
/zones - Check RSI zones
"""
        await update.message.reply_text(coins_message, parse_mode=ParseMode.HTML)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        print(f"✅ /help command received from {update.effective_user.first_name}")
        
        help_message = """
📖 <b>Help - Enhanced RSI Bot</b>

<b>🎯 Commands:</b>

<b>/start</b> - Start the bot and see welcome message
<b>/scan</b> - Perform full scan of monitored coins
<b>/quick</b> - Quick scan of top 10 coins (faster)
<b>/zones</b> - Show RSI overbought/oversold zones
<b>/status</b> - Check bot status and configuration
<b>/coins</b> - View list of monitored coins
<b>/help</b> - Show this help message

<b>📊 RSI Zones Explained:</b>

<b>🟣 Extreme Oversold (RSI < 25)</b>
• Strong buy opportunity
• Price heavily oversold

<b>🔵 Oversold (RSI 25-30)</b>
• Buy zone
• Potential reversal coming

<b>🟢 Approaching Oversold (RSI 30-40)</b>
• Watch for entry
• Momentum weakening

<b>🟡 Approaching Overbought (RSI 60-70)</b>
• Watch for exit
• Momentum peaking

<b>🟠 Overbought (RSI 70-75)</b>
• Sell zone
• Potential reversal down

<b>🔴 Extreme Overbought (RSI > 75)</b>
• Strong sell opportunity
• Price heavily overbought

<b>📈 Trend Indicators:</b>
📈 = RSI Rising (bullish momentum)
📉 = RSI Falling (bearish momentum)
➡️ = RSI Stable (neutral)

<b>💡 Trading Tips:</b>
• Use zones + divergences together
• RSI zones show current conditions
• Divergences predict reversals
• Always use risk management

<b>⚠️ Disclaimer:</b>
This bot provides technical analysis, not financial advice. Always do your own research and trade responsibly.
"""
        await update.message.reply_text(help_message, parse_mode=ParseMode.HTML)
    
    async def send_alert(self, divergence):
        """Send divergence alert to user"""
        try:
            alert = self.detector.format_divergence_alert(
                divergence,
                divergence.get('symbol', 'UNKNOWN'),
                divergence.get('timeframe', '15m')
            )
            
            await self.app.bot.send_message(
                chat_id=self.chat_id,
                text=f"<pre>{alert}</pre>",
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            print(f"Error sending alert: {e}")
    
    async def send_message(self, message):
        """Send a text message to user"""
        try:
            await self.app.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def setup_handlers(self):
        """Setup command handlers"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("scan", self.scan_command))
        self.app.add_handler(CommandHandler("quick", self.quick_command))
        self.app.add_handler(CommandHandler("zones", self.zones_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("coins", self.coins_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        print("✓ Command handlers registered")
    
    async def initialize(self):
        """Initialize the bot application and START POLLING"""
        try:
            print("Initializing Telegram bot...")
            
            # Build application
            self.app = Application.builder().token(self.token).build()
            
            # Setup command handlers
            self.setup_handlers()
            
            # Initialize and start
            await self.app.initialize()
            await self.app.start()
            
            # ✅ CRITICAL FIX: START POLLING TO RECEIVE MESSAGES
            print("Starting Telegram message polling...")
            await self.app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                poll_interval=1.0
            )
            
            self.is_running = True
            print("✓ Bot initialized and receiving Telegram messages")
            
        except Exception as e:
            print(f"❌ Error initializing bot: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def shutdown(self):
        """Shutdown the bot gracefully"""
        if self.app and self.app.updater:
            print("Stopping Telegram polling...")
            await self.app.updater.stop()
        
        if self.app:
            self.is_running = False
            await self.app.stop()
            await self.app.shutdown()
        
        print("✓ Bot shutdown complete")
    
    def run(self):
        """Run the bot (blocking) - for standalone testing"""
        print("=" * 60)
        print("Starting Enhanced Telegram Bot...")
        print("=" * 60)
        
        self.app = Application.builder().token(self.token).build()
        self.setup_handlers()
        
        self.is_running = True
        print("✓ Bot is running! Press Ctrl+C to stop.")
        print("✓ Send /start to test commands")
        
        # This will start polling automatically
        self.app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )


# Test the bot
if __name__ == "__main__":
    print("=" * 60)
    print("Testing Enhanced Telegram Bot with RSI Zones")
    print("=" * 60)
    
    try:
        bot = TelegramBot()
        print("\n✓ Bot created successfully")
        print(f"✓ Token configured: {bot.token[:10]}...")
        print(f"✓ Chat ID configured: {bot.chat_id}")
        print("✓ RSI Zone Scanner loaded")
        
        print("\nStarting bot... Send commands in Telegram to test!")
        print("Commands: /start, /scan, /quick, /zones, /status, /help")
        print("\nPress Ctrl+C to stop\n")
        
        bot.run()
        
    except KeyboardInterrupt:
        print("\n\n✓ Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
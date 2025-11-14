"""
Test Telegram Bot Connection and Commands
This will show if your bot is actually receiving messages
"""

import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

print("=" * 70)
print("TESTING TELEGRAM BOT CONNECTION")
print("=" * 70)

# Test 1: Check credentials
print("\n[1/4] Checking credentials...")
if not TELEGRAM_BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN is empty!")
    print("   Check your .env file")
    exit(1)
else:
    print(f"✅ Bot token found: {TELEGRAM_BOT_TOKEN[:10]}...{TELEGRAM_BOT_TOKEN[-5:]}")

if not TELEGRAM_CHAT_ID:
    print("❌ TELEGRAM_CHAT_ID is empty!")
    exit(1)
else:
    print(f"✅ Chat ID found: {TELEGRAM_CHAT_ID}")

# Test 2: Create simple bot
print("\n[2/4] Creating test bot...")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple test command"""
    print(f"✅ COMMAND RECEIVED from {update.effective_user.username}")
    await update.message.reply_text("✅ Bot is working! Commands are being received.")

async def echo_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo any message"""
    print(f"📩 Message received: {update.message.text}")
    await update.message.reply_text(f"Echo: {update.message.text}")

async def main():
    print("Creating application...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add test command
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("ping", test_command))
    
    # Add message handler to echo everything
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_all))
    
    print("✅ Test bot created")
    print("\n[3/4] Starting bot...")
    print("\n" + "=" * 70)
    print("BOT IS NOW RUNNING")
    print("=" * 70)
    print("\n💡 Try these in Telegram:")
    print("   /test   - Should respond with 'Bot is working!'")
    print("   /ping   - Should respond with 'Bot is working!'")
    print("   hello   - Should echo back 'Echo: hello'")
    print("\n📱 Send a message to your bot now...")
    print("   Press Ctrl+C to stop\n")
    
    # Initialize and start
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping bot...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Bot stopped")
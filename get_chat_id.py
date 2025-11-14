from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

load_dotenv()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"Your Chat ID is: {chat_id}\n\n"
        f"Add this to your .env file:\n"
        f"TELEGRAM_CHAT_ID={chat_id}"
    )
    print(f"Chat ID: {chat_id}")

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env file")
        return
    
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Bot is running. Send /start to your bot in Telegram...")
    app.run_polling()

if __name__ == '__main__':
    main()
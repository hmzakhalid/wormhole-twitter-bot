import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

async def start():
    global app
    await app.bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text="Testing...", parse_mode="MarkdownV2")

if __name__ == '__main__':
    asyncio.run(start())
    # application = ApplicationBuilder().token('6096709699:AAGgO4_RlEBsXhs9VdWcMQBQyBXihHQ-_NM').build()
    
    # start_handler = CommandHandler('start', start)
    # application.add_handler(start_handler)
    
    # application.run_polling()
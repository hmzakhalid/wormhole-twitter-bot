import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes
from twscrape import API, gather
from twscrape.logger import set_log_level
from twscrape.models import Tweet
from telegram.helpers import escape_markdown
import time

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

async def post_to_telegram():
    global app

    api = API("accounts.db") 
    tweet = (await gather(api.user_tweets("1417845872436547587", limit=1)))[1]
    # Check if it's not a retweet or reply
    if tweet.retweetedTweet is None and tweet.inReplyToTweetId is None:
        # Create the pretty message
        msg = f"{tweet.user.username} (@{tweet.user.username}) posted:\n{tweet.rawContent}\n\n🔗 [Twitter Link]({tweet.url})"
        msg = escape_markdown(msg, version=2)
        try:
            # Handle media
            if tweet.media:
                if tweet.media.photos:
                    for photo in tweet.media.photos:
                        await app.bot.send_photo(chat_id=TELEGRAM_CHANNEL_ID, photo=photo.url, caption=msg)
                        msg = None  # Ensure caption is only added once
                elif tweet.media.videos:
                    video = tweet.media.videos[0].variants[0] if tweet.media.videos else None
                    if video:
                        await app.bot.send_video(chat_id=TELEGRAM_CHANNEL_ID, video=video.url, caption=msg)
                        msg = None
                elif tweet.media.animated:
                    animated = tweet.media.animated[0] if tweet.media.animated else None
                    if animated:
                        await app.bot.send_animation(chat_id=TELEGRAM_CHANNEL_ID, animation=animated.videoUrl, caption=msg)
                        msg = None

            # Send text if there was no media or if there was additional text content
            if msg:
                await app.bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=msg, parse_mode="MarkdownV2")
        except Exception as e:
            print(f"Error while posting to Telegram: {e}")
    else:
        print("Tweet is a reply or retweet, ignoring.")


async def main():
    global app
    set_log_level("DEBUG")  # set log level to debug to see more info
    app.job_queue.run_repeating(post_to_telegram, interval=60, first=0)

if __name__ == "__main__":
    asyncio.run(main())
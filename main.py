import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from twscrape import API, gather
from twscrape.logger import set_log_level
from telegram.helpers import escape_markdown
import time

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
api = API("accounts.db") 
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
job_queue = app.job_queue

async def post_to_telegram(app):
    global api
    print(time.strftime("%H:%M:%S", time.localtime()), "Checking for new tweets...")

    tweet = (await gather(api.user_tweets(TWITTER_USERNAME, limit=1)))[1]
    # Check if it's not a retweet or reply
    if (tweet.retweetedTweet is None and tweet.inReplyToTweetId is None and tweet.inReplyToUser is None and tweet.quotedTweet is None):
        print(time.strftime("%H:%M:%S", time.localtime()), "New tweet found, posting to Telegram...")
        
        # Create the pretty message
        content = tweet.rawContent
        # Split the content and remove the last word
        content = content.split(" ")
        tweet_link = content.pop()
        # Join the content back together
        content = " ".join(content)

        # Escape only the content part
        escaped_content = escape_markdown(content, version=1)

        msg = f"{escaped_content}\n\n🔗 [Twitter Link]({tweet_link})"

        print(time.strftime("%H:%M:%S", time.localtime()), "Tweet content:\n", msg, "\n\n")
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
                await app.bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Error while posting to Telegram: {e}")
    else:
        print("Tweet is a reply or retweet, ignoring.")

set_log_level("DEBUG")  # set log level to debug to see more info
job_queue.run_repeating(post_to_telegram, interval=60)
app.run_polling()

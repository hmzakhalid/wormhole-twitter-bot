import os
import logging
import sqlite3
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from twscrape import API, gather
from twscrape.logger import set_log_level
from telegram.helpers import escape_markdown

# Set up logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
api = API("accounts.db") 

# SQLite setup
conn = sqlite3.connect('tweets.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS posted_tweets 
    (tweet_id TEXT PRIMARY KEY)
''')
conn.commit()

def is_tweet_posted(tweet_id):
    c.execute("SELECT tweet_id FROM posted_tweets WHERE tweet_id=?", (tweet_id,))
    return c.fetchone() is not None

def mark_tweet_as_posted(tweet_id):
    c.execute("INSERT INTO posted_tweets (tweet_id) VALUES (?)", (tweet_id,))
    conn.commit()

async def post_to_telegram(app):
    global api
    # Get the latest 2 tweets
    tweet = (await gather(api.user_tweets(TWITTER_USERNAME, limit=1)))[0]

    if is_tweet_posted(tweet.id_str):
        return

    if (tweet.retweetedTweet is None and tweet.inReplyToTweetId is None 
        and tweet.inReplyToUser is None and tweet.quotedTweet is None):

        if tweet.links and tweet.links[0].tcourl:
            tweet_link = tweet.links[0].tcourl
        else:
            tweet_link = tweet.url

        content = tweet.rawContent.replace(tweet_link, "").strip()
        escaped_content = escape_markdown(content, version=1)
        msg = f"{escaped_content}\n\n🔗 [Twitter Link]({tweet_link})"

        try:
            if tweet.media:
                if tweet.media.photos:
                    for photo in tweet.media.photos:
                        await app.bot.send_photo(chat_id=TELEGRAM_CHANNEL_ID, photo=photo.url, caption=msg)
                        msg = None
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

            if msg:
                await app.bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=msg, parse_mode="Markdown")

            mark_tweet_as_posted(tweet.id_str)

        except Exception as e:
            logger.error(f"Error while posting to Telegram: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    job_queue = app.job_queue
    set_log_level("ERROR")  # set log level to error to minimize logging from twscrape
    job_queue.run_repeating(post_to_telegram, interval=60)
    app.run_polling()

if __name__ == "__main__":
    main()

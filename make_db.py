import os
import asyncio
from dotenv import load_dotenv
from twscrape import API

load_dotenv()

SCREENNAME = os.getenv("SCREENNAME")
PASSWORD = os.getenv("PASSWORD")
EMAIL = os.getenv("EMAIL")

async def main():
    api = API()  # or API("path-to.db") - default is `accounts.db`

    await api.pool.add_account(SCREENNAME, PASSWORD, EMAIL, PASSWORD)
    await api.pool.login_all()

if __name__ == "__main__":
    asyncio.run(main())
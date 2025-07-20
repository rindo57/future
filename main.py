from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
from handlers import register_handlers

app = Client("anime_search_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Register all handlers
register_handlers(app)

if __name__ == "__main__":
    print("Bot started...")
    app.run()

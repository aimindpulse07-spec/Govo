import os
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, idle
from pyrogram.types import BotCommand

# IMPORT SETTINGS FROM CONFIG
from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URL, LOG_CHANNEL_ID

app = Client(
    "baka_master", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins") 
)

# ---------------- DATABASE CONNECTION ---------------- #
if not MONGO_URL:
    print("❌ CRITICAL: MONGO_URL MISSING. Bot cannot start.")
    exit()

mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo.baka_bot

# --- HELPER FUNCTIONS ---
async def log_deployment():
    print(f"➡️ Deployment Log Logic Started. Target ID: {LOG_CHANNEL_ID}")
    
    if LOG_CHANNEL_ID and LOG_CHANNEL_ID != 0:
        try:
            # 1. Force fetch the chat to "meet" the channel (Fixes PeerInvalid)
            try:
                chat = await app.get_chat(LOG_CHANNEL_ID)
                print(f"✅ Found Log Channel: '{chat.title}' (ID: {chat.id})")
            except Exception as e:
                print(f"⚠️ Warning: Could not resolve Log Channel. Error: {e}")
                print("   -> Attempting to send message anyway...")

            # 2. Send the message
            await app.send_message(
                LOG_CHANNEL_ID, 
                f"✅ **Bot Restarted Successfully**\n"
                f"📅 `{datetime.now()}`\n"
                f"🤖 **Version:** v7.0 (Stable)",
                disable_web_page_preview=True
            )
            print("✅ Deployment Log Sent to Telegram!")
            
        except Exception as e:
            # THIS PRINT IS CRITICAL FOR DEBUGGING
            print(f"❌ FAILED TO SEND LOG. Reason: {e}")
            print("   -> Check: Is Bot Admin? Is ID correct? Does ID start with -100?")
    else:
        print("ℹ️ Log Channel ID is 0 or Missing in Config. Skipping.")

# ---------------- STARTUP LOGIC ---------------- #

async def main():
    print("➡️ Bot Client Starting...")
    
    # 1. Start the Bot Client
    try:
        await app.start()
        print("✅ Bot Client Connected to Telegram!")
    except Exception as e:
        print(f"❌ Failed to start Bot Client: {e}")
        return
    
    # 2. Send Deployment Log
    await log_deployment()
    
    # 3. Set Bot Commands (Full Menu)
    commands = [
        ("start", "Talk to Meow"), 
        ("help", "Show admin commands"),
        ]
    try:
        await app.set_bot_commands([BotCommand(c, d) for c, d in commands])
        print("✅ Bot Commands Set Successfully.")
    except Exception as e:
        print(f"⚠️ Failed to set commands: {e}")

    print("🤖 Bot is Idle and Running!")
    
    # 4. Keep the bot running
    await idle()
    
    # 5. Stop the bot gracefully
    await app.stop()

if __name__ == "__main__":
    app.run(main())

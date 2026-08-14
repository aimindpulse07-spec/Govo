import time
import os
import sys
import asyncio
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient
# IMPORT CONFIG VARIABLES
from config import MONGO_URL, OWNER_ID, HEROKU_API_KEY, HEROKU_APP_NAME

# --- DATABASE CONNECTION ---
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo.baka_bot
users_col = db.users

# --- HELPER: CHECK OWNER ---
async def check_owner(message: Message):
    return message.from_user.id == OWNER_ID

# ---------------- OWNER MENU ---------------- #

@Client.on_message(filters.command("sudo") & filters.private)
async def sudo_menu(client: Client, message: Message):
    if not await check_owner(message): return
    
    txt = (
        "👑 **Owner / Sudo Dashboard**\n\n"
        "📊 **Stats:**\n"
        "• /status - Check System Health & Ping\n"
        "• /stats - Check Total Users & DB Size\n\n"
        "📢 **Broadcast:**\n"
        "• /broadcast [reply/text] - Send msg to ALL users\n\n"
        "💎 **Premium Management:**\n"
        "• /makepremium [id] - Give Premium\n"
        "• /removepremium [id] - Remove Premium\n"
        "• /premiumlist - List all Premium Users\n\n"
        "⚙️ **System:**\n"
        "• /restart - Restart the Bot\n"
        "• /logs - Get Heroku Logs"
    )
    await message.reply_text(txt)

# ---------------- SYSTEM STATUS & STATS ---------------- #

@Client.on_message(filters.command("status"))
async def status_cmd(client: Client, message: Message):
    # This command is usually public to check if bot is alive
    start = time.time()
    msg = await message.reply_text("🔄 Checking System...")
    end = time.time()
    ping = int((end - start) * 1000)
    
    await msg.edit_text(
        f"🤖 **System Status**\n\n"
        f"📶 **Ping:** `{ping}ms`\n"
        f"✅ **Service:** Online\n"
        f"🧠 **AI Engine:** Dual-Core (GitHub + Pollinations)\n"
        f"👑 **Owner ID:** `{OWNER_ID}`"
    )

@Client.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats_cmd(client: Client, message: Message):
    msg = await message.reply_text("🔄 Counting Users...")
    try:
        count = await users_col.count_documents({})
        prem_count = await users_col.count_documents({"premium": True})
        
        await msg.edit_text(
            f"📊 **Bot Statistics**\n\n"
            f"👤 **Total Users:** `{count}`\n"
            f"💎 **Premium Users:** `{prem_count}`\n"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Error fetching stats: {e}")

# ---------------- BROADCAST ---------------- #

@Client.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client: Client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("⚠️ Usage: Reply to a message or use `/broadcast Hello`")
    
    msg = await message.reply_text("📣 **Broadcasting started...** (This may take a while)")
    
    # Fetch all users
    users = users_col.find({})
    total = await users_col.count_documents({})
    sent = 0
    failed = 0
    
    async for user in users:
        try:
            if message.reply_to_message:
                await message.reply_to_message.copy(user['_id'])
            else:
                await client.send_message(user['_id'], message.text.split(None, 1)[1])
            sent += 1
            # Small delay to prevent floodwaits
            if sent % 20 == 0:
                await asyncio.sleep(1)
        except:
            failed += 1
            
    await msg.edit_text(
        f"✅ **Broadcast Complete**\n\n"
        f"👥 Total Users: `{total}`\n"
        f"✅ Successfully Sent: `{sent}`\n"
        f"❌ Failed (Blocked/Deleted): `{failed}`"
    )

# ---------------- PREMIUM MANAGEMENT ---------------- #

@Client.on_message(filters.command("makepremium") & filters.user(OWNER_ID))
async def make_premium(client: Client, message: Message):
    try:
        user_id = int(message.command[1])
        await users_col.update_one({"_id": user_id}, {"$set": {"premium": True}})
        await message.reply_text(f"✅ User `{user_id}` is now **Premium**! 💎")
        
        # Try to notify the user
        try: await client.send_message(user_id, "💎 **Congratulations!** You have been upgraded to Premium!")
        except: pass
    except:
        await message.reply_text("⚠️ Usage: `/makepremium 12345678`")

@Client.on_message(filters.command("removepremium") & filters.user(OWNER_ID))
async def remove_premium(client: Client, message: Message):
    try:
        user_id = int(message.command[1])
        await users_col.update_one({"_id": user_id}, {"$set": {"premium": False}})
        await message.reply_text(f"🚫 User `{user_id}` is no longer Premium.")
    except:
        await message.reply_text("⚠️ Usage: `/removepremium 12345678`")

@Client.on_message(filters.command("premiumlist") & filters.user(OWNER_ID))
async def premium_list(client: Client, message: Message):
    users = users_col.find({"premium": True})
    txt = "💎 **Premium Users:**\n\n"
    count = 0
    async for u in users:
        count += 1
        txt += f"{count}. `{u['_id']}` - {u.get('name', 'User')}\n"
    
    if count == 0:
        await message.reply_text("🤷‍♂️ No premium users found.")
    else:
        await message.reply_text(txt)

# ---------------- SYSTEM COMMANDS ---------------- #

@Client.on_message(filters.command("restart") & filters.user(OWNER_ID))
async def restart_bot(client: Client, message: Message):
    await message.reply_text("🔄 **Bot is restarting...**\n(Check log channel for 'Restart Successful' msg)")
    os.execl(sys.executable, sys.executable, *sys.argv)

@Client.on_message(filters.command("logs") & filters.user(OWNER_ID))
async def get_logs(client: Client, message: Message):
    if not HEROKU_API_KEY or not HEROKU_APP_NAME:
        return await message.reply_text("❌ **Error:** `HEROKU_API_KEY` or `HEROKU_APP_NAME` is missing in ConfigVars.")
    
    msg = await message.reply_text("🔄 **Fetching Heroku Logs...**")
    try:
        headers = {
            "Accept": "application/vnd.heroku+json; version=3",
            "Authorization": f"Bearer {HEROKU_API_KEY}"
        }
        # 1. Create Log Session
        url = f"https://api.heroku.com/apps/{HEROKU_APP_NAME}/log-sessions"
        payload = {"lines": 100, "tail": False}
        r = requests.post(url, headers=headers, json=payload)
        
        if r.status_code != 201:
            return await msg.edit_text(f"❌ **Heroku Error:** {r.text}")
            
        # 2. Fetch Actual Logs
        log_url = r.json()['logplex_url']
        logs = requests.get(log_url).text
        
        # 3. Save and Send
        with open("logs.txt", "w", encoding='utf-8') as f:
            f.write(logs)
            
        await message.reply_document("logs.txt", caption=f"📄 **Heroku Logs** for `{HEROKU_APP_NAME}`")
        os.remove("logs.txt")
        await msg.delete()
        
    except Exception as e:
        await msg.edit_text(f"❌ **Exception:** {e}")

# ---------------- BANALL SUDO MANAGEMENT ---------------- #
# These commands are OWNER-ONLY. Sudo users get mass-command access
# (/banall and /unbanall) without needing to be group administrators.

sudo_col = db.sudo_users

async def _resolve_user_id(client, message):
    """Resolve a Telegram user ID from an argument or replied message."""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    if len(message.command) > 1:
        raw = message.command[1].strip()
        try:
            return int(raw)
        except ValueError:
            try:
                user = await client.get_users(raw.lstrip("@"))
                return user.id
            except Exception:
                return None
    return None


@Client.on_message(filters.command("addsudo") & filters.user(OWNER_ID))
async def add_sudo(client: Client, message: Message):
    user_id = await _resolve_user_id(client, message)
    if not user_id:
        return await message.reply_text(
            "⚠️ Usage: `/addsudo 123456789` or reply to a user's message."
        )
    if user_id == OWNER_ID:
        return await message.reply_text("👑 Owner already has sudo access.")
    await sudo_col.update_one(
        {"_id": int(user_id)},
        {"$set": {"user_id": int(user_id), "added_by": OWNER_ID}},
        upsert=True,
    )
    await message.reply_text(
        f"✅ `{user_id}` ko **Sudo User** bana diya gaya.\n\n"
        "Ab ye user group admin na hote hue bhi `/banall` aur `/unbanall` use kar sakta hai."
    )


@Client.on_message(filters.command("delsudo") & filters.user(OWNER_ID))
async def del_sudo(client: Client, message: Message):
    user_id = await _resolve_user_id(client, message)
    if not user_id:
        return await message.reply_text(
            "⚠️ Usage: `/delsudo 123456789` or reply to a user's message."
        )
    result = await sudo_col.delete_one({"_id": int(user_id)})
    if result.deleted_count:
        await message.reply_text(f"✅ `{user_id}` ka Sudo access remove kar diya gaya.")
    else:
        await message.reply_text(f"ℹ️ `{user_id}` Sudo list me nahi hai.")


@Client.on_message(filters.command("sudolist") & filters.user(OWNER_ID))
async def sudo_list(client: Client, message: Message):
    users = []
    async for doc in sudo_col.find({}):
        users.append(int(doc["_id"]))
    if not users:
        return await message.reply_text("📋 Abhi koi Sudo User nahi hai.")
    text = "👑 **Sudo Users:**\n\n" + "\n".join(
        f"{i}. `{uid}`" for i, uid in enumerate(users, 1)
    )
    await message.reply_text(text)

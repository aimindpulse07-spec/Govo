import time
import random
import asyncio
import requests
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.types import Message
from googletrans import Translator

# IMPORT CONFIG
from config import (
    MONGO_URL, DAILY_BONUS, REVIVE_COST, PROTECT_1D_COST, PROTECT_2D_COST,
    AUTO_REVIVE_HOURS, KILL_LIMIT_DAILY, ROB_LIMIT_DAILY, ROB_MAX_AMOUNT,
    KILL_SPAM_COOLDOWN
)
# IMPORT HELPER TEXTS
from plugins.helper import ECONOMY_TEXT, GAME_OPEN_TEXT, GAME_CLOSE_TEXT

# --- DATABASE CONNECTION ---
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo.baka_bot
users_col = db.users
chats_col = db.chats

# --- TRANSLATOR INIT ---
trans = Translator()

# --- ANIME REACTION GIF API (free, no key needed) ---
REACTION_GIF_API = "https://api.otakugifs.xyz/gif?reaction={}"

def _fetch_reaction_gif_sync(reaction: str):
    """Blocking call, run in a thread. Returns a gif URL or None on failure."""
    try:
        r = requests.get(REACTION_GIF_API.format(reaction), timeout=10)
        r.raise_for_status()
        return r.json().get("url")
    except Exception as e:
        print(f"⚠️ Failed to fetch reaction gif for '{reaction}': {e}")
        return None


# --- ITEM SHOP DATA ---
SHOP_ITEMS = {
    "rose": {"name": "Rose", "emoji": "🌹", "cost": 500},
    "chocolate": {"name": "Chocolate", "emoji": "🍫", "cost": 800},
    "ring": {"name": "Ring", "emoji": "💍", "cost": 2000},
    "teddy": {"name": "Teddy Bear", "emoji": "🧸", "cost": 1500},
    "pizza": {"name": "Pizza", "emoji": "🍕", "cost": 600},
    "box": {"name": "Surprise Box", "emoji": "🎁", "cost": 2500},
    "puppy": {"name": "Puppy", "emoji": "🐶", "cost": 3000},
    "cake": {"name": "Cake", "emoji": "🎂", "cost": 1000},
    "letter": {"name": "Love Letter", "emoji": "💌", "cost": 400},
    "cat": {"name": "Cat", "emoji": "🐱", "cost": 2500},
}

# --- HELPER FUNCTIONS ---

async def get_user(user_id, name="User"):
    user = await users_col.find_one({"_id": user_id})
    now = time.time()
    
    # Create User if not exists
    if not user:
        user = {
            "_id": user_id, 
            "name": name, 
            "balance": 0, 
            "status": "alive",
            "death_time": 0,
            "kills": 0, 
            "premium": False, 
            "last_daily": 0, 
            "protected_until": 0,
            "items": {},
            "name_history": [],
            "kills_today": 0,
            "robs_today": 0,
            "last_limit_reset": now,
            "last_kill_time": 0
        }
        await users_col.insert_one(user)

    # 0. RESET DAILY KILL/ROB LIMITS (every 24h)
    if now - user.get('last_limit_reset', 0) > 86400:
        await users_col.update_one(
            {"_id": user_id},
            {"$set": {"kills_today": 0, "robs_today": 0, "last_limit_reset": now}}
        )
        user['kills_today'] = 0
        user['robs_today'] = 0
        user['last_limit_reset'] = now

    # 1. AUTO-REVIVE LOGIC (config-driven hours)
    if user['status'] == 'dead' and user.get('death_time', 0) > 0:
        if (now - user['death_time']) > (AUTO_REVIVE_HOURS * 3600):
            # Revive with random balance < 200
            new_bal = random.randint(10, 199)
            await users_col.update_one(
                {"_id": user_id}, 
                {"$set": {"status": "alive", "death_time": 0, "balance": new_bal}}
            )
            user['status'] = "alive"
            user['balance'] = new_bal

    # 2. NAME HISTORY TRACKER (For /detail)
    if name != "User" and user.get('name') != name:
        # Add old name to history if changed
        await users_col.update_one(
            {"_id": user_id}, 
            {"$push": {"name_history": user['name']}, "$set": {"name": name}}
        )

    return user

async def update_user(user_id, data):
    await users_col.update_one({"_id": user_id}, {"$set": data})

async def is_admin(message: Message):
    if message.chat.type == ChatType.PRIVATE: return False
    try:
        mem = await message.chat.get_member(message.from_user.id)
        return mem.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except: return False

async def is_game_enabled(chat_id):
    chat = await chats_col.find_one({"_id": chat_id})
    return chat.get("games_enabled", True) if chat else True

# ---------------- MANAGEMENT COMMANDS ---------------- #

@Client.on_message(filters.command("check"))
async def check_premium_cmd(client: Client, message: Message):
    user = await get_user(message.from_user.id, message.from_user.first_name)
    
    if not user.get("premium", False):
        return await message.reply_text(
            "𝙈𝙚𝙤𝙬 😻:\n"
            "❌ This command is only for Premium users."
        )
        
    rem = user.get('protected_until', 0) - time.time()
    prot_status = f"Active ({int(rem/3600)}h left) 🛡️" if rem > 0 else "Inactive ❌"
    
    await message.reply_text(
        f"💎 **Premium Dashboard**\n"
        f"👤 {message.from_user.mention}\n"
        f"🛡️ **Protection:** {prot_status}\n"
        f"✅ **Daily Limit:** $2000"
    )

@Client.on_message(filters.command("open") & filters.group)
async def open_games(client: Client, message: Message):
    if not await is_admin(message):
        return await message.reply_text("❌ You need to be an Admin to use this!")
    await chats_col.update_one({"_id": message.chat.id}, {"$set": {"games_enabled": True}}, upsert=True)
    await message.reply_text(GAME_OPEN_TEXT)

@Client.on_message(filters.command("close") & filters.group)
async def close_games(client: Client, message: Message):
    if not await is_admin(message):
        return await message.reply_text("❌ You need to be an Admin to use this!")
    await chats_col.update_one({"_id": message.chat.id}, {"$set": {"games_enabled": False}}, upsert=True)
    await message.reply_text(GAME_CLOSE_TEXT)

@Client.on_message(filters.command("claim") & filters.group)
async def claim_reward(client: Client, message: Message):
    if not await is_admin(message):
        return await message.reply_text("❌ Only Admins can claim the group reward!")

    chat_id = message.chat.id
    user_id = message.from_user.id
    
    chat_data = await chats_col.find_one({"_id": chat_id})
    if chat_data and chat_data.get("claimed", False):
        return await message.reply_text("❌ This group has already claimed the start reward!")
        
    reward = 5000
    user = await get_user(user_id)
    await update_user(user_id, {"balance": user['balance'] + reward})
    await chats_col.update_one({"_id": chat_id}, {"$set": {"claimed": True}}, upsert=True)
    
    await message.reply_text(f"✅ **Group Reward Claimed!**\n👤 {message.from_user.mention} got ${reward}!")

# ---------------- ECONOMY COMMANDS ---------------- #

@Client.on_message(filters.command("economy"))
async def economy_cmd(client: Client, message: Message):
    await message.reply_text(ECONOMY_TEXT)

@Client.on_message(filters.command("daily"))
async def daily(client: Client, message: Message):
    if not await is_game_enabled(message.chat.id): return
    user = await get_user(message.from_user.id, message.from_user.first_name)
    now = time.time()
    if now - user['last_daily'] < 86400: return await message.reply_text("⏳ Please wait 24 hours!")
    reward = DAILY_BONUS * 2 if user['premium'] else DAILY_BONUS
    await update_user(user['_id'], {"balance": user['balance'] + reward, "last_daily": now})
    await message.reply_text(f"✅ Received ${reward}!")

@Client.on_message(filters.command("bal"))
async def bal(client: Client, message: Message):
    # Logic: Show target balance if reply, else show own balance
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    else:
        target = message.from_user
        
    data = await get_user(target.id, target.first_name)
    
    # Exact Format Requested
    status_icon = "❤️" if data['status'] == 'alive' else "☠️"
    await message.reply_text(
        f"👤 Name: {data['name']}\n"
        f"💰 Balance: ${data['balance']}\n"
        f"{status_icon} Status: {data['status'].title()}"
    )

@Client.on_message(filters.command("rob"))
async def rob(client: Client, message: Message):
    if not await is_game_enabled(message.chat.id): return
    if not message.reply_to_message: return await message.reply_text("Reply to someone!")
    
    robber = await get_user(message.from_user.id)
    victim = await get_user(message.reply_to_message.from_user.id)
    
    # Dead users CAN rob (per request "dead user... only can rob")
    # But victim must be alive or dead? Usually robbing dead people is fine.
    
    if victim['status'] == "dead": return await message.reply_text("They are dead ☠️ (Wait for revive)")
    if time.time() < victim['protected_until']: return await message.reply_text("🛡️ Protected!")

    # Daily rob limit (config-driven)
    if robber.get('robs_today', 0) >= ROB_LIMIT_DAILY:
        return await message.reply_text(f"⚠️ Daily rob limit reached ({ROB_LIMIT_DAILY}/day). Try tomorrow!")

    limit = 100000 if robber['premium'] else 10000
    limit = min(limit, ROB_MAX_AMOUNT)  # hard cap from config
    try: amt = int(message.command[1])
    except: amt = random.randint(100, limit)
    
    if amt > limit: amt = limit
    if victim['balance'] < amt: amt = victim['balance']
    if amt <= 0: return await message.reply_text("They are broke!")
    
    if random.choice([True, False]):
        await update_user(victim['_id'], {"balance": victim['balance'] - amt})
        await update_user(robber['_id'], {"balance": robber['balance'] + amt, "robs_today": robber.get('robs_today', 0) + 1})
        await message.reply_text(f"💸 Stole **${amt}**!")
    else:
        fine = 500
        await update_user(robber['_id'], {"balance": robber['balance'] - fine, "robs_today": robber.get('robs_today', 0) + 1})
        await message.reply_text(f"🚔 Caught! Fined ${fine}.")

@Client.on_message(filters.command("kill"))
async def kill(client: Client, message: Message):
    if not await is_game_enabled(message.chat.id): return
    
    # Fix: Check Reply
    if not message.reply_to_message: 
        return await message.reply_text("❌ You have to reply to a user to kill them!")
    
    killer = await get_user(message.from_user.id)
    victim = await get_user(message.reply_to_message.from_user.id)
    
    # Fix: Dead users CANNOT kill
    if killer['status'] == "dead":
        return await message.reply_text("❌ You are dead! You can only /rob or wait 6h to revive.")
        
    if victim['status'] == "dead": 
        return await message.reply_text("⚠️ They are already dead!")
        
    if time.time() < victim['protected_until']: 
        return await message.reply_text("🛡️ Protected!")

    # Spam cooldown (config-driven)
    now_ts = time.time()
    if now_ts - killer.get('last_kill_time', 0) < KILL_SPAM_COOLDOWN:
        return await message.reply_text(f"⏳ Slow down! Wait {KILL_SPAM_COOLDOWN}s between kills.")

    # Daily kill limit (config-driven)
    if killer.get('kills_today', 0) >= KILL_LIMIT_DAILY:
        return await message.reply_text(f"⚠️ Daily kill limit reached ({KILL_LIMIT_DAILY}/day). Try tomorrow!")

    # Random Reward Logic ($100 - $200)
    reward = random.randint(100, 200)
    
    # Set Victim Dead + Time
    await update_user(victim['_id'], {
        "status": "dead", 
        "death_time": time.time(),
        "balance": 0 # Usually death loses money
    })
    
    # Reward Killer
    await update_user(killer['_id'], {
        "kills": killer['kills'] + 1,
        "kills_today": killer.get('kills_today', 0) + 1,
        "last_kill_time": now_ts,
        "balance": killer['balance'] + reward
    })
    
    # Fix: Exact Message Format
    await message.reply_text(
        f"👤 {message.from_user.mention} killed {message.reply_to_message.from_user.mention}!\n"
        f"💰 Earned: ${reward}"
    )

@Client.on_message(filters.command("revive"))
async def revive(client: Client, message: Message):
    if not await is_game_enabled(message.chat.id): return
    
    # Target is the user being replied to
    if not message.reply_to_message:
        return await message.reply_text("Reply to the user you want to revive!")

    target_user = message.reply_to_message.from_user
    t_data = await get_user(target_user.id)
    p_data = await get_user(message.from_user.id)

    if t_data['status'] == "alive":
        return await message.reply_text(f"✅ {target_user.mention} is already alive!")
        
    if p_data['balance'] < REVIVE_COST:
        return await message.reply_text(f"❌ You need {REVIVE_COST} coins to revive someone!")

    # Deduct Cost
    await update_user(p_data['_id'], {"balance": p_data['balance'] - REVIVE_COST})
    
    # Revive with Random Balance < 200
    revive_bal = random.randint(10, 199)
    await update_user(t_data['_id'], {
        "status": "alive", 
        "death_time": 0,
        "balance": revive_bal
    })
    
    await message.reply_text(f"❤️ Revived {target_user.mention}!\n💰 They spawned with ${revive_bal}.")

@Client.on_message(filters.command("protect"))
async def protect(client: Client, message: Message):
    if len(message.command) < 2: return await message.reply_text("Usage: /protect 1d")
    
    days_map = {"1d": 1, "2d": 2, "3d": 3}
    days = days_map.get(message.command[1])
    if not days: return await message.reply_text("Invalid duration. Use 1d, 2d, or 3d.")
    
    user = await get_user(message.from_user.id)
    if days > 1 and not user.get('premium', False):
        return await message.reply_text("❌ 2d and 3d protection is for Premium Users only!")

    # Config-driven cost (3d falls back to 2d rate + 1 day of 1d rate)
    cost_map = {1: PROTECT_1D_COST, 2: PROTECT_2D_COST, 3: PROTECT_2D_COST + PROTECT_1D_COST}
    cost = cost_map[days]
    if user['balance'] < cost: return await message.reply_text(f"❌ Low Balance. You need ${cost}")
    
    new_expiry = time.time() + (86400 * days)
    await update_user(user['_id'], {"balance": user['balance'] - cost, "protected_until": new_expiry})
    await message.reply_text(f"🛡️ **Protection Activated!**\nDuration: {message.command[1]}")

@Client.on_message(filters.command("give"))
async def give(client: Client, message: Message):
    if not message.reply_to_message: return
    try: amt = int(message.command[1])
    except: return await message.reply_text("Usage: /give [amount]")
    
    sender = await get_user(message.from_user.id)
    if sender['balance'] < amt: return await message.reply_text("❌ Low balance.")
    
    rec = await get_user(message.reply_to_message.from_user.id)
    tax = int(amt * 0.10)
    
    await update_user(sender['_id'], {"balance": sender['balance'] - amt})
    await update_user(rec['_id'], {"balance": rec['balance'] + (amt - tax)})
    await message.reply_text(f"💸 Sent ${amt-tax} (Tax: ${tax})")

# ---------------- UTILITY & FUN COMMANDS ---------------- #

@Client.on_message(filters.command("tr"))
async def translate_cmd(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("❌ Reply to a message to translate it!")
    
    try:
        # Translate detected lang -> English
        txt = message.reply_to_message.text or message.reply_to_message.caption
        if not txt: return
        
        result = trans.translate(txt, dest='en')
        await message.reply_text(
            f"🌍 **Translation (to English):**\n\n`{result.text}`"
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.command("detail"))
async def detail_cmd(client: Client, message: Message):
    # Resolve Target
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target = await client.get_users(message.command[1])
        except:
            return await message.reply_text("❌ User not found.")
    else:
        target = message.from_user
        
    # Fetch Data
    user_data = await get_user(target.id, target.first_name)
    history = user_data.get("name_history", [])
    
    # Format History
    if history:
        history_txt = "\n".join([f"• {n}" for n in set(history[-5:])]) # Show last 5 unique names
    else:
        history_txt = "No name changes recorded."
    
    txt = (
        f"👤 **User Details**\n"
        f"🆔 ID: `{target.id}`\n"
        f"📛 Name: {target.mention}\n"
        f"✏️ Username: @{target.username if target.username else 'None'}\n\n"
        f"📜 **Past Names:**\n{history_txt}"
    )
    await message.reply_text(txt)

@Client.on_message(filters.command("pay"))
async def pay(client: Client, message: Message):
    await message.reply_text("💓 **Jully Premium**\nSend your ID to @MrRockyTg to buy.\n\nYour ID: `/id`")

@Client.on_message(filters.command("toprich"))
async def toprich(client: Client, message: Message):
    top = users_col.find().sort("balance", -1).limit(10)
    txt = "🏆 **Top Richest**\n\n"
    i = 1
    async for u in top:
        txt += f"{i}. {u['name']} - ${u['balance']}\n"
        i += 1
    await message.reply_text(txt)

@Client.on_message(filters.command("topkill"))
async def topkill(client: Client, message: Message):
    top = users_col.find().sort("kills", -1).limit(10)
    txt = "⚔️ **Top Killers**\n\n"
    i = 1
    async for u in top:
        txt += f"{i}. {u['name']} - {u['kills']} Kills\n"
        i += 1
    await message.reply_text(txt)

@Client.on_message(filters.command("items"))
async def shop_list(client: Client, message: Message):
    txt = "📦 **Available Gift Items:**\n\n"
    for key, item in SHOP_ITEMS.items():
        txt += f"{item['emoji']} **{item['name']}** — ${item['cost']}\n"
    await message.reply_text(txt)

@Client.on_message(filters.command("item"))
async def my_items(client: Client, message: Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    user = await get_user(target.id, target.first_name)

    items = user.get("items", {})
    if not items:
        return await message.reply_text(f"{target.mention} has no items yet 😢")

    txt = f"🎒 **{target.first_name}'s Items:**\n\n"
    for key, count in items.items():
        if count > 0:
            meta = SHOP_ITEMS.get(key, {"name": key, "emoji": "❓"})
            txt += f"{meta['emoji']} **{meta['name']}**: {count}\n"
    await message.reply_text(txt)

@Client.on_message(filters.command("gift"))
async def gift_item(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to the user you want to gift!")
    try: item_name = message.command[1].lower()
    except: return await message.reply_text("Usage: /gift rose (Reply to user)")

    item_key = None
    for k in SHOP_ITEMS:
        if k in item_name: item_key = k; break
    if not item_key: return await message.reply_text("❌ Item not found! Check /items")

    sender = await get_user(message.from_user.id)
    receiver = await get_user(message.reply_to_message.from_user.id)
    cost = SHOP_ITEMS[item_key]["cost"]

    if sender['balance'] < cost: return await message.reply_text(f"❌ You need ${cost}!")

    r_items = receiver.get("items", {})
    r_items[item_key] = r_items.get(item_key, 0) + 1

    await update_user(sender['_id'], {"balance": sender['balance'] - cost})
    await update_user(receiver['_id'], {"items": r_items})

    await message.reply_text(f"🎁 You gifted {SHOP_ITEMS[item_key]['emoji']} to {message.reply_to_message.from_user.mention}!")

@Client.on_message(filters.command(["stupid_meter", "brain", "look", "crush", "love"]))
async def fun_meters(client: Client, message: Message):
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply_text("🚫 You can use this command in groups only!")
    p = random.randint(0, 100)
    cmd = message.command[0]
    await message.reply_text(f"📊 **{cmd.title()} Level:** {p}%")

@Client.on_message(filters.command(["slap", "punch", "bite", "kiss", "hug"]))
async def actions(client: Client, message: Message):
    if not message.reply_to_message: return await message.reply_text("Reply to someone!")
    act = message.command[0]
    emojis = {"slap": "👋", "punch": "👊", "bite": "🦷", "kiss": "💋", "hug": "🤗"}
    caption = f"{message.from_user.mention} **{act}ed** {message.reply_to_message.from_user.mention} {emojis.get(act, '')}!"

    # Fetch a matching anime reaction GIF (non-blocking)
    loop = asyncio.get_running_loop()
    gif_url = await loop.run_in_executor(None, _fetch_reaction_gif_sync, act)

    if gif_url:
        try:
            await message.reply_animation(animation=gif_url, caption=caption)
            return
        except Exception as e:
            print(f"⚠️ Failed to send action gif, falling back to text: {e}")

    # Fallback: text-only if the gif fetch/send failed
    await message.reply_text(caption)

@Client.on_message(filters.command(["truth", "dare", "puzzle"]))
async def t_d_p(client: Client, message: Message):
    cmd = message.command[0]
    if cmd == "truth": t = random.choice(["Deepest fear?", "Crush name?"])
    elif cmd == "dare": t = random.choice(["Send a selfie.", "Bark like a dog."])
    else: t = "What is 2+2?"
    await message.reply_text(f"🎲 **{cmd.title()}:** {t}")

@Client.on_message(filters.command("couples"))
async def couples(client: Client, message: Message):
    if message.chat.type == ChatType.PRIVATE: return await message.reply_text("Groups only!")
    await message.reply_text(f"💘 **Couple of the day:** {message.from_user.mention} ❤️ Baka")

@Client.on_message(filters.command("music"))
async def music_list(client: Client, message: Message):
    await message.reply_text("🎶 **Music List:**\n1. Starboy\n2. Mockingbird\n3. Bones")

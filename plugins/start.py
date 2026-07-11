from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType
# Import Texts
from plugins.helper import START_TEXT, HELP_TEXT
# Import Config
from config import BOT_USERNAME, LOG_CHANNEL_ID, START_IMG

# --- START COMMAND ---
@Client.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    # Log the user if it's a private message
    if message.chat.type == ChatType.PRIVATE and LOG_CHANNEL_ID:
        try:
            log_msg = (
                f"🚀 **User Started Bot**\n"
                f"👤 {message.from_user.mention}\n"
                f"🆔 `{message.from_user.id}`"
            )
            await client.send_message(LOG_CHANNEL_ID, log_msg)
        except:
            pass # Fail silently if log channel error

    # Prepare Start Text
    txt = START_TEXT.format(mention=message.from_user.mention)
    
    # Buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ 𝙏𝙖𝙡𝙠 𝙩𝙤 𝙉𝙤𝙫𝙖 💬", callback_data="talk_info")],
        [InlineKeyboardButton("✨ 𝙁𝙧𝙞𝙚𝙣𝙙𝙨 🧸", url="https://t.me/+oL9HctF7LUA4NDRk"),
         InlineKeyboardButton("✨ 𝙂𝙖𝙢𝙚 🎮", callback_data="games_info")],
        [InlineKeyboardButton("➕ Add me to your group 👥", url=f"https://t.me/its_meowBot?startgroup=true")]
    ])
    
    if START_IMG:
        try:
            await message.reply_photo(photo=START_IMG, caption=txt, reply_markup=buttons)
            return
        except Exception as e:
            print(f"⚠️ START_IMG failed, falling back to text: {e}")

    await message.reply_text(text=txt, reply_markup=buttons)

# --- HELP COMMAND ---
@Client.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    await message.reply_text(HELP_TEXT)

# --- ID COMMAND ---
@Client.on_message(filters.command("id"))
async def id_cmd(client: Client, message: Message):
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        await message.reply_text(f"🆔 **User ID:** `{target.id}`")
    else:
        chat_id = message.chat.id
        await message.reply_text(f"🆔 **Chat ID:** `{chat_id}`")

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
        [InlineKeyboardButton("✨ 𝙁𝙧𝙞𝙚𝙣𝙙𝙨 🧸", url="https://t.me/LoveDoseGroup"),
         InlineKeyboardButton("✨ 𝙂𝙖𝙢𝙚 🎮", callback_data="games_info")],
        [InlineKeyboardButton("➕ Add me to your group 👥", url=f"https://t.me/itzNova_bot?startgroup=true")]
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

# --- BOT ADDED TO GROUP (Welcome + Logger) ---
@Client.on_message(filters.new_chat_members)
async def bot_added_to_group(client: Client, message: Message):
    me = await client.get_me()

    # Check if the bot itself is among the new members
    is_bot_added = any(member.id == me.id for member in message.new_chat_members)
    if not is_bot_added:
        return  # Some other user joined, not the bot — ignore

    added_by = message.from_user.mention if message.from_user else "Unknown"

    # 0. Try to get the group's invite link (needed for both welcome + logger)
    group_link = None
    try:
        if message.chat.username:
            # Public group -> direct t.me link, no admin rights needed
            group_link = f"https://t.me/{message.chat.username}"
        elif message.chat.invite_link:
            group_link = message.chat.invite_link
        else:
            # Bot needs "Invite Users" admin permission for this to work
            group_link = await client.export_chat_invite_link(message.chat.id)
    except Exception as e:
        print(f"⚠️ Could not fetch group invite link: {e}")
        group_link = None

    # 1. Send Welcome Message in the Group (with image)
    try:
        welcome_text = (
            f"👋 **Hello everyone!**\n"
            f"Thanks **{added_by}** for adding me to **{message.chat.title}** 💖\n\n"
            f"Use /help to see what I can do!"
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("✨ Add me to another group 👥", url="https://t.me/itzNova_bot?startgroup=true")]
        ])
        if START_IMG:
            try:
                await message.reply_photo(photo=START_IMG, caption=welcome_text, reply_markup=buttons)
            except Exception as e:
                print(f"⚠️ START_IMG failed in welcome message, falling back to text: {e}")
                await message.reply_text(text=welcome_text, reply_markup=buttons)
        else:
            await message.reply_text(text=welcome_text, reply_markup=buttons)
    except Exception as e:
        print(f"⚠️ Failed to send group welcome message: {e}")

    # 2. Send Log to Logger Channel (with group link)
    if LOG_CHANNEL_ID:
        try:
            link_line = f"🔗 **Group Link:** {group_link}\n" if group_link else "🔗 **Group Link:** Not available (private / no permission)\n"
            log_msg = (
                f"➕ **Bot Added to a New Group**\n"
                f"📛 **Group:** {message.chat.title}\n"
                f"🆔 **Group ID:** `{message.chat.id}`\n"
                f"{link_line}"
                f"👤 **Added By:** {added_by}"
            )
            await client.send_message(LOG_CHANNEL_ID, log_msg, disable_web_page_preview=True)
        except Exception as e:
            print(f"⚠️ Failed to send group-add log: {e}")


# --- BOT REMOVED FROM GROUP (Logger) ---
@Client.on_message(filters.left_chat_member)
async def bot_removed_from_group(client: Client, message: Message):
    me = await client.get_me()

    if not message.left_chat_member or message.left_chat_member.id != me.id:
        return  # Some other user left, not the bot — ignore

    removed_by = message.from_user.mention if message.from_user else "Unknown"

    if LOG_CHANNEL_ID:
        try:
            log_msg = (
                f"➖ **Bot Removed from a Group**\n"
                f"📛 **Group:** {message.chat.title}\n"
                f"🆔 **Group ID:** `{message.chat.id}`\n"
                f"👤 **Removed By:** {removed_by}"
            )
            await client.send_message(LOG_CHANNEL_ID, log_msg)
        except Exception as e:
            print(f"⚠️ Failed to send group-remove log: {e}")


# --- ID COMMAND ---
@Client.on_message(filters.command("id"))
async def id_cmd(client: Client, message: Message):
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        await message.reply_text(f"🆔 **User ID:** `{target.id}`")
    else:
        chat_id = message.chat.id
        await message.reply_text(f"🆔 **Chat ID:** `{chat_id}`")

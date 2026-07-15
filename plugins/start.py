import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, User
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import SlowmodeWait, FloodWait
# Import Texts
from plugins.helper import START_TEXT, HELP_TEXT
# Import Config
from config import BOT_USERNAME, LOG_CHANNEL_ID, START_IMG


# --- Reusable Start Menu Builders (also used by the Back button) ---
def build_start_text(user: User) -> str:
    # HTML-style mention (matches the parse_mode used to send this text,
    # so the custom emoji tag in START_TEXT renders correctly)
    mention_html = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    return START_TEXT.format(mention=mention_html)


def build_start_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ 𝙏𝙖𝙡𝙠 𝙩𝙤 𝙈𝙚𝙤𝙬 💬", callback_data="talk_info")],
        [InlineKeyboardButton("✨ 𝙂𝙧𝙤𝙪𝙥 🧸", url="https://t.me/LoveDoseGroup"),
         InlineKeyboardButton("✨ 𝙂𝙖𝙢𝙚 🎮", callback_data="games_info")],
        [InlineKeyboardButton("➕ 𝘼𝙙𝙙 𝙢𝙚 𝙩𝙤 𝙮𝙤𝙪𝙧 𝙜𝙧𝙤𝙪𝙥 👥", url=f"https://t.me/itzMeow_bot?startgroup=true")]
    ])


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
    txt = build_start_text(message.from_user)
    
    # Buttons
    buttons = build_start_buttons()
    
    if START_IMG:
        try:
            await message.reply_photo(photo=START_IMG, caption=txt, reply_markup=buttons, parse_mode=ParseMode.HTML)
            return
        except Exception as e:
            print(f"⚠️ START_IMG failed, falling back to text: {e}")

    await message.reply_text(text=txt, reply_markup=buttons, parse_mode=ParseMode.HTML)

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
    welcome_text = (
        f"👋 **Hello everyone!**\n"
        f"Thanks **{added_by}** for adding me to **{message.chat.title}** 💖\n\n"
        f"Use /help to see what I can do!"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Add me to another group 👥", url="https://t.me/itzMeow_bot?startgroup=true")]
    ])

    async def send_welcome():
        """Send welcome message, retrying once if slowmode/flood wait hits."""
        try:
            if START_IMG:
                try:
                    await message.reply_photo(photo=START_IMG, caption=welcome_text, reply_markup=buttons)
                except (SlowmodeWait, FloodWait) as e:
                    print(f"⏳ Slowmode/Flood hit on photo welcome, waiting {e.value}s...")
                    await asyncio.sleep(e.value)
                    await message.reply_photo(photo=START_IMG, caption=welcome_text, reply_markup=buttons)
                except Exception as e:
                    print(f"⚠️ START_IMG failed in welcome message, falling back to text: {e}")
                    await message.reply_text(text=welcome_text, reply_markup=buttons)
            else:
                await message.reply_text(text=welcome_text, reply_markup=buttons)
        except (SlowmodeWait, FloodWait) as e:
            print(f"⏳ Slowmode/Flood hit on text welcome, waiting {e.value}s...")
            await asyncio.sleep(e.value)
            try:
                await message.reply_text(text=welcome_text, reply_markup=buttons)
            except Exception as e2:
                print(f"⚠️ Failed to send group welcome message after retry: {e2}")
        except Exception as e:
            print(f"⚠️ Failed to send group welcome message: {e}")

    await send_welcome()

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


# --- GET PREMIUM EMOJI ID (utility, reply to a message containing custom/premium emoji) ---
@Client.on_message(filters.command("getemoji"))
async def get_emoji_id_cmd(client: Client, message: Message):
    target = message.reply_to_message
    if not target:
        return await message.reply_text(
            "❌ Reply to a message that contains the premium emoji(s) you want, then send /getemoji"
        )

    from pyrogram.enums import MessageEntityType

    entities = (target.entities or []) + (target.caption_entities or [])
    found = [e for e in entities if e.type == MessageEntityType.CUSTOM_EMOJI]

    if not found:
        return await message.reply_text(
            "❌ No premium/custom emoji found in that message.\n"
            "Note: you must send the emoji yourself (as a Premium user) or forward it — "
            "regular emoji picker emoji won't count."
        )

    text = target.text or target.caption or ""
    lines = ["✅ **Found Premium Emoji ID(s):**\n"]
    for e in found:
        emoji_char = text[e.offset: e.offset + e.length]
        lines.append(f"`{e.custom_emoji_id}` → {emoji_char}")

    await message.reply_text("\n".join(lines))

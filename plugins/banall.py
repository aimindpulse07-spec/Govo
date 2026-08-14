import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors import FloodWait, RPCError
from pyrogram.raw.types import InputPeerChannel, InputPeerChat
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient

from config import API_ID, API_HASH, SESSION_STRING, MONGO_URL, OWNER_ID

# IMPORTANT:
# The user session is used ONLY to discover participants.
# The BOT account performs all ban/unban actions, so the user session
# does not need to be an administrator. The bot itself MUST be an admin
# with permission to ban/restrict users.

_user_app = None
_user_lock = asyncio.Lock()

# Persistent sudo users. Only OWNER_ID can add/remove them.
_mongo = AsyncIOMotorClient(MONGO_URL) if MONGO_URL else None
_sudo_col = _mongo.baka_bot.sudo_users if _mongo else None

async def is_sudo_user(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    if _sudo_col is None:
        return False
    try:
        return await _sudo_col.find_one({"_id": int(user_id)}) is not None
    except Exception:
        return False

async def can_use_mass_commands(client, message):
    if not message.from_user:
        return False
    if await is_sudo_user(message.from_user.id):
        return True
    return await is_group_admin(client, message)


async def get_user_client():
    global _user_app
    if not SESSION_STRING:
        return None
    async with _user_lock:
        if _user_app is None:
            _user_app = Client(
                "govo_banall_user",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=SESSION_STRING,
                in_memory=True,
            )
        if not _user_app.is_connected:
            await _user_app.start()
    return _user_app


async def is_group_admin(client, message):
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return False
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


async def bot_can_ban(client, chat_id):
    try:
        me = await client.get_me()
        member = await client.get_chat_member(chat_id, me.id)
        return member.status == ChatMemberStatus.OWNER or (
            member.status == ChatMemberStatus.ADMINISTRATOR
            and bool(getattr(member.privileges, "can_restrict_members", False))
        )
    except Exception:
        return False


async def is_admin_or_owner(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


async def safe_ban(bot, chat_id, user_id):
    while True:
        try:
            await bot.ban_chat_member(chat_id, user_id)
            return True, None
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
        except RPCError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)


@Client.on_message(filters.command("banall", prefixes=["/", "."]) & filters.group)
async def ban_all(client, message: Message):
    # Owner/Sudo can use this without being a group admin. Normal users must be admins.
    if not await can_use_mass_commands(client, message):
        return await message.reply_text(
            "❌ Sirf group admins, owner ya Sudo Users `/banall` use kar sakte hain."
        )

    if not await bot_can_ban(client, message.chat.id):
        return await message.reply_text(
            "❌ Bot ko Admin + Ban Users permission deni hogi."
        )

    try:
        user_app = await get_user_client()
    except Exception as e:
        return await message.reply_text(
            "❌ User session start nahi ho pa raha. `SESSION_STRING`, `API_ID` aur `API_HASH` check karo.\n\n"
            f"Error: `{type(e).__name__}: {e}`"
        )

    if user_app is None:
        return await message.reply_text(
            "❌ `SESSION_STRING` configured nahi hai. User session discovery ke liye required hai."
        )

    status = await message.reply_text(
        "⏳ Members fetch ho rahe hain...\nUser session admin hona zaroori nahi hai."
    )

    try:
        bot_me = await client.get_me()
        user_me = await user_app.get_me()
        total = 0
        banned = 0
        skipped = 0
        failed = 0

        # User session discovers members; bot does the actual banning.
        async for member in user_app.get_chat_members(message.chat.id):
            user = member.user
            if not user or user.is_deleted or user.is_bot:
                skipped += 1
                continue
            if user.id in (bot_me.id, user_me.id):
                skipped += 1
                continue
            total += 1

            # Never ban current admins/owner.
            if await is_admin_or_owner(client, message.chat.id, user.id):
                skipped += 1
                continue

            ok, _ = await safe_ban(client, message.chat.id, user.id)
            if ok:
                banned += 1
            else:
                failed += 1

            if (banned + failed) % 25 == 0:
                try:
                    await status.edit_text(
                        f"⏳ BanAll running...\n\n"
                        f"Found: {total}\nBanned: {banned}\nFailed: {failed}\nSkipped: {skipped}"
                    )
                except Exception:
                    pass

        await status.edit_text(
            f"✅ BanAll complete.\n\n"
            f"Found: {total}\n"
            f"Banned: {banned}\n"
            f"Failed: {failed}\n"
            f"Skipped: {skipped}"
        )
    except FloodWait as e:
        await asyncio.sleep(e.value + 1)
        await status.edit_text("⚠️ Telegram FloodWait ki wajah se process pause hua. Dobara command chalao.")
    except Exception as e:
        await status.edit_text(f"❌ BanAll error: {e}")


@Client.on_message(filters.command("unbanall", prefixes=["/", "."]) & filters.group)
async def unban_all(client, message: Message):
    if not await can_use_mass_commands(client, message):
        return await message.reply_text(
            "❌ Sirf group admins, owner ya Sudo Users `/unbanall` use kar sakte hain."
        )

    if not await bot_can_ban(client, message.chat.id):
        return await message.reply_text(
            "❌ Bot ko Admin + Ban Users permission deni hogi."
        )

    status = await message.reply_text("⏳ Banned members fetch ho rahe hain...")
    unbanned = 0
    failed = 0
    scanned = 0

    try:
        # This list is requested through the BOT account, which is the admin.
        # Pyrogram exposes banned participants through ChatMembersFilter.BANNED.
        from pyrogram.enums import ChatMembersFilter

        async for member in client.get_chat_members(
            message.chat.id, filter=ChatMembersFilter.BANNED
        ):
            scanned += 1
            user = member.user
            if not user or user.is_deleted:
                continue
            while True:
                try:
                    await client.unban_chat_member(message.chat.id, user.id)
                    unbanned += 1
                    break
                except FloodWait as e:
                    await asyncio.sleep(e.value + 1)
                except Exception:
                    failed += 1
                    break

        await status.edit_text(
            f"✅ UnbanAll complete.\n\nScanned: {scanned}\nUnbanned: {unbanned}\nFailed: {failed}"
        )
    except Exception as e:
        await status.edit_text(f"❌ UnbanAll error: {e}")

from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from plugins.helper import ECONOMY_TEXT, TALK_TEXT
from plugins.start import build_start_text, build_start_buttons

# Back button jo Game aur Talk to Nova dono panels me use hoga
BACK_BUTTON = InlineKeyboardMarkup(
    [[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]
)


async def edit_menu(query: CallbackQuery, text: str, buttons: InlineKeyboardMarkup):
    """Message ko edit karo (photo caption ya text), naya message bhejne ki jagah."""
    try:
        if query.message.photo:
            await query.message.edit_caption(caption=text, reply_markup=buttons)
        else:
            await query.message.edit_text(text=text, reply_markup=buttons)
    except Exception as e:
        print(f"⚠️ Failed to edit menu: {e}")


@Client.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):

    if query.data == "talk_info":
        await query.answer()
        await edit_menu(query, TALK_TEXT, BACK_BUTTON)

    elif query.data == "games_info":
        await query.answer("Opening Games Menu...", show_alert=False)
        await edit_menu(query, ECONOMY_TEXT, BACK_BUTTON)

    elif query.data == "back_to_start":
        await query.answer()
        txt = build_start_text(query.from_user.mention)
        buttons = build_start_buttons()
        await edit_menu(query, txt, buttons)

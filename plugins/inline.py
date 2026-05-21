from pyrogram import Client
from pyrogram.types import CallbackQuery
from plugins.helper import ECONOMY_TEXT

@Client.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    
    if query.data == "talk_info":
        await query.answer()
        await query.message.reply_text(
            "💬 **How to talk to me:**\n\n"
            "Just send me a message in PM, or tag me in a group!\n"
            "Example: `Meow how are you?`"
        )

    elif query.data == "games_info":
        await query.answer("Opening Games Menu...", show_alert=False)
        await query.message.reply_text(ECONOMY_TEXT)

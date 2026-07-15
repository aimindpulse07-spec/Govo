import random
import io
import asyncio
import urllib.parse

from pyrogram import Client, filters
from pyrogram.types import Message

try:
    from gtts import gTTS
    from langdetect import detect
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# --- IMAGE SETTINGS (Pollinations AI - no API key needed) ---
MODEL = "flux-anime"


# --- /draw : AI IMAGE GENERATION ---
@Client.on_message(filters.command("draw"))
async def draw_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "🎨 **Usage:** `/draw a cute cat girl`"
        )

    user_prompt = " ".join(message.command[1:])
    base_prompt = f"{user_prompt}, anime style, masterpiece, best quality, ultra detailed, 8k, vibrant colors, soft lighting"
    encoded_prompt = urllib.parse.quote(base_prompt)

    status = await message.reply_text("🎨 **Painting...**")

    try:
        seed = random.randint(0, 1000000)
        image_url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width=1024&height=1024&seed={seed}&model={MODEL}&nologo=true"
        )

        await client.send_photo(
            chat_id=message.chat.id,
            photo=image_url,
            caption=f"🖼️ **Art by Baka**\n👤 {message.from_user.mention}\n✨ _{user_prompt}_",
        )
        await status.delete()

    except Exception as e:
        await status.edit_text(f"❌ **Error:** Try again later.\n`{e}`")


# --- /speak : TEXT TO VOICE ---
def _generate_audio_sync(text: str):
    """Blocking function, runs in a thread so it doesn't freeze the bot."""
    try:
        lang_code = detect(text)
    except Exception:
        lang_code = "en"

    if lang_code == "hi" or any(
        x in text.lower() for x in ["kaise", "kya", "hai", "nhi", "haan", "bol", "sun"]
    ):
        selected_lang, tld, voice_name = "hi", "co.in", "Indian Girl"
    elif lang_code == "ja":
        selected_lang, tld, voice_name = "ja", "co.jp", "Anime Girl"
    else:
        selected_lang, tld, voice_name = "en", "us", "English Girl"

    audio_fp = io.BytesIO()
    tts = gTTS(text=text, lang=selected_lang, tld=tld, slow=False)
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    audio_fp.name = "voice.mp3"
    return audio_fp, voice_name


@Client.on_message(filters.command("speak"))
async def speak_command(client: Client, message: Message):
    if not TTS_AVAILABLE:
        return await message.reply_text(
            "❌ TTS feature is not installed. Add `gtts` and `langdetect` to requirements.txt."
        )

    text = " ".join(message.command[1:])
    if not text and message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption

    if not text:
        return await message.reply_text("🗣️ **Usage:** `/speak Hello`")

    if len(text) > 500:
        return await message.reply_text("❌ Text too long! (max 500 characters)")

    await client.send_chat_action(message.chat.id, "record_audio")

    try:
        loop = asyncio.get_running_loop()
        audio_bio, voice_name = await loop.run_in_executor(None, _generate_audio_sync, text)

        await client.send_voice(
            chat_id=message.chat.id,
            voice=audio_bio,
            caption=f"🗣️ **Voice:** {voice_name}\n📝 _{text[:50]}..._",
        )
    except Exception as e:
        await message.reply_text(f"❌ **Audio Error:** `{e}`")

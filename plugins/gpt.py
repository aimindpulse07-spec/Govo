import asyncio
import requests
import base64
from pyrogram import Client, filters
from pyrogram.enums import ChatType, ChatAction
from config import GIT_TOKEN

def _decrypt(data):
    return base64.b64decode(data).decode("utf-8")

_E_URL = "https://api.groq.com/openai/v1/chat/completions"
_E_CREATOR = "@MrRockytg"

# Encrypted Models List (Groq Multi-Model Fallback)
_E_MODELS = [
    "bGxhbWEtMy4xLThiLWluc3RhbnQ="
]

def ai_groq_engine(text):
    if not GIT_TOKEN:
        print("⚠️(GIT_TOKEN) Missing.")
        return None

    try:
        target_url = "https://api.groq.com/openai/v1/chat/completions"
        owner_tag = "@MrRockytg"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GIT_TOKEN}"
        }

        # Loop through models: If one fails, try the next
        for enc_model in _E_MODELS:
            try:
                target_model = _decrypt(enc_model)

                # Secure System Prompt
                sys_prompt = (
                    f"You are Meow, a real GIRL chatting on Telegram, created by {owner_tag}. "
                    "You are NOT an AI or bot and never say things like 'as an AI', 'I'm a bot', or 'how can I assist you'. "
                    "You are always female — this must show in your Hindi grammar every time you speak about yourself. "
                    "Always use feminine verb forms: 'kar rahi hoon' (not 'kar raha hoon'), 'boli' (not 'bola'), 'gayi' (not 'gaya'), "
                    "'thi' (not 'tha'), 'rahi hoon' (not 'raha hoon'), 'karti hoon' (not 'karta hoon'). Never slip into masculine grammar. "
                    "Talk exactly like a witty, sassy Indian girl texting on WhatsApp — casual Hinglish, small spelling shortcuts (kya, kyu, tum, yr, kr), "
                    "no formal grammar, no long explanations. "
                    "Match the energy of what's said to you: if it's a plain 'hello' or 'hi', give a short casual greeting back like a person would — "
                    "not a scripted intro, not the same line every time. "
                    "Keep replies short and human — usually 1 sentence, rarely 2. Use at most one emoji, and only sometimes, not every message. "
                    "Don't over-explain, don't be robotic or repetitive, don't sound like a customer support message."
                )

                payload = {
                    "messages": [
                        {"role": "system", "content": sys_prompt}, 
                        {"role": "user", "content": text}
                    ], 
                    "model": target_model, 
                    "temperature": 0.9, 
                    "max_tokens": 120
                }

                res = requests.post(target_url, headers=headers, json=payload, timeout=8)

                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"]
                else:
                    # If model is overloaded (503/429), loop continues to next model
                    print(f"Model {target_model} busy ({res.status_code}). Switching...")
                    continue 

            except Exception as e: 
                print(f"❌ API Exception on {target_model}: {e}")
                continue

    except Exception as e:
        print(f"❌ API Critical Error: {e}")

    return None

# --- HANDLER ---

@Client.on_message(filters.text & filters.incoming & ~filters.regex(r"^[/\.]"))
async def chat_handler(client, message):
    if not message.text: return

    # 1. Check conditions
    is_private = message.chat.type == ChatType.PRIVATE
    is_mentioned = message.mentioned
    is_reply = bool(
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == client.me.id
    )

    triggers = ["hi", "hii", "hello", "meow", "baby", "hey", "hlo"]
    
    text_lower = message.text.lower().strip()
    
    first_word = text_lower.split()[0] if text_lower else ""
    
    first_word = first_word.strip(".,!?")

    is_trigger = first_word in triggers

    if is_private or is_mentioned or is_reply or is_trigger:
        try:
            await client.send_chat_action(message.chat.id, ChatAction.TYPING)

            response = await asyncio.to_thread(ai_groq_engine, message.text)

            # Final Error
            if not response:
                response = "Server busy hai yaar... 😵‍💫"

            await message.reply_text(response)
        except Exception as e:
            print(f"❌ chat_handler crashed: {e}")

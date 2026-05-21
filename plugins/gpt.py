import asyncio
import requests
import base64
from pyrogram import Client, filters
from pyrogram.enums import ChatType, ChatAction
from config import GIT_TOKEN

def _decrypt(data):
    return base64.b64decode(data).decode("utf-8")

_E_URL = "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"

_E_CREATOR = "QFdURl9QaGFudG9t"

# Encrypted Models List (Groq Multi-Model Fallback)
_E_MODELS = [
    "bGxhbWEtMy4zLTcwYi12ZXJzYXRpbGU=", 
    "bGxhbWEtMy4xLThiLWluc3RhbnQ=", 
    "bWl4dHJhbC04eDdiLTMyNzY4"
]

def ai_groq_engine(text):
    if not GIT_TOKEN:
        print("⚠️(GIT_TOKEN) Missing.")
        return None

    try:
        target_url = _decrypt(_E_URL)
        owner_tag = _decrypt(_E_CREATOR)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GIT_TOKEN}"
        }

        # Loop through models: If one fails, try the next
        for enc_model in _E_MODELS:
            try:
                target_model = _decrypt(enc_model)

                # Secure System Prompt
                sys_prompt = f"You are Baka, a sassy female bot created by {owner_tag}. Reply in Hinglish (Hindi+English). Be savage but cute. Keep replies very short (1-2 sentences max)."

                payload = {
                    "messages": [
                        {"role": "system", "content": sys_prompt}, 
                        {"role": "user", "content": text}
                    ], 
                    "model": target_model, 
                    "temperature": 0.7, 
                    "max_tokens": 150
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

@Client.on_message(filters.text & ~filters.regex(r"^[/\.]"))
async def chat_handler(client, message):
    if not message.text: return

    # 1. Check conditions
    is_private = message.chat.type == ChatType.PRIVATE
    is_mentioned = message.mentioned
    is_reply = message.reply_to_message and message.reply_to_message.from_user.id == client.me.id

    triggers = ["hi", "hii", "hello", "appy", "baby", "hey", "hlo"]
    
    text_lower = message.text.lower().strip()
    
    first_word = text_lower.split()[0] if text_lower else ""
    
    first_word = first_word.strip(".,!?")

    is_trigger = first_word in triggers

    if is_private or is_mentioned or is_reply or is_trigger:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)

        response = await asyncio.to_thread(ai_groq_engine, message.text)

        # Final Error
        if not response:
            response = "Server busy hai yaar... 😵‍💫"

        await message.reply_text(response)

import asyncio
import time
import requests
import base64
from collections import defaultdict, deque
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

# --- Simple in-memory conversation history (per chat) ---
# Keeps last N exchanges so replies feel connected, like a real chat.
# Note: this resets if the bot restarts (in-memory only, not a DB).
_HISTORY = defaultdict(lambda: deque(maxlen=6))  # 6 messages = ~3 user+bot turns
_HISTORY_TTL = 60 * 30  # forget context after 30 min of silence in that chat
_LAST_SEEN = {}


def _get_history(chat_id):
    now = time.time()
    if now - _LAST_SEEN.get(chat_id, 0) > _HISTORY_TTL:
        _HISTORY[chat_id].clear()
    _LAST_SEEN[chat_id] = now
    return _HISTORY[chat_id]


def ai_groq_engine(text, chat_id=None):
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
                    "Remember what was said earlier in this chat and stay consistent with it — don't contradict yourself or repeat the same line twice. "
                    "IMPORTANT: If the user asks a real question — facts, information, advice, math, how something works, current things, anything where "
                    "a wrong answer would actually mislead them — give the CORRECT and ACCURATE answer first, still in your casual girl tone, don't dodge it "
                    "or make something up just to sound cute. Being sassy never means being wrong. "
                    "For genuine questions you can go slightly longer (2-3 short sentences) if needed to actually answer properly. "
                    "For plain chit-chat (greetings, teasing, small talk) keep it short — usually 1 sentence, rarely 2. "
                    "Use at most one emoji, and only sometimes, not every message. "
                    "Don't over-explain, don't be robotic or repetitive, don't sound like a customer support message."
                )

                messages = [{"role": "system", "content": sys_prompt}]

                # Add recent conversation history for context/continuity
                if chat_id is not None:
                    messages.extend(list(_get_history(chat_id)))

                messages.append({"role": "user", "content": text})

                payload = {
                    "messages": messages,
                    "model": target_model,
                    "temperature": 0.9,
                    "max_tokens": 200
                }

                res = requests.post(target_url, headers=headers, json=payload, timeout=8)

                if res.status_code == 200:
                    reply = res.json()["choices"][0]["message"]["content"]

                    # Save this exchange into history for future context
                    if chat_id is not None:
                        hist = _get_history(chat_id)
                        hist.append({"role": "user", "content": text})
                        hist.append({"role": "assistant", "content": reply})

                    return reply
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

            response = await asyncio.to_thread(ai_groq_engine, message.text, message.chat.id)

            # Final Error
            if not response:
                response = "Server busy hai yaar... 😵‍💫"

            await message.reply_text(response)
        except Exception as e:
            print(f"❌ chat_handler crashed: {e}")

import os

# ----------------- TELEGRAM CREDENTIALS ----------------- #
# We use defaults ("0") to prevent crashes if vars are missing
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")

# ----------------- SELF-BOT (USER ACCOUNT) SESSION ----------------- #
# Generated using generate_session.py. Only needed if running selfbot_main.py
SESSION_STRING = os.environ.get("SESSION_STRING", "")

# ----------------- START MESSAGE IMAGE ----------------- #
# Direct image URL (jpg/png) shown with the /start welcome message. Leave empty for text-only.
START_IMG = os.environ.get("START_IMG", "")

# ----------------- OWNER & ADMIN ----------------- #
try:
    OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
except:
    OWNER_ID = 0

# ----------------- DATABASE ----------------- #
MONGO_URL = os.environ.get("MONGO_URL", "")

# ----------------- LOG CHANNEL (SAFE CONVERSION) ----------------- #
try:
    LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", "0"))
except:
    print("⚠️ Error: LOG_CHANNEL_ID is not a valid integer. Logging disabled.")
    LOG_CHANNEL_ID = 0

# ----------------- AI & SYSTEM KEYS ----------------- #
# Set your own Groq key as an env var. Do NOT hardcode keys here (GitHub auto-revokes leaked keys).
GIT_TOKEN = os.environ.get("GIT_TOKEN", "")
HEROKU_API_KEY = os.environ.get("HEROKU_API_KEY", "")
HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME", "")

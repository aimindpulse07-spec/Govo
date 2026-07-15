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
START_IMG = os.environ.get("START_IMG", "https://graph.org/file/2eb14c9f89e216976ab64-9b85ce80b1240c7bd3.jpg")

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

# ----------------- GAME / ECONOMY LIMITS (from kirtibaka) ----------------- #
DAILY_BONUS = int(os.environ.get("DAILY_BONUS", "1000"))
REVIVE_COST = int(os.environ.get("REVIVE_COST", "200"))
PROTECT_1D_COST = int(os.environ.get("PROTECT_1D_COST", "2000"))
PROTECT_2D_COST = int(os.environ.get("PROTECT_2D_COST", "3500"))
AUTO_REVIVE_HOURS = int(os.environ.get("AUTO_REVIVE_HOURS", "6"))
KILL_LIMIT_DAILY = int(os.environ.get("KILL_LIMIT_DAILY", "100"))
ROB_LIMIT_DAILY = int(os.environ.get("ROB_LIMIT_DAILY", "200"))
ROB_MAX_AMOUNT = int(os.environ.get("ROB_MAX_AMOUNT", "500000"))
KILL_SPAM_COOLDOWN = int(os.environ.get("KILL_SPAM_COOLDOWN", "3"))  # seconds

# ----------------- AI & SYSTEM KEYS ----------------- #
# Set your own Groq key as an env var. Do NOT hardcode keys here (GitHub auto-revokes leaked keys).
GIT_TOKEN = os.environ.get("GIT_TOKEN", "")
HEROKU_API_KEY = os.environ.get("HEROKU_API_KEY", "")
HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME", "")

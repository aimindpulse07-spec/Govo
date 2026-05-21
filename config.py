import os

# ----------------- TELEGRAM CREDENTIALS ----------------- #
# We use defaults ("0") to prevent crashes if vars are missing
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")

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
GIT_TOKEN = os.environ.get("GIT_TOKEN", "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")
HEROKU_API_KEY = os.environ.get("HEROKU_API_KEY", "")
HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME", "")

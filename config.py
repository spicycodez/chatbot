import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram API credentials
API_ID = os.getenv("API_ID", "28967047")
API_HASH = os.getenv("API_HASH", "9d85609f45b51aa970fa13f6af3d4947")
GPT_API = os.getenv("GPT_API")

# Groq API key (free) — https://console.groq.com
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")  # Fast & good

# Bot token and MongoDB URL fetched from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URL = os.getenv("MONGO_URL", "")

# Bot owner's Telegram user ID and username
OWNER_ID = os.getenv("OWNER_ID",)
OWNER_USERNAME = "SheOwnsMaxim"

# Support group and update channel names
SUPPORT_GROUP = "SpIcYxChAtS"
UPDATE_CHANNEL = "xD_Feelings"

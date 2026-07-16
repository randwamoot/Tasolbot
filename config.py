import os

# ==========================
# Bot Credentials
# ==========================
# TODO: Agar token change karna ho toh yahan apna sahi token paste kar dena
BOT_TOKEN = "8708038876:AAGJ-IefVqZhsS0xYkQHr9JFaxSKsWOnzJs"
OWNER_ID = 6201236707
BOT_NAME = "LX Pays"

# ==========================
# Database & Paths Setup
# ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "users.db")
UPLOADS_PATH = os.path.join(BASE_DIR, "uploads")

# Automatic Uploads Folder Creation
os.makedirs(UPLOADS_PATH, exist_ok=True)

# ==========================
# Business/User Settings
# ==========================
USER_ID_PREFIX = "LX"
START_BALANCE = 0.0
DEFAULT_LEVEL = 1

# ==========================
# Force Subscribe Settings
# ==========================
FORCE_SUBSCRIBE = True

FORCE_SUB_CHANNELS = [
    {
        "name": "Simple Lucky Bio",
        "chat_id": "@simpleluckybio",
        "invite_link": "https://t.me/+FY6IFLXMiL83NDk1"
    },
    {
        "name": "LX Pays",
        "chat_id": "@lxpays",
        "invite_link": "https://t.me/+Q2wKThJ1LQA5ZjI1"
    }
]

# ==========================
# Pagination Limits
# ==========================
TASKS_PER_PAGE = 5
STORE_ITEMS_PER_PAGE = 6
LEADERBOARD_LIMIT = 10


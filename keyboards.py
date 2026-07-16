from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import FORCE_SUB_CHANNELS

# ==========================
# Main Menu
# ==========================
def main_menu_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🏠 Home", callback_data="home"),
        InlineKeyboardButton("👤 Profile", callback_data="profile")
    )
    markup.add(
        InlineKeyboardButton("📋 My Tasks", callback_data="my_tasks"),
        InlineKeyboardButton("💰 Wallet", callback_data="wallet")
    )
    markup.add(
        InlineKeyboardButton("👫 Refer & Earn", callback_data="refer_earn")
    )
    markup.add(
        InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
    )
    return markup

# ==========================
# Home Menu
# ==========================
def home_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("💼 Work", callback_data="work"),
        InlineKeyboardButton("🛒 Store", callback_data="store"),
        InlineKeyboardButton("🎮 Play & Earn", callback_data="play"),
        InlineKeyboardButton("🔙 Back", callback_data="main_menu")
    )
    return markup

# ==========================
# Work Menu
# ==========================
def work_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("⭐ Google Maps", callback_data="google_maps"),
        InlineKeyboardButton("📧 Gmail", callback_data="gmail"),
        InlineKeyboardButton("💬 WhatsApp", callback_data="whatsapp"),
        InlineKeyboardButton("🔙 Back", callback_data="home")
    )
    return markup

# ==========================
# Back Keyboard Wrapper
# ==========================
def back_keyboard(back_callback):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔙 Back", callback_data=back_callback),
        InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
    )
    return markup

# ==========================
# Store Menu
# ==========================
def store_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🎮 Free Fire ID (Likes)", callback_data="store_ff_likes"),
        InlineKeyboardButton("🔥 FF Rank Push", callback_data="store_rank_push"),
        InlineKeyboardButton("❤️ Profile Likes", callback_data="store_profile_likes"),
        InlineKeyboardButton("🔙 Back", callback_data="home")
    )
    return markup

# ==========================
# Play & Earn Menu
# ==========================
def play_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🏆 Free Fire Tournament", callback_data="ff_tournament"),
        InlineKeyboardButton("🎮 Other Games (Soon)", callback_data="other_games"),
        InlineKeyboardButton("🔙 Back", callback_data="home")
    )
    return markup

# ==========================
# Wallet Menu
# ==========================
def wallet_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("💸 Withdraw Request", callback_data="withdraw"),
        InlineKeyboardButton("📜 Withdrawal History", callback_data="withdraw_history"),
        InlineKeyboardButton("🔙 Back", callback_data="main_menu")
    )
    return markup

# ==========================
# My Tasks Menu
# ==========================
def my_tasks_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🟡 Pending", callback_data="status_pending"),
        InlineKeyboardButton("✅ Approved", callback_data="status_approved")
    )
    markup.add(
        InlineKeyboardButton("❌ Rejected", callback_data="status_rejected"),
        InlineKeyboardButton("🔙 Back", callback_data="main_menu")
    )
    return markup

# ==========================
# Leaderboard Menu
# ==========================
def leaderboard_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🔙 Back", callback_data="main_menu")
    )
    return markup

# ==========================
# Force Subscribe Keyboard
# ==========================
def force_subscribe_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    for channel in FORCE_SUB_CHANNELS:
        markup.add(
            InlineKeyboardButton(text=f"📢 {channel['name']}", url=channel["invite_link"])
        )
    markup.add(
        InlineKeyboardButton("✅ Verify", callback_data="verify_join")
    )
    return markup

# ==========================
# DYNAMIC ADMIN REVIEW BUTTONS
# ==========================
def admin_review_keyboard(submission_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{submission_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{submission_id}")
    )
    return markup

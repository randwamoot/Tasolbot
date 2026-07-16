from database import db
from utils import is_user_joined
from keyboards import main_menu_keyboard, force_subscribe_keyboard
from config import BOT_NAME

def register_handlers(bot):
    
    @bot.message_handler(commands=["start"])
    def start(message):
        user_id = message.from_user.id
        
        # Referral Code extract karne ka logic (Deep-linking)
        # Format: /start ESREF12345678
        referred_by = 0
        parts = message.text.split()
        if len(parts) > 1:
            ref_code = parts[1].replace("ESREF", "").replace("LXREF", "").strip()
            if ref_code.isdigit():
                referred_by = int(ref_code)

        # 1. Force Subscribe Check
        if not is_user_joined(bot, user_id):
            # Agar user joined nahi hai, toh registration pending rahegi aur force join keyboard dikhega
            # Referral logic register_callbacks me verify button click hone par chalega
            bot.send_message(
                chat_id=message.chat.id,
                text=(
                    "🔒 <b>Access Locked</b>\n\n"
                    "To use this bot, please join all the required channels first.\n\n"
                    "After joining, tap the <b>✅ Verify</b> button."
                ),
                reply_markup=force_subscribe_keyboard()
            )
            return

        # 2. User Registration (Direct Join bina link ke ya already registered)
        db.add_user(
            telegram_id=user_id,
            name=message.from_user.first_name,
            username=message.from_user.username,
            referred_by=referred_by
        )

        # 3. Main Menu Presentation
        bot.send_message(
            chat_id=message.chat.id,
            text=f"👋 Welcome to <b>{BOT_NAME}</b>\n\nSelect an option below.",
            reply_markup=main_menu_keyboard()
        )

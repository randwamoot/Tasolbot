import telebot
from config import OWNER_ID
from database import db

admin_bot = None

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

def register_admin(bot_instance):
    global admin_bot
    admin_bot = bot_instance

    # ==========================================
    # BULK GMAIL UPLOADER COMMAND
    # ==========================================
    @admin_bot.message_handler(commands=["addgmail"])
    def add_gmail_bulk(message):
        if not is_owner(message.from_user.id):
            return

        lines = message.text.split("\n")
        if len(lines) == 1 and not message.text.replace("/addgmail", "").strip():
            admin_bot.send_message(
                message.chat.id,
                "⚠️ <b>Bulk Upload Format:</b>\n\n"
                "<code>/addgmail\n"
                "email1@gmail.com\n"
                "email2@gmail.com</code>",
                parse_mode="HTML"
            )
            return

        emails = []
        for line in lines:
            if "/addgmail" in line:
                text_part = line.replace("/addgmail", "").strip()
                if text_part:
                    emails.append(text_part)
            else:
                if line.strip():
                    emails.append(line.strip())

        if not emails:
            admin_bot.send_message(message.chat.id, "❌ Koi valid email nahi mili list mein.")
            return

        inserted = db.bulk_insert_gmails(emails)
        admin_bot.send_message(
            message.chat.id,
            f"📊 <b>Bulk Processing Done!</b>\n\n"
            f"📥 Total Received: {len(emails)}\n"
            f"✅ Successfully Added: {inserted}\n"
            f"❌ Skipped/Duplicates: {len(emails) - inserted}",
            parse_mode="HTML"
        )

    # ==========================================
    # 🗑️ NEW: DELETE/CLEAR POOL COMMANDS
    # ==========================================
    @admin_bot.message_handler(commands=["cleargmail"])
    def clear_gmail_pool(message):
        if not is_owner(message.from_user.id):
            return
        try:
            db.cursor.execute("DELETE FROM gmail_inventory")
            db.connection.commit()
            admin_bot.send_message(message.chat.id, "🗑️ <b>Gmail Pool Successfully Cleared!</b> All emails deleted.", parse_mode="HTML")
        except Exception as e:
            admin_bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

    @admin_bot.message_handler(commands=["clearmaps"])
    def clear_maps_pool(message):
        if not is_owner(message.from_user.id):
            return
        try:
            db.cursor.execute("DELETE FROM tasks")
            db.connection.commit()
            admin_bot.send_message(message.chat.id, "🗑️ <b>Maps & Whatsapp Tasks Cleared!</b> All tasks deleted.", parse_mode="HTML")
        except Exception as e:
            admin_bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

    # ==========================================
    # PURANA MAPS ADD TASK COMMAND (SAFE)
    # ==========================================
    @admin_bot.message_handler(commands=["addtask"])
    def add_task(message):
        if not is_owner(message.from_user.id):
            return
        try:
            content = message.text.replace("/addtask", "").strip()
            if not content:
                admin_bot.send_message(message.chat.id, "⚠️ Format: <code>/addtask maps | Title | Reward | Tutorial | Location | ReviewText</code>", parse_mode="HTML")
                return

            parts = [p.strip() for p in content.split("|")]
            category = parts[0].lower()

            if category == "maps" or category == "whatsapp":
                if len(parts) < 6:
                    admin_bot.send_message(message.chat.id, "❌ <b>Format Error!</b> Saare parts bhariye.", parse_mode="HTML")
                    return
                
                title = parts[1]
                reward = float(parts[2])
                tutorial_link = parts[3]
                location_link = parts[4]
                data = parts[5]

                db.cursor.execute(
                    "INSERT INTO tasks (category, title, reward, tutorial_link, location_link, data, active) VALUES (?, ?, ?, ?, ?, ?, 1)",
                    (category, title, reward, tutorial_link, location_link, data)
                )
                db.connection.commit()
                admin_bot.send_message(message.chat.id, f"✅ <b>Maps Task Created!</b>\n\n📌 Title: {title}\n💰 Reward: ₹{reward}", parse_mode="HTML")
        except Exception as e:
            admin_bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

    # ==========================================
    # CORE ADMIN FEATURES (BROADCAST & BALANCES)
    # ==========================================
    @admin_bot.message_handler(commands=["broadcast"])
    def broadcast(message):
        if not is_owner(message.from_user.id):
            return
        text = message.text.replace("/broadcast", "").strip()
        if not text:
            return
        users = db.cursor.execute("SELECT telegram_id FROM users").fetchall()
        for u in users:
            try: admin_bot.send_message(u["telegram_id"], f"📢 <b>Announcement</b>\n\n{text}", parse_mode="HTML")
            except Exception: pass
        admin_bot.send_message(message.chat.id, "✅ Broadcast Done!")

    @admin_bot.message_handler(commands=["addbalance"])
    def add_balance(message):
        if not is_owner(message.from_user.id):
            return
        try:
            parts = message.text.split()
            db.update_wallet(int(parts[1]), float(parts[2]))
            admin_bot.send_message(message.chat.id, "✅ Balance updated!")
        except Exception: pass

    @admin_bot.message_handler(commands=["user"])
    def user_info(message):
        if not is_owner(message.from_user.id):
            return
        try:
            tg_id = int(message.text.split()[1])
            user = db.get_user(tg_id)
            if user:
                admin_bot.send_message(message.chat.id, f"👤 <b>User:</b> {user['name']}\n💰 <b>Balance:</b> ₹{user['wallet']}", parse_mode="HTML")
        except Exception: pass

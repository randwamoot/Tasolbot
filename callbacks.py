from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from utils import is_user_joined
from datetime import datetime
from keyboards import main_menu_keyboard, home_keyboard, work_keyboard, store_keyboard, play_keyboard, wallet_keyboard, my_tasks_keyboard, leaderboard_keyboard, admin_review_keyboard
from config import BOT_NAME, OWNER_ID
from gmail_checker import check_email_exists

bot = None

def process_proof(message, task_id):
    telegram_id = message.from_user.id
    task = db.cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task or task["claimed_by"] != telegram_id:
        bot.send_message(message.chat.id, "❌ Time-out! Task reservation expired.")
        return
    if not message.photo:
        bot.send_message(message.chat.id, "❌ Screenshot image bhejiye.")
        return

    file_id = message.photo[-1].file_id
    sub_id = db.submit_task(telegram_id, task_id, file_id)
    bot.send_message(message.chat.id, "✅ Proof submitted successfully!\n\n⏳ Waiting for Admin approval.")

    try:
        admin_text = f"📥 <b>New Task Submission!</b>\n\n👤 User TG ID: <code>{telegram_id}</code>\n📌 Title: {task['title']}\n💰 Reward: ₹{task['reward']}\n🆔 Ref ID: #{sub_id}"
        bot.send_photo(chat_id=OWNER_ID, photo=file_id, caption=admin_text, reply_markup=admin_review_keyboard(sub_id), parse_mode="HTML")
    except Exception: pass

# ==========================================
# ADVANCED WALLET PIPELINE ENGINE
# ==========================================
def process_upi_withdrawal(message):
    telegram_id = message.from_user.id
    upi_id = message.text.strip()
    
    if "@" not in upi_id or len(upi_id) < 5:
        bot.send_message(message.chat.id, "❌ Invalid UPI Format! Wallet menu me jaakar dubara try karein.")
        return
        
    user = db.get_user(telegram_id)
    balance = user['wallet']
    
    if balance < 100.0:
        bot.send_message(message.chat.id, "❌ Error: Minimum withdrawal limit is ₹100.00!")
        return
        
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Secure Transaction: Main balance se minus karke withdrawals records table me store karenge
    db.cursor.execute("UPDATE users SET wallet = wallet - ? WHERE telegram_id = ?", (balance, telegram_id))
    db.cursor.execute("INSERT INTO withdrawals (telegram_id, amount, upi_id, status, request_time) VALUES (?, ?, ?, 'pending', ?)", (telegram_id, balance, upi_id, now_str))
    withdrawal_id = db.cursor.lastrowid
    db.connection.commit()
    
    bot.send_message(message.chat.id, f"🔒 <b>Request Frozen Successfully!</b>\n\n💰 Pending Amount: ₹{balance:.2f}\n🏦 Processing UPI: <code>{upi_id}</code>\n\n⏳ Status review ke liye Admin panel me forward kar diya gaya hai.")
    
    try:
        admin_markup = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("🟢 Approve & Paid", callback_data=f"wpaid_{withdrawal_id}_{telegram_id}"),
            InlineKeyboardButton("🔴 Reject & Refund", callback_data=f"wreject_{withdrawal_id}_{telegram_id}")
        )
        bot.send_message(
            OWNER_ID,
            f"💸 <b>NEW WITHDRAWAL LEDGER ENTRY!</b>\n\n"
            f"🆔 Req ID: #{withdrawal_id}\n"
            f"👤 Worker ID: <code>{telegram_id}</code>\n"
            f"💰 Cashout Amount: ₹{balance:.2f}\n"
            f"📌 Target UPI Address: <code>{upi_id}</code>\n\n"
            f"Select action after verifying transaction:",
            reply_markup=admin_markup, parse_mode="HTML"
        )
    except Exception: pass

def register_callbacks(bot_instance):
    global bot
    bot = bot_instance

    @bot.callback_query_handler(func=lambda call: call.data == "verify_join")
    def verify_join(call):
        user_id = call.from_user.id
        if is_user_joined(bot, user_id):
            db.add_user(user_id, call.from_user.first_name, call.from_user.username)
            bot.edit_message_text(f"👋 Welcome to <b>{BOT_NAME}</b>", call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
    def approve_submission(call):
        sub_id = call.data.split("_")[1]
        sub = db.get_submission(sub_id)
        if not sub or sub["status"] != "pending": return
        task = db.cursor.execute("SELECT * FROM tasks WHERE id = ?", (sub["task_id"],)).fetchone()
        db.update_submission_status(sub_id, "approved")
        db.update_wallet(sub["telegram_id"], task["reward"])
        db.cursor.execute("UPDATE users SET completed_tasks = completed_tasks + 1 WHERE telegram_id = ?", (sub["telegram_id"],))
        db.connection.commit()
        bot.edit_message_caption(call.message.caption + "\n\n🟢 <b>STATUS: APPROVED</b>", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
    def reject_submission(call):
        sub_id = call.data.split("_")[1]
        sub = db.get_submission(sub_id)
        if not sub or sub["status"] != "pending": return
        db.cursor.execute("DELETE FROM submissions WHERE id = ?", (sub_id,))
        db.connection.commit()
        bot.edit_message_caption(call.message.caption + "\n\n🔴 <b>STATUS: REJECTED</b>", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data in ["gmail", "google_maps", "whatsapp"])
    def filter_work_tasks(call):
        user_id = call.from_user.id
        if db.is_user_blocked(user_id): return
        
        if call.data == "gmail":
            handle_gmail_farmer(call)
            return
            
        category_map = {"google_maps": "maps", "whatsapp": "whatsapp"}
        tasks = db.get_available_tasks(category_map[call.data], user_id)
        markup = InlineKeyboardMarkup(row_width=1)
        for t in tasks:
            markup.add(InlineKeyboardButton(f"📌 {t['title']} | ₹{t['reward']}", callback_data=f"task_{t['id']}"))
        markup.add(InlineKeyboardButton("🔙 Back", callback_data="work"))
        bot.edit_message_text("📂 <b>Available Tasks:</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("task_"))
    def open_task_details(call):
        user_id = call.from_user.id
        task_id = call.data.split("_")[1]
        task = db.cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        markup = InlineKeyboardMarkup()
        if task["claimed_by"] == 0:
            markup.add(InlineKeyboardButton("🔑 Claim & Start Task", callback_data=f"claim_{task_id}"))
        else:
            markup.add(InlineKeyboardButton("📤 Submit Proof", callback_data=f"submit_{task_id}"))
        markup.add(InlineKeyboardButton("🔙 Back", callback_data="work"))
        bot.edit_message_text(f"📌 <b>{task['title']}</b>\nReward: ₹{task['reward']}", call.message.chat.id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("claim_"))
    def claim_task_action(call):
        user_id = call.from_user.id
        task_id = call.data.split("_")[1]
        if db.claim_task(task_id, user_id):
            bot.answer_callback_query(call.id, "✅ Task Claimed!", show_alert=True)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("submit_"))
    def start_submission_flow(call):
        task_id = call.data.split("_")[1]
        bot.register_next_step_handler(call.message, process_proof, task_id)

    # ==========================================
    # GMAIL WORKFLOW OPERATIONS
    # ==========================================
    def handle_gmail_farmer(call):
        user_id = call.from_user.id
        task = db.get_available_gmail_task(user_id)
        if not task:
            bot.edit_message_text("❌ No Gmail Accounts available.", call.message.chat.id, call.message.message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="work")))
            return
        
        text = (
            f"📋 <b>Register Gmail Account:</b>\n\n"
            f"💰 <b>Reward Rate:</b> ₹15.00\n\n"
            f"👤 Name: <code>{task['first_name']}</code>\n"
            f"📅 DOB: <code>{task['dob']}</code>\n"
            f"📧 Email: <code>{task['email']}</code>\n"
            f"🔑 Pass: <code>{task['password']}</code>\n\n"
            f"⏱️ Time Limit: 10 Mins"
        )
        markup = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton("✔️ Done", callback_data=f"gdone_{task['id']}_{task['email']}"),
            InlineKeyboardButton("🚫 Cancel registration", callback_data=f"gconfirmcancel_{task['id']}")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("gconfirmcancel_"))
    def confirm_gmail_cancel(call):
        task_id = call.data.split("_")[1]
        markup = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("✅ Yes, Cancel", callback_data=f"gcancel_{task_id}"),
            InlineKeyboardButton("🔙 No, Keep Working", callback_data="gmail")
        )
        bot.edit_message_text("⚠️ <b>Are you sure?</b>\n\nKya aap sach me ye registration cancel karna chahte hain? Data wapas pool me chala jayega.", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("gdone_") or call.data.startswith("gcancel_"))
    def handle_gmail_actions(call):
        action, task_id = call.data.split("_")[0], call.data.split("_")[1]
        user_id = call.from_user.id
        
        if action == "gcancel":
            db.release_gmail_task(task_id)
            bot.answer_callback_query(call.id, "❌ Task Cancelled.", show_alert=True)
            bot.edit_message_text("💼 <b>Work Section</b>\n\nSelect a category to view active tasks.", call.message.chat.id, call.message.message_id, reply_markup=work_keyboard())
            return
            
        if action == "gdone":
            email = call.data.split("_")[2]
            exists, msg = check_email_exists(email)
            if exists:
                db.set_gmail_pending_admin(task_id)
                task_data = db.cursor.execute("SELECT password FROM gmail_inventory WHERE id = ?", (task_id,)).fetchone()
                current_password = task_data["password"] if task_data else "Unknown"

                user_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("💼 Next Work", callback_data="work"), InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"))
                bot.edit_message_text("✅ <b>Auto-Check Passed!</b> Sent to Admin. Aap agla kaam shuru kar sakte hain!", call.message.chat.id, call.message.message_id, reply_markup=user_markup, parse_mode="HTML")
                
                admin_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🟢 Approve", callback_data=f"gapprove_{task_id}_{user_id}"), InlineKeyboardButton("🔴 Reject", callback_data=f"greject_{task_id}_{user_id}"))
                
                bot.send_message(
                    OWNER_ID, 
                    f"📧 <b>New Gmail Submission!</b>\n\n"
                    f"👤 Worker: <code>{user_id}</code>\n"
                    f"Email: <code>{email}</code>\n"
                    f"🔑 Password: <code>{current_password}</code>\n"
                    f"⚙️ Auto-SMTP: Verified (Live)", 
                    reply_markup=admin_markup, parse_mode="HTML"
                )
            else:
                bot.send_message(call.message.chat.id, f"❌ <b>Verification Failed!</b> Google server ko ye email register nahi mili. Pehle sahi se banayein.", parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("gapprove_") or call.data.startswith("greject_"))
    def admin_gmail_review(call):
        action, task_id, worker_id = call.data.split("_")[0], call.data.split("_")[1], int(call.data.split("_")[2])
        if action == "gapprove":
            db.approve_gmail_task(task_id)
            db.update_wallet(worker_id, 15.0) 
            db.cursor.execute("UPDATE users SET completed_tasks = completed_tasks + 1 WHERE telegram_id = ?", (worker_id,))
            db.connection.commit()
            bot.edit_message_text(call.message.text + "\n\n🟢 <b>APPROVED & PAID</b>", call.message.chat.id, call.message.message_id)
            try: bot.send_message(worker_id, f"🟢 Gmail Approved! Payment added.")
            except Exception: pass
        elif action == "greject":
            db.release_gmail_task(task_id)
            bot.edit_message_text(call.message.text + "\n\n🔴 <b>REJECTED</b>", call.message.chat.id, call.message.message_id)

    # ==========================================
    # ADMIN WITHDRAW MANAGEMENT EXECUTIONS
    # ==========================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("wpaid_") or call.data.startswith("wreject_"))
    def admin_payout_action(call):
        action, withdrawal_id, worker_id = call.data.split("_")[0], int(call.data.split("_")[1]), int(call.data.split("_")[2])
        
        record = db.cursor.execute("SELECT * FROM withdrawals WHERE id = ?", (withdrawal_id,)).fetchone()
        if not record or record["status"] != "pending": return
        
        if action == "wpaid":
            db.cursor.execute("UPDATE withdrawals SET status = 'success' WHERE id = ?", (withdrawal_id,))
            db.connection.commit()
            bot.edit_message_text(call.message.text + "\n\n🟢 <b>PAYMENT RESOLVED & SUCCESS</b>", call.message.chat.id, call.message.message_id)
            try: bot.send_message(worker_id, f"💰 <b>Withdrawal Successful!</b> ₹{record['amount']:.2f} aapke UPI ID par transfer kar diya gaya hai.")
            except Exception: pass
            
        elif action == "wreject":
            # REFUND PROCESS: Ledger status badlenge aur main wallet balance me wapas refund jod denge
            db.cursor.execute("UPDATE withdrawals SET status = 'refunded' WHERE id = ?", (withdrawal_id,))
            db.update_wallet(worker_id, record["amount"])
            db.connection.commit()
            bot.edit_message_text(call.message.text + "\n\n🔴 <b>REQUEST REJECTED & REFUNDED TO USER</b>", call.message.chat.id, call.message.message_id)
            try: bot.send_message(worker_id, f"⚠️ <b>Withdrawal Rejected!</b>\n\n₹{record['amount']:.2f} wapas aapke main wallet balance me refund kar diya gaya hai. Kripya apna UPI address check karke dubara request karein.")
            except Exception: pass

    @bot.callback_query_handler(func=lambda call: call.data == "trigger_withdraw")
    def trigger_withdrawal_flow(call):
        user_id = call.from_user.id
        user = db.get_user(user_id)
        if user['wallet'] < 100.0:
            bot.answer_callback_query(call.id, "❌ Minimum withdrawal requirement is ₹100.00!", show_alert=True)
            return
        msg = bot.send_message(call.message.chat.id, "💸 <b>Enter UPI Handle:</b>\n\nApna active UPI address type karke bhejiye jispar aapko payment chahiye:")
        bot.register_next_step_handler(msg, process_upi_withdrawal)

    # ==========================================
    # CORE INTERFACE CONTROLLERS (FIXED ENGINE)
    # ==========================================
    @bot.callback_query_handler(func=lambda call: call.data in ["main_menu", "home", "work", "profile", "refer_earn", "store", "play", "wallet", "my_tasks", "leaderboard"])
    def core_menus(call):
        user_id = call.from_user.id
        
        if call.data == "main_menu":
            bot.edit_message_text(f"👋 Welcome to <b>{BOT_NAME}</b>\n\nSelect an option below.", call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard())
        elif call.data == "home":
            bot.edit_message_text("🏠 <b>Home Menu</b>\n\nChoose an option below.", call.message.chat.id, call.message.message_id, reply_markup=home_keyboard())
        elif call.data == "work":
            bot.edit_message_text("💼 <b>Work Section</b>\n\nSelect a category to view active tasks.", call.message.chat.id, call.message.message_id, reply_markup=work_keyboard())
            
        elif call.data == "profile":
            user = db.get_user(user_id)
            # Fetch pending items dynamically to clean errors
            pending_wd = db.cursor.execute("SELECT TOTAL(amount) FROM withdrawals WHERE telegram_id = ? AND status = 'pending'", (user_id,)).fetchone()[0]
            text = (
                f"👤 <b>YOUR PROFILE DASHBOARD</b>\n\n"
                f"🆔 User Code: <code>{user['user_id']}</code>\n"
                f"📛 Name: {user['name']}\n"
                f"💰 Available Balance: <b>₹{user['wallet']:.2f}</b>\n"
                f"🔒 Locked Payouts: <b>₹{pending_wd:.2f}</b>\n"
                f"🎯 Total Verified Tasks: {user['completed_tasks']}\n"
                f"⚠️ Active Warnings: {user['warnings']}/3\n"
                f"📅 Register Date: {user['join_date']}"
            )
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="main_menu")), parse_mode="HTML")
            
        elif call.data == "refer_earn":
            user = db.get_user(user_id)
            total_ref = db.cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND status = 'valid'", (user_id,)).fetchone()[0]
            ref_link = f"https://t.me/{bot.get_me().username}?start={user['referral_code']}"
            text = (
                f"👫 <b>REFER & EARN PIPELINE</b>\n\n"
                f"👥 Total Valid Refers: <b>{total_ref} Users</b>\n"
                f"💰 Current Reward Rate: <b>₹2.00 / Invite</b>\n\n"
                f"⚠️ <b>Device Integrity Protection Activated:</b> Multi-account creation on a single terminal or device pattern switching will trigger immediate security flags and invalidate reward codes.\n\n"
                f"🔗 <b>Your Exclusive Link:</b>\n<code>{ref_link}</code>"
            )
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="main_menu")), parse_mode="HTML")
            
        elif call.data == "my_tasks":
            user = db.get_user(user_id)
            pending_img = db.cursor.execute("SELECT COUNT(*) FROM submissions WHERE telegram_id = ? AND status = 'pending'", (user_id,)).fetchone()[0]
            pending_gmail = db.cursor.execute("SELECT COUNT(*) FROM gmail_inventory WHERE claimed_by = ? AND status = 'pending_admin'", (user_id,)).fetchone()[0]
            
            text = (
                f"📋 <b>YOUR TASKS HISTORY REPORT</b>\n\n"
                f"✅ Approved Operations: <b>{user['completed_tasks']} Tasks</b>\n"
                f"⏳ Maps/WA Tasks Pending: <b>{pending_img} Items</b>\n"
                f"📧 Gmail Accounts In Audit: <b>{pending_gmail} Accounts</b>\n\n"
                f"Backend auditing clear hote hi aapke ledger me amount shift kar diya jayega."
            )
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="main_menu")), parse_mode="HTML")
            
        elif call.data == "wallet":
            user = db.get_user(user_id)
            pending_wd = db.cursor.execute("SELECT TOTAL(amount) FROM withdrawals WHERE telegram_id = ? AND status = 'pending'", (user_id,)).fetchone()[0]
            text = (
                f"💰 <b>SECURE WALLET DECK</b>\n\n"
                f"💵 Main Earning Balance: <b>₹{user['wallet']:.2f}</b>\n"
                f"⏳ Locked Payout Queue: <b>₹{pending_wd:.2f}</b>\n\n"
                f"🛑 Minimum Withdrawal Required: ₹100.00"
            )
            markup = InlineKeyboardMarkup(row_width=1).add(
                InlineKeyboardButton("💸 Request Payout (UPI)", callback_data="trigger_withdraw"),
                InlineKeyboardButton("🔙 Back", callback_data="main_menu")
            )
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            
        elif call.data == "leaderboard":
            # Compiling the top 10 earner records across the entire sqlite space
            top_users = db.cursor.execute("SELECT name, wallet FROM users ORDER BY wallet DESC LIMIT 10").fetchall()
            leaderboard_text = "🏆 <b>GLOBAL TOP EARNERS LEADERBOARD</b>\n\n"
            
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            for index, u in enumerate(top_users):
                leaderboard_text += f"{medals[index]} {u['name']} — <b>₹{u['wallet']:.2f}</b>\n"
                
            if not top_users:
                leaderboard_text += "<i>Inventory empty. Work systematically to secure the top spot!</i>"
                
            bot.edit_message_text(leaderboard_text, call.message.chat.id, call.message.message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="main_menu")), parse_mode="HTML")
            
        elif call.data in ["store", "play"]:
            menu_titles = {"store": ("🛒 Store", store_keyboard()), "play": ("🎮 Play & Earn", play_keyboard())}
            title, markup = menu_titles[call.data]
            bot.edit_message_text(f"<b>{title}</b>", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

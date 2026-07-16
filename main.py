import telebot
import time
import threading
from datetime import datetime
from config import BOT_TOKEN, BOT_NAME
from callbacks import register_callbacks
from admin import register_admin
from handlers import register_handlers
from database import db

# Bot Initialization
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Modules Link up
register_handlers(bot)
register_callbacks(bot)
register_admin(bot)

# ==========================
# BACKGROUND TIMEOUT CHECKER (BACKGROUND THREAD)
# ==========================
def auto_release_timeout_loop():
    """
    Ye function background me chupchaap har 10 seconds me chalega
    aur expired reservations ko chheen kar user ko punish karega.
    """
    # Pehle thread ko 5 second rokna hai taaki database completely initialize ho jaye
    time.sleep(5)
    print("⏰ Background Timeout Engine Started Successfully...")
    
    while True:
        try:
            # Table bani hai ya nahi uska safe check
            db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            if not db.cursor.fetchone():
                time.sleep(5)
                continue

            # Sirf wahi tasks uthao jo kisi ne claim kiye hain aur active hain
            claimed_tasks = db.cursor.execute("SELECT * FROM tasks WHERE claimed_by != 0 AND active = 1").fetchall()
            
            for task in claimed_tasks:
                if not task["claim_time"]:
                    continue
                    
                claim_dt = datetime.strptime(task["claim_time"], "%Y-%m-%d %H:%M:%S")
                elapsed_seconds = (datetime.now() - claim_dt).total_seconds()
                
                # 5 Minutes = 300 Seconds
                if elapsed_seconds >= 300:
                    user_id = task["claimed_by"]
                    task_id = task["id"]
                    task_title = task["title"]
                    
                    # 1. Task ko chheeno aur market me wapas dalo
                    db.release_task(task_id)
                    
                    # 2. User ko warning do aur check karo kya wo block hua
                    warnings = db.handle_timeout_user(user_id)
                    
                    # 3. User ko inform karo
                    try:
                        if warnings >= 3:
                            bot.send_message(
                                chat_id=user_id,
                                text=f"🚫 <b>Auto-Block Alert!</b>\n\nAapne task <b>{task_title}</b> ka 5-minute ka time-limit cross kar diya.\n\n⚠️ Aapki total 3 warnings ho chuki hain, isliye aapko <b>24 ghante ke liye block</b> kar diya gaya hai!"
                            )
                        else:
                            bot.send_message(
                                chat_id=user_id,
                                text=f"⚠️ <b>Task Reservation Expired!</b>\n\nAapne task <b>{task_title}</b> ko 5 minute me submit nahi kiya.\n\n🔄 Task wapas available ho gaya hai. Aapko ek warning di gayi hai ({warnings}/3)."
                            )
                    except Exception:
                        pass
                        
        except Exception as e:
            print(f"Error in background timer loop: {str(e)}")
            
        time.sleep(10) # Har 10 seconds me loop chalega

# Thread start karna
timer_thread = threading.Thread(target=auto_release_timeout_loop, daemon=True)
timer_thread.start()

# ==========================
# RUN BOT
# ==========================
if __name__ == "__main__":
    print(f"🔥 [{BOT_NAME}] Project Structure Is 100% Fully Built & Automated!")
    print("👉 Polling loop is now running...")
    
    while True:
        try:
            bot.infinity_polling(
                skip_pending=True,
                timeout=60,
                long_polling_timeout=60
            )
        except Exception as e:
            print(f"Polling crashed, restarting in 5s... Error: {str(e)}")
            time.sleep(5)

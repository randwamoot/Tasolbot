import sqlite3
import random
import string
from datetime import datetime

class Database:
    def __init__(self, db_name="bot_database.db"):
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self.create_tables()
        self.create_gmail_table()
        self.create_financial_and_referral_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                wallet REAL DEFAULT 0.0,
                completed_tasks INTEGER DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                block_until TEXT,
                user_id TEXT UNIQUE,
                referral_code TEXT UNIQUE,
                join_date TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                title TEXT,
                reward REAL,
                tutorial_link TEXT,
                location_link TEXT,
                data TEXT,
                active INTEGER DEFAULT 1,
                claimed_by INTEGER DEFAULT 0,
                claim_time TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                task_id INTEGER,
                file_id TEXT,
                status TEXT DEFAULT 'pending',
                submit_time TEXT
            )
        ''')
        self.connection.commit()

    def create_gmail_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS gmail_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                dob TEXT,
                email TEXT UNIQUE,
                password TEXT DEFAULT '',
                claimed_by INTEGER DEFAULT 0,
                claim_time TEXT,
                status TEXT DEFAULT 'free'
            )
        ''')
        self.connection.commit()

    def create_financial_and_referral_tables(self):
        # 💸 Payout Ledger Tracking Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                amount REAL,
                upi_id TEXT,
                status TEXT DEFAULT 'pending',
                request_time TEXT
            )
        ''')
        # 👫 Secure Referral Logs (Anti-Cheat Validation Table)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                timestamp TEXT,
                status TEXT DEFAULT 'valid'
            )
        ''')
        self.connection.commit()

    # ==========================================
    # CORE USER & WALLET OPERATIONS
    # ==========================================
    def get_user(self, telegram_id):
        return self.cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()

    def add_user(self, telegram_id, name, username):
        if self.get_user(telegram_id):
            return
        user_code = f"USER-{random.randint(100000, 999999)}"
        ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO users (telegram_id, name, username, user_id, referral_code, join_date) VALUES (?, ?, ?, ?, ?, ?)",
            (telegram_id, name, username, user_code, ref_code, now_str)
        )
        self.connection.commit()

    def is_user_blocked(self, telegram_id):
        user = self.get_user(telegram_id)
        if user and user["block_until"]:
            try:
                if datetime.now() < datetime.strptime(user["block_until"], "%Y-%m-%d %H:%M:%S"):
                    return True
            except Exception:
                pass
        return False

    def update_wallet(self, telegram_id, amount):
        self.cursor.execute("UPDATE users SET wallet = wallet + ? WHERE telegram_id = ?", (amount, telegram_id))
        self.connection.commit()

    # ==========================================
    # MAPS & GENERAL TASK DISPATCHERS
    # ==========================================
    def get_available_tasks(self, category, user_id):
        return self.cursor.execute(
            "SELECT * FROM tasks WHERE category = ? AND active = 1 AND (claimed_by = 0 OR claimed_by = ?)",
            (category, user_id)
        ).fetchall()

    def claim_task(self, task_id, user_id):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("UPDATE tasks SET claimed_by = ?, claim_time = ? WHERE id = ? AND claimed_by = 0", (user_id, now_str, task_id))
        self.connection.commit()
        return self.cursor.rowcount > 0

    def release_task(self, task_id):
        self.cursor.execute("UPDATE tasks SET claimed_by = 0, claim_time = NULL WHERE id = ?", (task_id,))
        self.connection.commit()

    def submit_task(self, telegram_id, task_id, file_id):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("INSERT INTO submissions (telegram_id, task_id, file_id, submit_time) VALUES (?, ?, ?, ?)", (telegram_id, task_id, file_id, now_str))
        sub_id = self.cursor.lastrowid
        self.cursor.execute("UPDATE tasks SET active = 0 WHERE id = ?", (task_id,))
        self.connection.commit()
        return sub_id

    def get_submission(self, sub_id):
        return self.cursor.execute("SELECT * FROM submissions WHERE id = ?", (sub_id,)).fetchone()

    def update_submission_status(self, sub_id, status):
        self.cursor.execute("UPDATE submissions SET status = ? WHERE id = ?", (status, sub_id))
        self.connection.commit()

    # ==========================================
    # GMAIL POOL ENGINE ENGINE
    # ==========================================
    def generate_random_password(self, length=8):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for i in range(length))

    def bulk_insert_gmails(self, email_list):
        indian_names = [
            "Rahul", "Amit", "Priya", "Vikram", "Neha", "Rohan", "Anjali", "Suresh", 
            "Deepak", "Jyoti", "Manish", "Aakash", "Pooja", "Sanjay", "Ravi", "Divya",
            "Karan", "Arjun", "Kiran", "Vijay", "Rajesh", "Sunita", "Ajay", "Meena"
        ]
        success_count = 0
        for email in email_list:
            email = email.strip().lower()
            if not email or "@" not in email:
                continue
            random_name = random.choice(indian_names)
            day, month = random.randint(1, 28), random.randint(1, 12)
            year = random.randint(1998, 2006)
            random_dob = f"{day:02d}-{month:02d}-{year}"
            try:
                self.cursor.execute(
                    "INSERT INTO gmail_inventory (first_name, dob, email, password, status) VALUES (?, ?, ?, '', 'free')",
                    (random_name, random_dob, email)
                )
                success_count += 1
            except Exception:
                continue
        self.connection.commit()
        return success_count

    def get_available_gmail_task(self, user_id):
        already_claimed = self.cursor.execute("SELECT * FROM gmail_inventory WHERE claimed_by = ? AND status = 'free'", (user_id,)).fetchone()
        if already_claimed:
            return dict(already_claimed)
        free_task = self.cursor.execute("SELECT * FROM gmail_inventory WHERE status = 'free' AND claimed_by = 0 LIMIT 1").fetchone()
        if free_task:
            free_task = dict(free_task)
            random_pass = self.generate_random_password()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute("UPDATE gmail_inventory SET claimed_by = ?, claim_time = ?, password = ? WHERE id = ?", (user_id, now_str, random_pass, free_task["id"]))
            self.connection.commit()
            free_task["password"] = random_pass
            return free_task
        return None

    def release_gmail_task(self, task_id):
        self.cursor.execute("UPDATE gmail_inventory SET claimed_by = 0, claim_time = NULL, password = '', status = 'free' WHERE id = ?", (task_id,))
        self.connection.commit()

    def set_gmail_pending_admin(self, task_id):
        self.cursor.execute("UPDATE gmail_inventory SET status = 'pending_admin' WHERE id = ?", (task_id,))
        self.connection.commit()

    def approve_gmail_task(self, task_id):
        self.cursor.execute("UPDATE gmail_inventory SET status = 'done' WHERE id = ?", (task_id,))
        self.connection.commit()

db = Database()

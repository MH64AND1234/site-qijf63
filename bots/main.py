import telebot
import os
import subprocess
import json
import re
import threading
import time
import zipfile
import shutil
import sqlite3
import sys
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= الإعدادات الأساسية =================
TOKEN = "8026710964:AAHKvqO6YYkw_7BNCwo41Y6JNv3IVHfJnzs"
OWNER_ID = 6550748735

# ================= المسار التلقائي للاستضافة =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOTS_HOSTING_DIR = os.path.join(BASE_DIR, "bots_hosting")
BOTS_DIR = os.path.join(BOTS_HOSTING_DIR, "bots")
TEMP_DIR = os.path.join(BOTS_HOSTING_DIR, "temp")
BACKUP_DIR = os.path.join(BOTS_HOSTING_DIR, "backups")
DB_FILE = os.path.join(BOTS_HOSTING_DIR, "database.db")

os.makedirs(BOTS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

bot = telebot.TeleBot(TOKEN)

# ================= متغيرات عامة =================
running_processes = {}
waiting_token = {}
waiting_main_file = {}
waiting_approval_limit = {}
waiting_channel = {}
waiting_broadcast = {}
waiting_edit_user_limit = {}
waiting_edit_user_limit_value = {}
waiting_add_attempts = {}
waiting_add_attempts_value = {}
waiting_decrease_attempts = {}
waiting_decrease_attempts_value = {}
waiting_ban_user = {}
waiting_unban_user = {}
waiting_set_points = {}
waiting_set_points_value = {}
waiting_add_points = {}
waiting_add_points_value = {}
waiting_set_file_cost = {}

# تكلفة رفع ملف واحد بالنقاط (يمكن للمالك تغييرها)
FILE_COST_POINTS = 20

# ================= نظام قاعدة البيانات SQLite =================
class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                approved INTEGER DEFAULT 0,
                files_allowed INTEGER DEFAULT 0,
                files_uploaded INTEGER DEFAULT 0,
                banned INTEGER DEFAULT 0,
                points INTEGER DEFAULT 0,
                referral_code TEXT UNIQUE,
                referred_by TEXT,
                last_daily_reward INTEGER DEFAULT 0,
                total_referrals INTEGER DEFAULT 0,
                created_at INTEGER,
                updated_at INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE,
                user_id TEXT,
                bot_name TEXT,
                upload_time INTEGER,
                status TEXT DEFAULT 'stopped',
                disabled INTEGER DEFAULT 0,
                manual_stopped INTEGER DEFAULT 0,
                lang TEXT DEFAULT 'python',
                pid INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                username TEXT,
                first_name TEXT,
                file_name TEXT,
                request_time INTEGER,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE,
                added_by TEXT,
                added_time INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                message_type TEXT,
                message_data TEXT,
                created_at INTEGER,
                attempts INTEGER DEFAULT 0,
                last_attempt INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at INTEGER
            )
        ''')
        
        # إعدادات افتراضية
        cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('file_cost_points', str(FILE_COST_POINTS)))
        
        conn.commit()
        conn.close()
        print(f"✅ تم تهيئة قاعدة البيانات: {self.db_path}")
    
    # ============= دوال المستخدمين =============
    def add_user(self, user_id, username, first_name, referred_by=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # التحقق من وجود المستخدم
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (str(user_id),))
            existing = cursor.fetchone()
            if existing:
                # تحديث المعلومات الأساسية
                cursor.execute('''
                    UPDATE users SET username = ?, first_name = ?, updated_at = ?
                    WHERE user_id = ?
                ''', (username, first_name, int(time.time()), str(user_id)))
                conn.commit()
                return False
            
            # إنشاء كود إحالة فريد
            referral_code = self.generate_referral_code()
            
            cursor.execute('''
                INSERT INTO users 
                (user_id, username, first_name, referral_code, referred_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (str(user_id), username, first_name, referral_code, referred_by, int(time.time()), int(time.time())))
            
            # إذا تمت الإحالة، نضيف نقاط للمُحيل
            if referred_by:
                cursor.execute('''
                    UPDATE users 
                    SET points = points + 10, total_referrals = total_referrals + 1, updated_at = ?
                    WHERE user_id = ?
                ''', (int(time.time()), referred_by))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"⚠️ خطأ في إضافة المستخدم: {e}")
            return False
        finally:
            conn.close()
    
    def generate_referral_code(self, length=8):
        """توليد كود إحالة فريد"""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(chars, k=length))
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (code,))
            if not cursor.fetchone():
                conn.close()
                return code
            conn.close()
    
    def get_user_by_referral(self, code):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (code,))
            row = cursor.fetchone()
            return row['user_id'] if row else None
        finally:
            conn.close()
    
    def get_referral_code(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT referral_code FROM users WHERE user_id = ?', (str(user_id),))
            row = cursor.fetchone()
            return row['referral_code'] if row else None
        finally:
            conn.close()
    
    def approve_user(self, user_id, files_allowed):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users 
                SET approved = 1, files_allowed = ?, updated_at = ?
                WHERE user_id = ?
            ''', (files_allowed, int(time.time()), str(user_id)))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def is_approved(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT approved FROM users WHERE user_id = ?', (str(user_id),))
            row = cursor.fetchone()
            return row and row['approved'] == 1
        finally:
            conn.close()
    
    def ban_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE users SET banned = 1, updated_at = ? WHERE user_id = ?', 
                         (int(time.time()), str(user_id)))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def unban_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE users SET banned = 0, updated_at = ? WHERE user_id = ?', 
                         (int(time.time()), str(user_id)))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def is_banned(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT banned FROM users WHERE user_id = ?', (str(user_id),))
            row = cursor.fetchone()
            return row and row['banned'] == 1
        finally:
            conn.close()
    
    def get_user_stats(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT files_allowed, files_uploaded, approved, banned, points, last_daily_reward, total_referrals
                FROM users WHERE user_id = ?
            ''', (str(user_id),))
            row = cursor.fetchone()
            if row:
                return {
                    'files_allowed': row['files_allowed'],
                    'files_uploaded': row['files_uploaded'],
                    'approved': row['approved'] == 1,
                    'banned': row['banned'] == 1,
                    'points': row['points'],
                    'last_daily_reward': row['last_daily_reward'],
                    'total_referrals': row['total_referrals']
                }
            return None
        finally:
            conn.close()
    
    def update_user_upload_count(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users 
                SET files_uploaded = files_uploaded + 1, updated_at = ?
                WHERE user_id = ?
            ''', (int(time.time()), str(user_id)))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def set_user_files_limit(self, user_id, new_limit):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users 
                SET files_allowed = ?, updated_at = ?
                WHERE user_id = ?
            ''', (new_limit, int(time.time()), str(user_id)))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def add_to_files_limit(self, user_id, additional):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users 
                SET files_allowed = files_allowed + ?, updated_at = ?
                WHERE user_id = ?
            ''', (additional, int(time.time()), str(user_id)))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def subtract_from_files_limit(self, user_id, amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users 
                SET files_allowed = MAX(0, files_allowed - ?), updated_at = ?
                WHERE user_id = ?
            ''', (amount, int(time.time()), str(user_id)))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    # ============= دوال النقاط =============
    def get_file_cost(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT value FROM settings WHERE key = ?', ('file_cost_points',))
            row = cursor.fetchone()
            return int(row['value']) if row else FILE_COST_POINTS
        finally:
            conn.close()
    
    def set_file_cost(self, cost):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', ('file_cost_points', str(cost), int(time.time())))
            conn.commit()
            return True
        finally:
            conn.close()
    
    def get_points(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT points FROM users WHERE user_id = ?', (str(user_id),))
            row = cursor.fetchone()
            return row['points'] if row else 0
        finally:
            conn.close()
    
    def add_points(self, user_id, points):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users SET points = points + ?, updated_at = ? WHERE user_id = ?
            ''', (points, int(time.time()), str(user_id)))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def deduct_points(self, user_id, points):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users SET points = MAX(0, points - ?), updated_at = ? WHERE user_id = ?
            ''', (points, int(time.time()), str(user_id)))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def set_points(self, user_id, points):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users SET points = ?, updated_at = ? WHERE user_id = ?
            ''', (points, int(time.time()), str(user_id)))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def claim_daily_reward(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = int(time.time())
            # التحقق من آخر استلام
            cursor.execute('SELECT last_daily_reward FROM users WHERE user_id = ?', (str(user_id),))
            row = cursor.fetchone()
            if row:
                last = row['last_daily_reward']
                if now - last < 86400:  # أقل من 24 ساعة
                    return False, 86400 - (now - last)
            
            # إضافة النقاط
            cursor.execute('''
                UPDATE users 
                SET points = points + 20, last_daily_reward = ?, updated_at = ?
                WHERE user_id = ?
            ''', (now, now, str(user_id)))
            conn.commit()
            return True, 20
        finally:
            conn.close()
    
    # ============= دوال البوتات =============
    def add_bot(self, file_path, user_id, bot_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO bots 
                (file_path, user_id, bot_name, upload_time, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (file_path, str(user_id), bot_name, int(time.time()), 'stopped'))
            conn.commit()
            return True
        except Exception as e:
            print(f"⚠️ خطأ في إضافة البوت: {e}")
            return False
        finally:
            conn.close()
    
    def update_bot_status(self, file_path, status, pid=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE bots 
                SET status = ?, pid = ?, updated_at = ?
                WHERE file_path = ?
            ''', (status, pid, int(time.time()), file_path))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def disable_bot(self, file_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE bots SET disabled = 1 WHERE file_path = ?', (file_path,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def enable_bot(self, file_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE bots SET disabled = 0 WHERE file_path = ?', (file_path,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def manual_stop_bot(self, file_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE bots SET manual_stopped = 1 WHERE file_path = ?', (file_path,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def manual_start_bot(self, file_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE bots SET manual_stopped = 0 WHERE file_path = ?', (file_path,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def delete_bot(self, file_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM bots WHERE file_path = ?', (file_path,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def get_user_bots(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT * FROM bots 
                WHERE user_id = ?
                ORDER BY upload_time DESC
            ''', (str(user_id),))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_all_bots(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT * FROM bots 
                ORDER BY upload_time DESC
            ''')
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_bot_by_path(self, file_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM bots WHERE file_path = ?', (file_path,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    # ============= دوال الطلبات =============
    def add_pending_request(self, user_id, username, first_name, file_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO pending_requests 
                (user_id, username, first_name, file_name, request_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(user_id), username, first_name, file_name, int(time.time())))
            conn.commit()
            return True
        finally:
            conn.close()
    
    def get_pending_requests(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT * FROM pending_requests 
                WHERE status = 'pending'
                ORDER BY request_time DESC
            ''')
            return cursor.fetchall()
        finally:
            conn.close()
    
    def remove_pending_request(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM pending_requests WHERE user_id = ?', (str(user_id),))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    # ============= دوال القنوات =============
    def add_channel(self, channel_id, added_by):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO channels (channel_id, added_by, added_time)
                VALUES (?, ?, ?)
            ''', (channel_id, str(added_by), int(time.time())))
            conn.commit()
            return True
        finally:
            conn.close()
    
    def remove_channel(self, channel_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM channels WHERE channel_id = ?', (channel_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def get_channels(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT channel_id FROM channels ORDER BY added_time DESC')
            return [row['channel_id'] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    # ============= دوال الرسائل المعلقة =============
    def add_pending_message(self, user_id, message_type, message_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO pending_messages (user_id, message_type, message_data, created_at)
                VALUES (?, ?, ?, ?)
            ''', (str(user_id), message_type, message_data, int(time.time())))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_pending_messages(self, limit=10):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT * FROM pending_messages 
                WHERE attempts < 5
                ORDER BY created_at ASC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def increment_message_attempt(self, msg_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE pending_messages 
                SET attempts = attempts + 1, last_attempt = ?
                WHERE id = ?
            ''', (int(time.time()), msg_id))
            conn.commit()
        finally:
            conn.close()
    
    def delete_pending_message(self, msg_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM pending_messages WHERE id = ?', (msg_id,))
            conn.commit()
        finally:
            conn.close()
    
    # ============= دوال الإحصائيات =============
    def get_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            stats = {}
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE approved = 1')
            stats['approved_users'] = cursor.fetchone()['count']
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE banned = 1')
            stats['banned_users'] = cursor.fetchone()['count']
            cursor.execute('SELECT COUNT(*) as count FROM bots')
            stats['total_bots'] = cursor.fetchone()['count']
            cursor.execute('SELECT COUNT(*) as count FROM bots WHERE status = "running"')
            stats['running_bots'] = cursor.fetchone()['count']
            cursor.execute('SELECT COUNT(*) as count FROM bots WHERE disabled = 1')
            stats['disabled_bots'] = cursor.fetchone()['count']
            cursor.execute('SELECT COUNT(*) as count FROM bots WHERE manual_stopped = 1')
            stats['manual_stopped'] = cursor.fetchone()['count']
            cursor.execute('SELECT COUNT(*) as count FROM pending_requests WHERE status = "pending"')
            stats['pending_requests'] = cursor.fetchone()['count']
            cursor.execute('SELECT COUNT(*) as count FROM channels')
            stats['channels_count'] = cursor.fetchone()['count']
            cursor.execute('SELECT SUM(points) as total_points FROM users')
            stats['total_points'] = cursor.fetchone()['total_points'] or 0
            return stats
        finally:
            conn.close()

db = Database(DB_FILE)

# ================= دوال مساعدة =================
def cancel_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action"))
    return markup

def safe_delete_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

def format_time_elapsed(timestamp):
    if not timestamp:
        return "غير معروف"
    try:
        seconds = time.time() - timestamp
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        if days > 0:
            return f"منذ {days} يوم و {hours} ساعة"
        elif hours > 0:
            return f"منذ {hours} ساعة و {minutes} دقيقة"
        elif minutes > 0:
            return f"منذ {minutes} دقيقة"
        else:
            return "منذ لحظات"
    except:
        return "غير معروف"

def time_remaining(seconds):
    if seconds <= 0:
        return "الآن"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours} ساعة {minutes} دقيقة {secs} ثانية"

# ================= معالج زر الإلغاء =================
@bot.callback_query_handler(func=lambda c: c.data == "cancel_action")
def cancel_action_callback(call):
    user_id = call.message.chat.id
    cleared = False
    dictionaries = [
        waiting_token, waiting_main_file, waiting_channel, waiting_approval_limit,
        waiting_broadcast, waiting_edit_user_limit, waiting_edit_user_limit_value,
        waiting_add_attempts, waiting_add_attempts_value, waiting_decrease_attempts,
        waiting_decrease_attempts_value, waiting_ban_user, waiting_unban_user,
        waiting_set_points, waiting_set_points_value, waiting_add_points, waiting_add_points_value,
        waiting_set_file_cost
    ]
    for d in dictionaries:
        if user_id in d:
            del d[user_id]
            cleared = True
    bot.answer_callback_query(call.id, "✅ تم الإلغاء")
    safe_delete_message(call.message.chat.id, call.message.message_id)
    if cleared:
        bot.send_message(user_id, "✅ تم إلغاء العملية بنجاح.")

# ================= نظام الاشتراك الإجباري =================
def check_subscription(user_id):
    channels = db.get_channels()
    if not channels:
        return True
    for channel in channels:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

def subscription_markup():
    channels = db.get_channels()
    markup = InlineKeyboardMarkup()
    for ch in channels:
        ch_clean = ch.replace('@', '')
        markup.add(InlineKeyboardButton(f"📢 اشترك في {ch}", url=f"https://t.me/{ch_clean}"))
    markup.add(InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub"))
    return markup

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub_callback(call):
    if check_subscription(call.message.chat.id):
        bot.answer_callback_query(call.id, "✅ أنت مشترك!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ أنت غير مشترك!", show_alert=True)

# ================= التحقق من ملفات البوت =================
def is_python_telegram_bot(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        return False
    
    patterns = [
        r'import\s+telebot',
        r'from\s+telebot\s+import',
        r'telebot\.TeleBot',
        r'@bot\.message_handler',
        r'from\s+telegram\.ext\s+import',
        r'Updater\s*=\s*Updater',
        r'ApplicationBuilder',
        r'from\s+pyrogram\s+import',
        r'Client\s*\(\s*["\']bot',
        r'app\.run',
        r'from\s+aiogram\s+import',
        r'Dispatcher',
        r'Bot\s*=\s*Bot',
        r'bot\s*=\s*.*\d{8,10}:[A-Za-z0-9_-]{35,}',
    ]
    
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    
    if re.search(r'\d{8,10}:[A-Za-z0-9_-]{35,}', content):
        for line in content.split('\n'):
            if re.search(r'=\s*["\']?\d{8,10}:[A-Za-z0-9_-]{35,}', line):
                return True
    return False

def find_main_bot_file(folder):
    priority = ["bot.py", "main.py", "app.py", "run.py", "index.py", "__main__.py", "start.py", "telegram_bot.py"]
    for p in priority:
        path = os.path.join(folder, p)
        if os.path.exists(path) and is_python_telegram_bot(path):
            return path
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".py"):
                if "bot" in file.lower() or "telegram" in file.lower():
                    full = os.path.join(root, file)
                    if is_python_telegram_bot(full):
                        return full
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".py"):
                full = os.path.join(root, file)
                if is_python_telegram_bot(full):
                    return full
    return None

def replace_token_in_file(file_path, new_token):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = r'\d{8,10}:[A-Za-z0-9_-]{35,}'
        new_content = re.sub(pattern, new_token, content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    except Exception as e:
        print(f"⚠️ فشل تغيير التوكن: {e}")
        return False

def extract_zip(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        if os.path.exists(zip_path):
            os.remove(zip_path)
        py_files = []
        for root, dirs, files in os.walk(extract_to):
            for file in files:
                if file.endswith(".py"):
                    py_files.append(os.path.join(root, file))
        return py_files
    except Exception as e:
        print(f"⚠️ خطأ في استخراج ZIP: {e}")
        return []

# ================= تشغيل البوت =================
def start_bot_process(file_path):
    try:
        if not os.path.exists(file_path):
            return None, "الملف غير موجود"
        
        if file_path in running_processes:
            try:
                running_processes[file_path].kill()
            except:
                pass
            del running_processes[file_path]
        
        proc = subprocess.Popen(
            [sys.executable, file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(file_path),
            bufsize=1
        )
        
        time.sleep(2)
        
        if proc.poll() is None:
            running_processes[file_path] = proc
            db.update_bot_status(file_path, 'running', proc.pid)
            print(f"✅ تم تشغيل البوت: {os.path.basename(file_path)} (PID: {proc.pid})")
            return proc, None
        else:
            stdout, stderr = proc.communicate(timeout=1)
            error_msg = stderr.strip() or stdout.strip() or "خطأ غير معروف"
            db.update_bot_status(file_path, 'error')
            print(f"❌ فشل تشغيل البوت {os.path.basename(file_path)}: {error_msg[:100]}")
            return None, error_msg
    except Exception as e:
        error_msg = str(e)
        print(f"❌ استثناء أثناء تشغيل البوت {os.path.basename(file_path)}: {e}")
        return None, error_msg

def stop_bot_process(file_path):
    if file_path in running_processes:
        try:
            running_processes[file_path].kill()
        except:
            pass
        del running_processes[file_path]
        db.update_bot_status(file_path, 'stopped')
        return True
    return False

def start_all_bots():
    bots = db.get_all_bots()
    count = 0
    for bot_data in bots:
        file_path = bot_data['file_path']
        if not os.path.exists(file_path):
            continue
        if bot_data['disabled'] == 1 or bot_data['manual_stopped'] == 1:
            continue
        proc, error = start_bot_process(file_path)
        if proc:
            count += 1
    return count

def monitor_bots():
    while True:
        try:
            time.sleep(10)
            bots = db.get_all_bots()
            for bot_data in bots:
                file_path = bot_data['file_path']
                if not os.path.exists(file_path):
                    continue
                if bot_data['disabled'] == 1 or bot_data['manual_stopped'] == 1:
                    if file_path in running_processes:
                        stop_bot_process(file_path)
                    continue
                should_run = True
                if file_path not in running_processes:
                    should_run = True
                else:
                    try:
                        if running_processes[file_path].poll() is not None:
                            should_run = True
                            del running_processes[file_path]
                        else:
                            should_run = False
                    except:
                        should_run = True
                if should_run:
                    proc, error = start_bot_process(file_path)
                    if proc:
                        print(f"🔄 تم إعادة تشغيل البوت: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"⚠️ خطأ في المراقبة: {e}")

def retry_pending_messages():
    while True:
        try:
            time.sleep(30)
            messages = db.get_pending_messages(5)
            for msg in messages:
                user_id = int(msg['user_id'])
                try:
                    if msg['message_type'] == 'approval':
                        bot.send_message(user_id, msg['message_data'], parse_mode="Markdown")
                    elif msg['message_type'] == 'text':
                        bot.send_message(user_id, msg['message_data'])
                    db.delete_pending_message(msg['id'])
                    print(f"✅ تم إرسال رسالة معلقة للمستخدم {user_id}")
                except Exception as e:
                    db.increment_message_attempt(msg['id'])
                    print(f"⚠️ فشل إرسال رسالة معلقة: {e}")
        except Exception as e:
            print(f"⚠️ خطأ في إعادة المحاولة: {e}")

threading.Thread(target=monitor_bots, daemon=True).start()
threading.Thread(target=retry_pending_messages, daemon=True).start()

# ================= أوامر النقاط والإحالة =================
@bot.message_handler(commands=["points"])
def points_command(message):
    user_id = str(message.chat.id)
    if db.is_banned(user_id) and user_id != str(OWNER_ID):
        bot.reply_to(message, "🚫 أنت محظور.", parse_mode="Markdown")
        return
    
    stats = db.get_user_stats(user_id)
    if not stats:
        bot.reply_to(message, "❌ لم يتم العثور على حسابك. أرسل /start أولاً.")
        return
    
    file_cost = db.get_file_cost()
    text = f"""
💰 **رصيد النقاط**
━━━━━━━━━━━━━━━━━━
👤 المستخدم: `{user_id}`
💎 نقاطك الحالية: `{stats['points']}`

📊 **تفاصيل:**
• الملفات المجانية المتبقية: `{max(0, stats['files_allowed'] - stats['files_uploaded'])}`
• تكلفة الملف الواحد: `{file_cost}` نقطة
• إجمالي الإحالات: `{stats['total_referrals']}`

🔗 رابط الإحالة الخاص بك:
`https://t.me/{bot.get_me().username}?start=ref_{db.get_referral_code(user_id)}`
"""
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=["daily"])
def daily_reward(message):
    user_id = str(message.chat.id)
    if db.is_banned(user_id) and user_id != str(OWNER_ID):
        bot.reply_to(message, "🚫 أنت محظور.", parse_mode="Markdown")
        return
    
    success, result = db.claim_daily_reward(user_id)
    if success:
        bot.reply_to(message, f"✅ تم إضافة 20 نقطة إلى رصيدك! رصيدك الحالي: {db.get_points(user_id)}", parse_mode="Markdown")
    else:
        remaining = result
        bot.reply_to(message, f"⏳ يمكنك استلام المكافأة مرة واحدة كل 24 ساعة.\nالوقت المتبقي: {time_remaining(remaining)}", parse_mode="Markdown")

@bot.message_handler(commands=["referral"])
def referral_command(message):
    user_id = str(message.chat.id)
    code = db.get_referral_code(user_id)
    if not code:
        bot.reply_to(message, "❌ لم يتم العثور على كود الإحالة.")
        return
    bot_link = f"https://t.me/{bot.get_me().username}?start=ref_{code}"
    text = f"""
🔗 **رابط الإحالة الخاص بك**
شارك هذا الرابط مع أصدقائك، عندما يدخل شخص جديد عبر الرابط ستحصل أنت على 10 نقاط!

{bot_link}

عدد الإحالات الناجحة: `{db.get_user_stats(user_id)['total_referrals']}`
"""
    bot.reply_to(message, text, parse_mode="Markdown")

# ================= رفع بوت مع استهلاك النقاط (مع تمييز المالك) =================
@bot.message_handler(content_types=['document'])
def upload_bot(message):
    user_id = str(message.chat.id)
    
    # المالك لا يُحظر أبداً
    if db.is_banned(user_id) and user_id != str(OWNER_ID):
        bot.reply_to(message, "🚫 **لقد تم حظرك من استخدام هذا البوت.**", parse_mode="Markdown")
        return
    
    if not check_subscription(message.chat.id) and user_id != str(OWNER_ID):
        markup = subscription_markup()
        bot.reply_to(message, "❌ **يجب الاشتراك في القنوات التالية أولاً:**", 
                    reply_markup=markup, parse_mode="Markdown")
        return
    
    # إذا كان المستخدم هو المالك، نتجاوز كل قيود الموافقة والنقاط
    if user_id == str(OWNER_ID):
        # المالك يرفع فوراً بدون أي قيود
        pass
    elif not db.is_approved(user_id):
        # مستخدم عادي غير موافق عليه
        db.add_user(user_id, message.from_user.username, message.from_user.first_name)
        db.add_pending_request(
            user_id,
            message.from_user.username,
            message.from_user.first_name,
            message.document.file_name
        )
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ موافقة", callback_data=f"approve|{user_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"reject|{user_id}")
        )
        user_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        caption = f"📢 **طلب رفع بوت جديد**\n\n👤 المستخدم: `{user_id}`\n📛 الاسم: {user_info}\n📁 الملف: `{message.document.file_name}`"
        try:
            bot.send_message(OWNER_ID, caption, reply_markup=markup, parse_mode="Markdown")
        except:
            pass
        bot.reply_to(message, "✅ تم إرسال طلبك إلى المالك. سيتم الرد عليك قريبًا.")
        return
    
    file_name = message.document.file_name
    if not (file_name.endswith(".py") or file_name.endswith(".zip")):
        bot.reply_to(message, "❌ فقط ملفات `.py` أو `.zip` مسموحة")
        return
    
    # إذا كان المستخدم هو المالك، لا نطبق أي قيود على الموارد
    if user_id == str(OWNER_ID):
        free_remaining = 999999  # قيمة كبيرة جداً
        points = 999999
        file_cost = 0
        is_owner = True
    else:
        # حساب عدد الملفات المجانية المتبقية للمستخدم العادي
        stats = db.get_user_stats(user_id)
        free_remaining = max(0, stats['files_allowed'] - stats['files_uploaded']) if stats else 0
        file_cost = db.get_file_cost()
        points = db.get_points(user_id) if stats else 0
        is_owner = False
        
        # التحقق من وجود رصيد كافٍ
        if free_remaining <= 0 and points < file_cost:
            bot.reply_to(
                message,
                f"⚠️ **لا تملك رصيد كافٍ لرفع ملف!**\n\n"
                f"📊 الملفات المجانية المتبقية: 0\n"
                f"💰 نقاطك الحالية: {points}\n"
                f"💸 تكلفة الملف: {file_cost} نقطة\n\n"
                f"يمكنك الحصول على نقاط عبر:\n"
                f"• المكافأة اليومية (/daily)\n"
                f"• دعوة الأصدقاء (/referral)\n"
                f"• أو اطلب من المالك إضافة نقاط (/setpoints)",
                parse_mode="Markdown"
            )
            return
    
    # تحميل الملف
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء تحميل الملف: {str(e)[:50]}")
        return
    
    user_folder = os.path.join(BOTS_DIR, user_id)
    os.makedirs(user_folder, exist_ok=True)
    
    if file_name.endswith(".py"):
        file_path = os.path.abspath(os.path.join(user_folder, file_name))
        counter = 1
        while os.path.exists(file_path):
            name, ext = os.path.splitext(file_name)
            file_path = os.path.abspath(os.path.join(user_folder, f"{name}_{counter}{ext}"))
            counter += 1
        
        try:
            with open(file_path, "wb") as f:
                f.write(downloaded)
        except Exception as e:
            bot.reply_to(message, f"❌ فشل في حفظ الملف: {str(e)[:50]}")
            return
        
        if not is_python_telegram_bot(file_path):
            os.remove(file_path)
            bot.reply_to(message, "❌ الملف المرفوع ليس بوت تليجرام بايثون صحيح.")
            return
        
        db.add_bot(file_path, user_id, os.path.basename(file_path))
        
        # خصم الموارد (للمستخدم العادي فقط)
        if not is_owner:
            if free_remaining > 0:
                db.update_user_upload_count(user_id)
                resource_msg = "تم استخدام محاولة مجانية"
            else:
                db.deduct_points(user_id, file_cost)
                resource_msg = f"تم خصم {file_cost} نقطة من رصيدك"
        else:
            resource_msg = "رفع بدون استهلاك نقاط (مالك)"
        
        success = False
        error_msg = None
        if db.get_bot_by_path(file_path)['disabled'] == 0:
            proc, error = start_bot_process(file_path)
            if proc:
                success = True
            else:
                error_msg = error
        
        if success:
            bot.reply_to(
                message,
                f"✅ **تم رفع وتشغيل البوت بنجاح!**\n📁 `{os.path.basename(file_path)}`\n\n{resource_msg}",
                parse_mode="Markdown"
            )
        else:
            if error_msg:
                bot.reply_to(
                    message,
                    f"⚠️ **تم رفع الملف لكن فشل التشغيل**\n\n"
                    f"📁 `{os.path.basename(file_path)}`\n\n"
                    f"❌ **الخطأ:**\n`{error_msg[:300]}`\n\n{resource_msg}",
                    parse_mode="Markdown"
                )
            else:
                bot.reply_to(message, f"✅ تم رفع الملف بنجاح.\n\n{resource_msg}", parse_mode="Markdown")
    
    elif file_name.endswith(".zip"):
        zip_name = os.path.splitext(file_name)[0]
        extract_folder = os.path.join(user_folder, f"{zip_name}_{int(time.time())}")
        os.makedirs(extract_folder, exist_ok=True)
        zip_path = os.path.join(TEMP_DIR, f"{user_id}_{file_name}")
        try:
            with open(zip_path, "wb") as f:
                f.write(downloaded)
        except Exception as e:
            bot.reply_to(message, f"❌ فشل في حفظ ملف ZIP: {str(e)[:50]}")
            return
        
        py_files = extract_zip(zip_path, extract_folder)
        valid_py = [f for f in py_files if is_python_telegram_bot(f)]
        if not valid_py:
            shutil.rmtree(extract_folder, ignore_errors=True)
            bot.reply_to(message, "❌ ملف ZIP لا يحتوي على أي بوت تليجرام بايثون صحيح.")
            return
        
        main_file = find_main_bot_file(extract_folder)
        if main_file:
            file_path = os.path.abspath(main_file)
            db.add_bot(file_path, user_id, os.path.basename(file_path))
            
            if not is_owner:
                if free_remaining > 0:
                    db.update_user_upload_count(user_id)
                    resource_msg = "تم استخدام محاولة مجانية"
                else:
                    db.deduct_points(user_id, file_cost)
                    resource_msg = f"تم خصم {file_cost} نقطة من رصيدك"
            else:
                resource_msg = "رفع بدون استهلاك نقاط (مالك)"
            
            success = False
            error_msg = None
            if db.get_bot_by_path(file_path)['disabled'] == 0:
                proc, error = start_bot_process(file_path)
                if proc:
                    success = True
                else:
                    error_msg = error
            
            if success:
                bot.reply_to(
                    message,
                    f"✅ **تم استخراج وتشغيل البوت بنجاح!**\n📁 `{os.path.basename(main_file)}`\n\n{resource_msg}",
                    parse_mode="Markdown"
                )
            else:
                if error_msg:
                    bot.reply_to(
                        message,
                        f"⚠️ **تم استخراج الملفات لكن فشل التشغيل**\n\n"
                        f"📁 `{os.path.basename(main_file)}`\n\n"
                        f"❌ **الخطأ:**\n`{error_msg[:300]}`\n\n{resource_msg}",
                        parse_mode="Markdown"
                    )
                else:
                    bot.reply_to(message, f"✅ تم استخراج الملفات بنجاح.\n\n{resource_msg}", parse_mode="Markdown")
        else:
            waiting_main_file[message.chat.id] = {
                "folder": extract_folder,
                "user_id": user_id,
                "py_files": valid_py
            }
            markup = InlineKeyboardMarkup(row_width=1)
            for py_file in valid_py[:10]:
                rel_path = os.path.relpath(py_file, extract_folder)
                display_name = os.path.basename(py_file)
                markup.add(InlineKeyboardButton(f"📄 {display_name}", callback_data=f"setmain|{rel_path}"))
            markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action"))
            bot.send_message(
                message.chat.id,
                "❓ **لم أتمكن من تحديد الملف الرئيسي للبوت.**\n\nالرجاء اختيار الملف الذي تريد تشغيله:",
                reply_markup=markup,
                parse_mode="Markdown"
            )

# ================= اختيار الملف الرئيسي (مع تمييز المالك) =================
@bot.callback_query_handler(func=lambda c: c.data.startswith("setmain|"))
def set_main_file(call):
    if call.message.chat.id not in waiting_main_file:
        bot.answer_callback_query(call.id, "❌ انتهت صلاحية الطلب", show_alert=True)
        return
    info = waiting_main_file[call.message.chat.id]
    folder = info["folder"]
    user_id = info["user_id"]
    rel_path = call.data.split("|", 1)[1]
    full_path = os.path.abspath(os.path.join(folder, rel_path))
    if not os.path.exists(full_path):
        bot.answer_callback_query(call.id, "❌ الملف غير موجود", show_alert=True)
        return
    if not is_python_telegram_bot(full_path):
        bot.answer_callback_query(call.id, "❌ الملف ليس بوت تليجرام", show_alert=True)
        return
    
    db.add_bot(full_path, user_id, os.path.basename(full_path))
    
    # تحديد ما إذا كان المستخدم هو المالك
    is_owner = (user_id == str(OWNER_ID))
    
    if is_owner:
        resource_msg = "رفع بدون استهلاك نقاط (مالك)"
    else:
        # حساب الموارد للمستخدم العادي
        stats = db.get_user_stats(user_id)
        free_remaining = max(0, stats['files_allowed'] - stats['files_uploaded']) if stats else 0
        file_cost = db.get_file_cost()
        
        if free_remaining > 0:
            db.update_user_upload_count(user_id)
            resource_msg = "تم استخدام محاولة مجانية"
        else:
            db.deduct_points(user_id, file_cost)
            resource_msg = f"تم خصم {file_cost} نقطة من رصيدك"
    
    success = False
    error_msg = None
    if db.get_bot_by_path(full_path)['disabled'] == 0:
        proc, error = start_bot_process(full_path)
        if proc:
            success = True
        else:
            error_msg = error
    
    del waiting_main_file[call.message.chat.id]
    
    if success:
        bot.edit_message_text(
            f"✅ **تم تشغيل البوت بنجاح!**\n📁 `{os.path.basename(full_path)}`\n\n{resource_msg}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    else:
        bot.edit_message_text(
            f"⚠️ **تم اختيار الملف لكن فشل التشغيل:**\n`{error_msg[:200]}`\n\n{resource_msg}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )

# ================= أوامر المالك لإدارة النقاط =================
@bot.message_handler(commands=["setpoints"])
def set_points_command(message):
    if message.chat.id != OWNER_ID:
        return
    waiting_set_points[OWNER_ID] = True
    markup = cancel_markup()
    bot.reply_to(
        message,
        "💰 **تعديل رصيد نقاط مستخدم**\n\nأرسل معرف المستخدم (الآيدي):",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_set_points)
def handle_set_points_user(message):
    if message.text == "/cancel":
        del waiting_set_points[OWNER_ID]
        bot.reply_to(message, "✅ تم إلغاء العملية")
        return
    user_id = message.text.strip()
    if not db.get_user_stats(user_id):
        bot.reply_to(message, f"❌ المستخدم `{user_id}` غير موجود.", parse_mode="Markdown")
        del waiting_set_points[OWNER_ID]
        return
    waiting_set_points_value[OWNER_ID] = user_id
    del waiting_set_points[OWNER_ID]
    markup = cancel_markup()
    bot.reply_to(
        message,
        f"👤 المستخدم: `{user_id}`\n💰 الرصيد الحالي: {db.get_points(user_id)}\n\nأرسل **الرصيد الجديد** (رقم):",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_set_points_value and m.text and m.text.isdigit())
def handle_set_points_value(message):
    user_id = waiting_set_points_value[OWNER_ID]
    new_points = int(message.text.strip())
    db.set_points(user_id, new_points)
    bot.reply_to(
        message,
        f"✅ **تم تحديث رصيد المستخدم** `{user_id}` إلى {new_points} نقطة.",
        parse_mode="Markdown"
    )
    del waiting_set_points_value[OWNER_ID]

@bot.message_handler(commands=["addpoints"])
def add_points_command(message):
    if message.chat.id != OWNER_ID:
        return
    waiting_add_points[OWNER_ID] = True
    markup = cancel_markup()
    bot.reply_to(
        message,
        "➕ **إضافة نقاط لمستخدم**\n\nأرسل معرف المستخدم (الآيدي):",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_add_points)
def handle_add_points_user(message):
    if message.text == "/cancel":
        del waiting_add_points[OWNER_ID]
        bot.reply_to(message, "✅ تم إلغاء العملية")
        return
    user_id = message.text.strip()
    if not db.get_user_stats(user_id):
        bot.reply_to(message, f"❌ المستخدم `{user_id}` غير موجود.", parse_mode="Markdown")
        del waiting_add_points[OWNER_ID]
        return
    waiting_add_points_value[OWNER_ID] = user_id
    del waiting_add_points[OWNER_ID]
    markup = cancel_markup()
    bot.reply_to(
        message,
        f"👤 المستخدم: `{user_id}`\n💰 الرصيد الحالي: {db.get_points(user_id)}\n\nأرسل **عدد النقاط المراد إضافتها** (رقم):",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_add_points_value and m.text and m.text.isdigit())
def handle_add_points_value(message):
    user_id = waiting_add_points_value[OWNER_ID]
    points = int(message.text.strip())
    db.add_points(user_id, points)
    new_balance = db.get_points(user_id)
    bot.reply_to(
        message,
        f"✅ **تم إضافة {points} نقطة للمستخدم** `{user_id}`\n💰 الرصيد الجديد: {new_balance}",
        parse_mode="Markdown"
    )
    del waiting_add_points_value[OWNER_ID]

@bot.message_handler(commands=["setfilecost"])
def set_file_cost_command(message):
    if message.chat.id != OWNER_ID:
        return
    waiting_set_file_cost[OWNER_ID] = True
    markup = cancel_markup()
    current_cost = db.get_file_cost()
    bot.reply_to(
        message,
        f"💸 **تحديد تكلفة الملف بالنقاط**\nالتكلفة الحالية: {current_cost}\n\nأرسل التكلفة الجديدة (رقم):",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_set_file_cost and m.text and m.text.isdigit())
def handle_set_file_cost(message):
    new_cost = int(message.text.strip())
    db.set_file_cost(new_cost)
    bot.reply_to(
        message,
        f"✅ **تم تحديث تكلفة الملف إلى {new_cost} نقطة.**",
        parse_mode="Markdown"
    )
    del waiting_set_file_cost[OWNER_ID]

# ================= نظام الموافقة على المستخدمين من سجل الطلبات =================
@bot.callback_query_handler(func=lambda c: c.data.startswith("approve|"))
def approve_user_callback(call):
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ هذه الخاصية للمالك فقط", show_alert=True)
        return
    _, user_id = call.data.split("|")
    waiting_approval_limit[OWNER_ID] = user_id
    markup = cancel_markup()
    bot.edit_message_text(
        f"📂 **أدخل عدد الملفات المسموح للمستخدم** `{user_id}`:\n(أرسل رقم فقط)",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("reject|"))
def reject_user_callback(call):
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ هذه الخاصية للمالك فقط", show_alert=True)
        return
    _, user_id = call.data.split("|")
    db.remove_pending_request(user_id)
    bot.edit_message_text(
        f"❌ **تم رفض طلب المستخدم** `{user_id}`",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )
    try:
        bot.send_message(int(user_id), "❌ للأسف، تم رفض طلب رفع البوتات من قبل المالك.")
    except:
        db.add_pending_message(user_id, 'text', "❌ للأسف، تم رفض طلب رفع البوتات من قبل المالك.")

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.text and m.text.isdigit() and OWNER_ID in waiting_approval_limit)
def set_user_limit(message):
    user_id = waiting_approval_limit[OWNER_ID]
    files_allowed = int(message.text.strip())
    db.approve_user(user_id, files_allowed)
    db.remove_pending_request(user_id)
    bot.reply_to(message, f"✅ **تمت الموافقة على المستخدم** `{user_id}`\n📂 الحد الأقصى: {files_allowed} ملفات")
    try:
        bot.send_message(
            int(user_id),
            f"✅ **تمت الموافقة على حسابك!**\n📂 يمكنك رفع {files_allowed} ملف مجاني.\n💰 استخدم /points لمعرفة رصيد نقاطك.\n🎁 استلم مكافأتك اليومية عبر /daily",
            parse_mode="Markdown"
        )
    except:
        db.add_pending_message(
            user_id,
            'approval',
            f"✅ **تمت الموافقة على حسابك!**\n📂 يمكنك رفع {files_allowed} ملف مجاني.\n💰 استخدم /points لمعرفة رصيد نقاطك.\n🎁 استلم مكافأتك اليومية عبر /daily"
        )
    del waiting_approval_limit[OWNER_ID]

# ================= قائمة ملفات المستخدم =================
@bot.message_handler(commands=["mybots"])
def my_bots(message):
    user_id = str(message.chat.id)
    if db.is_banned(user_id) and user_id != str(OWNER_ID):
        bot.reply_to(message, "🚫 **لقد تم حظرك من استخدام هذا البوت.**", parse_mode="Markdown")
        return
    bots = db.get_user_bots(user_id)
    if not bots:
        bot.reply_to(message, "📂 **لا توجد بوتات مرفوعة بعد.**", parse_mode="Markdown")
        return
    for bot_data in bots:
        file_path = bot_data['file_path']
        if not os.path.exists(file_path):
            continue
        time_str = format_time_elapsed(bot_data['upload_time'])
        if file_path in running_processes:
            try:
                if running_processes[file_path].poll() is None:
                    status = "🟢 **شغال**"
                else:
                    status = "🔴 **متوقف**"
                    del running_processes[file_path]
            except:
                status = "🔴 **متوقف**"
        else:
            status = "🔴 **متوقف**"
        if bot_data['disabled'] == 1:
            status += " (🚫 معطل)"
        elif bot_data['manual_stopped'] == 1:
            status += " (🛑 موقوف يدوياً)"
        rel_path = os.path.relpath(file_path, os.path.join(BOTS_DIR, user_id))
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("▶️ تشغيل", callback_data=f"start|{user_id}|{rel_path}"),
            InlineKeyboardButton("⏹ إيقاف", callback_data=f"stop|{user_id}|{rel_path}")
        )
        markup.add(
            InlineKeyboardButton("🗑 حذف", callback_data=f"delete|{user_id}|{rel_path}"),
            InlineKeyboardButton("🔑 توكن", callback_data=f"token|{user_id}|{rel_path}")
        )
        try:
            bot.send_message(
                message.chat.id,
                f"🐍 **{os.path.basename(file_path)}**\n⏳ {time_str}\n{status}",
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"⚠️ خطأ في إرسال رسالة البوت: {e}")

# ================= أوامر المالك (مختصرة) =================
@bot.message_handler(commands=["stats"])
def stats(message):
    if message.chat.id != OWNER_ID:
        return
    stats_data = db.get_stats()
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    text = f"""
👑 **إحصائيات المالك**
━━━━━━━━━━━━━━━━━━
👥 **المستخدمون:**
• موافق عليهم: `{stats_data['approved_users']}`
• بانتظار الموافقة: `{stats_data['pending_requests']}`
• محظورين: `{stats_data['banned_users']}`

🤖 **البوتات:**
• إجمالي البوتات: `{stats_data['total_bots']}`
• نشطة حالياً: `{stats_data['running_bots']}`
• معطلة (مالك): `{stats_data['disabled_bots']}`
• موقوفة يدوياً: `{stats_data['manual_stopped']}`

💰 **النقاط:**
• إجمالي النقاط: `{stats_data['total_points']}`
• تكلفة الملف: `{db.get_file_cost()}` نقطة

📢 **الاشتراك الإجباري:**
• عدد القنوات: `{stats_data['channels_count']}`

💾 **النظام:**
• Python: `{python_version}`
• المسار: `{BASE_DIR}`
• البوتات النشطة: `{len(running_processes)}`
"""
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=["pending"])
def pending_users(message):
    if message.chat.id != OWNER_ID:
        return
    requests = db.get_pending_requests()
    if not requests:
        bot.reply_to(message, "📂 **لا يوجد مستخدمين بانتظار الموافقة**", parse_mode="Markdown")
        return
    text = "⏳ **المستخدمون بانتظار الموافقة:**\n\n"
    markup = InlineKeyboardMarkup(row_width=2)
    for req in requests:
        name = req['username'] or req['first_name'] or req['user_id']
        text += f"• `{req['user_id']}` - {name}\n  📁 `{req['file_name']}`\n  🕐 {format_time_elapsed(req['request_time'])}\n\n"
        markup.add(
            InlineKeyboardButton(f"✅ {req['user_id']}", callback_data=f"approve|{req['user_id']}"),
            InlineKeyboardButton(f"❌ {req['user_id']}", callback_data=f"reject|{req['user_id']}")
        )
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=["ownerbots"])
def owner_bots_list(message):
    if message.chat.id != OWNER_ID:
        return
    bots = db.get_all_bots()
    if not bots:
        bot.reply_to(message, "📂 **لا يوجد أي بوت مرفوع حالياً.**", parse_mode="Markdown")
        return
    sent_count = 0
    for bot_data in bots:
        file_path = bot_data['file_path']
        if not os.path.exists(file_path):
            continue
        time_str = format_time_elapsed(bot_data['upload_time'])
        if file_path in running_processes:
            try:
                if running_processes[file_path].poll() is None:
                    status = "🟢 **شغال**"
                else:
                    status = "🔴 **متوقف**"
            except:
                status = "🔴 **متوقف**"
        else:
            status = "🔴 **متوقف**"
        if bot_data['disabled'] == 1:
            status += " (🚫 معطل)"
        elif bot_data['manual_stopped'] == 1:
            status += " (🛑 موقوف يدوياً)"
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("▶️ تشغيل", callback_data=f"owner_start|{file_path}"),
            InlineKeyboardButton("⏹ إيقاف", callback_data=f"owner_stop|{file_path}")
        )
        try:
            bot.send_message(
                OWNER_ID,
                f"🐍 **{os.path.basename(file_path)}**\n👤 المستخدم: `{bot_data['user_id']}`\n⏳ {time_str}\n{status}",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            sent_count += 1
        except:
            pass
    if sent_count == 0:
        bot.reply_to(message, "📂 **لا توجد بوتات نشطة للعرض.**", parse_mode="Markdown")

@bot.message_handler(commands=["addchannel"])
def add_channel(message):
    if message.chat.id != OWNER_ID:
        return
    waiting_channel[OWNER_ID] = True
    markup = cancel_markup()
    bot.reply_to(
        message,
        "➕ **إضافة قناة اشتراك إجباري**\n\nأرسل معرف القناة بصيغة:\n• `@username`\n• أو المعرف الرقمي",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_channel)
def add_channel_handler(message):
    if message.text == "/cancel":
        del waiting_channel[OWNER_ID]
        bot.reply_to(message, "✅ تم إلغاء العملية")
        return
    channel = message.text.strip()
    if db.add_channel(channel, OWNER_ID):
        bot.reply_to(message, f"✅ **تم إضافة القناة:** {channel}")
    else:
        bot.reply_to(message, "❌ القناة موجودة مسبقاً")
    del waiting_channel[OWNER_ID]

@bot.message_handler(commands=["channels"])
def list_channels(message):
    if message.chat.id != OWNER_ID:
        return
    channels = db.get_channels()
    if not channels:
        bot.reply_to(message, "📋 **لا توجد قنوات اشتراك إجباري**", parse_mode="Markdown")
        return
    text = "📋 **قنوات الاشتراك الإجباري:**\n\n"
    markup = InlineKeyboardMarkup()
    for ch in channels:
        text += f"• {ch}\n"
        markup.add(InlineKeyboardButton(f"❌ حذف {ch}", callback_data=f"remove_channel|{ch}"))
    bot.send_message(OWNER_ID, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("remove_channel|"))
def remove_channel_callback(call):
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ هذه الخاصية للمالك فقط", show_alert=True)
        return
    _, channel = call.data.split("|", 1)
    if db.remove_channel(channel):
        bot.answer_callback_query(call.id, f"✅ تم حذف {channel}")
    else:
        bot.answer_callback_query(call.id, "❌ القناة غير موجودة")
    list_channels(call.message)

@bot.message_handler(commands=["banned"])
def list_banned(message):
    if message.chat.id != OWNER_ID:
        return
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT user_id, username, first_name FROM users WHERE banned = 1')
        banned_users = cursor.fetchall()
        if not banned_users:
            bot.reply_to(message, "📂 **لا يوجد مستخدمين محظورين.**", parse_mode="Markdown")
            return
        text = "🚫 **قائمة المحظورين:**\n\n"
        for user in banned_users:
            name = user['username'] or user['first_name'] or user['user_id']
            text += f"• `{user['user_id']}` - {name}\n"
        bot.reply_to(message, text, parse_mode="Markdown")
    finally:
        conn.close()

@bot.message_handler(commands=["broadcast"])
def broadcast_command(message):
    if message.chat.id != OWNER_ID:
        return
    waiting_broadcast[OWNER_ID] = True
    markup = cancel_markup()
    bot.reply_to(
        message,
        "📢 **نظام الإذاعة**\n\nأرسل الآن **الرسالة التي تريد بثها** لجميع المستخدمين.\nأرسل /cancel أو استخدم زر الإلغاء.",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_broadcast, content_types=['text', 'photo', 'video', 'document'])
def handle_broadcast_content(message):
    if message.chat.id != OWNER_ID:
        return
    del waiting_broadcast[OWNER_ID]
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT user_id FROM users WHERE approved = 1 AND banned = 0')
        users = cursor.fetchall()
    finally:
        conn.close()
    if not users:
        bot.reply_to(message, "📭 **لا يوجد مستخدمون موافق عليهم للإرسال.**", parse_mode="Markdown")
        return
    status_msg = bot.reply_to(message, f"⏳ جاري بث الرسالة إلى {len(users)} مستخدم...")
    success = 0
    failed = 0
    for user in users:
        try:
            if message.content_type == 'text':
                bot.send_message(int(user['user_id']), message.text, parse_mode="Markdown")
            else:
                bot.forward_message(int(user['user_id']), message.chat.id, message.message_id)
            success += 1
            time.sleep(0.05)
        except:
            failed += 1
    bot.edit_message_text(
        f"✅ **تمت الإذاعة بنجاح!**\n\n📨 المستلمون: {success}\n❌ الفشل: {failed}\n👥 الإجمالي: {len(users)}",
        status_msg.chat.id,
        status_msg.message_id,
        parse_mode="Markdown"
    )

# ================= لوحة المالك =================
@bot.message_handler(commands=["panel"])
def panel_command(message):
    if message.chat.id != OWNER_ID:
        return
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 إحصائيات", callback_data="stats_panel"),
        InlineKeyboardButton("⏳ طلبات الانتظار", callback_data="pending_panel"),
        InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel_panel"),
        InlineKeyboardButton("📋 القنوات", callback_data="channels_panel"),
        InlineKeyboardButton("📋 كل البوتات", callback_data="owner_bots_panel"),
        InlineKeyboardButton("📢 إذاعة", callback_data="broadcast_panel"),
        InlineKeyboardButton("✏️ تعديل حد", callback_data="edit_user_limit_panel"),
        InlineKeyboardButton("➕ إضافة محاولات", callback_data="add_attempts_panel"),
        InlineKeyboardButton("➖ تنقيص محاولات", callback_data="decrease_attempts_panel"),
        InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban_user_panel"),
        InlineKeyboardButton("✅ إلغاء حظر", callback_data="unban_user_panel"),
        InlineKeyboardButton("📋 قائمة المحظورين", callback_data="banned_list_panel"),
        InlineKeyboardButton("💰 إدارة النقاط", callback_data="points_management_panel"),
        InlineKeyboardButton("💾 تحديث الإحصائيات", callback_data="refresh_stats")
    )
    bot.send_message(OWNER_ID, "👑 **لوحة تحكم المالك**\nاختر العملية التي تريدها:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "points_management_panel")
def points_management_panel(call):
    if call.message.chat.id != OWNER_ID:
        return
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("💰 تعيين رصيد", callback_data="setpoints_panel"),
        InlineKeyboardButton("➕ إضافة نقاط", callback_data="addpoints_panel"),
        InlineKeyboardButton("💸 تكلفة الملف", callback_data="setfilecost_panel")
    )
    bot.edit_message_text(
        "💰 **إدارة النقاط**\nاختر العملية:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data == "setpoints_panel")
def setpoints_panel(call):
    if call.message.chat.id != OWNER_ID:
        return
    set_points_command(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "addpoints_panel")
def addpoints_panel(call):
    if call.message.chat.id != OWNER_ID:
        return
    add_points_command(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "setfilecost_panel")
def setfilecost_panel(call):
    if call.message.chat.id != OWNER_ID:
        return
    set_file_cost_command(call.message)

# باقي معالجات الأزرار للوحة التحكم
@bot.callback_query_handler(func=lambda c: c.data == "panel")
def callback_panel(call):
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ هذه الخاصية للمالك فقط", show_alert=True)
        return
    panel_command(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "stats_panel")
def callback_stats_panel(call):
    if call.message.chat.id != OWNER_ID:
        return
    stats(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "pending_panel")
def callback_pending_panel(call):
    if call.message.chat.id != OWNER_ID:
        return
    pending_users(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "add_channel_panel")
def callback_add_channel_panel(call):
    if call.message.chat.id != OWNER_ID:
        return
    add_channel(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "channels_panel")
def callback_channels_panel(call):
    if call.message.chat.id != OWNER_ID:
        return
    list_channels(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "owner_bots_panel")
def callback_owner_bots_panel(call):
    if call.message.chat.id != OWNER_ID:
        return
    owner_bots_list(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_panel")
def callback_broadcast_panel(call):
    if call.message.chat.id != OWNER_ID:
        return
    broadcast_command(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "banned_list_panel")
def callback_banned_list_panel(call):
    if call.message.chat.id != OWNER_ID:
        return
    list_banned(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "refresh_stats")
def callback_refresh_stats(call):
    if call.message.chat.id != OWNER_ID:
        return
    bot.answer_callback_query(call.id, "✅ تم تحديث الإحصائيات")
    stats(call.message)

# ================= أوامر تعديل الحدود والحظر =================
@bot.callback_query_handler(func=lambda c: c.data == "edit_user_limit_panel")
def callback_edit_user_limit_panel(call):
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ هذه الخاصية للمالك فقط", show_alert=True)
        return
    waiting_edit_user_limit[OWNER_ID] = True
    markup = cancel_markup()
    bot.edit_message_text(
        "✏️ **تعديل حد المستخدم**\n\nأرسل معرف المستخدم (الآيدي):",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_edit_user_limit)
def handle_edit_user_id(message):
    if message.text == "/cancel":
        del waiting_edit_user_limit[OWNER_ID]
        bot.reply_to(message, "✅ تم إلغاء العملية")
        return
    user_id = message.text.strip()
    if not db.is_approved(user_id):
        bot.reply_to(message, f"❌ المستخدم `{user_id}` غير موافق عليه.", parse_mode="Markdown")
        del waiting_edit_user_limit[OWNER_ID]
        return
    waiting_edit_user_limit_value[OWNER_ID] = user_id
    del waiting_edit_user_limit[OWNER_ID]
    user_stats = db.get_user_stats(user_id)
    current_limit = user_stats['files_allowed'] if user_stats else 0
    markup = cancel_markup()
    bot.reply_to(
        message,
        f"👤 المستخدم: `{user_id}`\n📊 الحد الحالي: `{current_limit}`\n\nأرسل **الحد الجديد** (رقم):",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_edit_user_limit_value and m.text and m.text.isdigit())
def handle_edit_user_limit(message):
    user_id = waiting_edit_user_limit_value[OWNER_ID]
    new_limit = int(message.text.strip())
    user_stats = db.get_user_stats(user_id)
    old_limit = user_stats['files_allowed'] if user_stats else 0
    if db.set_user_files_limit(user_id, new_limit):
        bot.reply_to(
            message,
            f"✅ **تم تحديث حد المستخدم** `{user_id}`\n📂 من {old_limit} إلى {new_limit}",
            parse_mode="Markdown"
        )
        try:
            bot.send_message(int(user_id), f"✅ **تم تحديث حد رفع البوتات الخاص بك**\n📂 الحد الجديد: {new_limit} ملف")
        except:
            pass
    else:
        bot.reply_to(message, f"❌ المستخدم `{user_id}` غير موجود.", parse_mode="Markdown")
    del waiting_edit_user_limit_value[OWNER_ID]

@bot.callback_query_handler(func=lambda c: c.data == "add_attempts_panel")
def callback_add_attempts_panel(call):
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ هذه الخاصية للمالك فقط", show_alert=True)
        return
    waiting_add_attempts[OWNER_ID] = True
    markup = cancel_markup()
    bot.edit_message_text(
        "➕ **إضافة محاولات رفع للمستخدم**\n\nأرسل معرف المستخدم (الآيدي):",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_add_attempts)
def handle_add_attempts_user_id(message):
    if message.text == "/cancel":
        del waiting_add_attempts[OWNER_ID]
        bot.reply_to(message, "✅ تم إلغاء العملية")
        return
    user_id = message.text.strip()
    if not db.is_approved(user_id):
        bot.reply_to(message, f"❌ المستخدم `{user_id}` غير موافق عليه.", parse_mode="Markdown")
        del waiting_add_attempts[OWNER_ID]
        return
    waiting_add_attempts_value[OWNER_ID] = user_id
    del waiting_add_attempts[OWNER_ID]
    user_stats = db.get_user_stats(user_id)
    current_limit = user_stats['files_allowed'] if user_stats else 0
    used = user_stats['files_uploaded'] if user_stats else 0
    markup = cancel_markup()
    bot.reply_to(
        message,
        f"👤 المستخدم: `{user_id}`\n📊 الحد الحالي: `{current_limit}`\n📤 المستخدم: `{used}`\n\nأرسل **عدد المحاولات الإضافية** (رقم):",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_add_attempts_value and m.text and m.text.isdigit())
def handle_add_attempts_value(message):
    user_id = waiting_add_attempts_value[OWNER_ID]
    additional = int(message.text.strip())
    user_stats = db.get_user_stats(user_id)
    old_limit = user_stats['files_allowed'] if user_stats else 0
    if db.add_to_files_limit(user_id, additional):
        new_limit = old_limit + additional
        bot.reply_to(
            message,
            f"✅ **تمت إضافة {additional} محاولة رفع للمستخدم** `{user_id}`\n📂 الحد القديم: {old_limit}\n📂 الحد الجديد: {new_limit}",
            parse_mode="Markdown"
        )
        try:
            bot.send_message(int(user_id), f"✅ **تمت إضافة {additional} محاولة رفع لحسابك**\n📂 الحد الجديد: {new_limit} ملف")
        except:
            pass
    else:
        bot.reply_to(message, f"❌ المستخدم `{user_id}` غير موجود.", parse_mode="Markdown")
    del waiting_add_attempts_value[OWNER_ID]

@bot.callback_query_handler(func=lambda c: c.data == "decrease_attempts_panel")
def callback_decrease_attempts_panel(call):
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ هذه الخاصية للمالك فقط", show_alert=True)
        return
    waiting_decrease_attempts[OWNER_ID] = True
    markup = cancel_markup()
    bot.edit_message_text(
        "➖ **تنقيص محاولات رفع المستخدم**\n\nأرسل معرف المستخدم (الآيدي):",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_decrease_attempts)
def handle_decrease_attempts_user_id(message):
    if message.text == "/cancel":
        del waiting_decrease_attempts[OWNER_ID]
        bot.reply_to(message, "✅ تم إلغاء العملية")
        return
    user_id = message.text.strip()
    if not db.is_approved(user_id):
        bot.reply_to(message, f"❌ المستخدم `{user_id}` غير موافق عليه.", parse_mode="Markdown")
        del waiting_decrease_attempts[OWNER_ID]
        return
    waiting_decrease_attempts_value[OWNER_ID] = user_id
    del waiting_decrease_attempts[OWNER_ID]
    user_stats = db.get_user_stats(user_id)
    current_limit = user_stats['files_allowed'] if user_stats else 0
    used = user_stats['files_uploaded'] if user_stats else 0
    markup = cancel_markup()
    bot.reply_to(
        message,
        f"👤 المستخدم: `{user_id}`\n📊 الحد الحالي: `{current_limit}`\n📤 المستخدم: `{used}`\n\nأرسل **عدد المحاولات المراد خصمها** (رقم):",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_decrease_attempts_value and m.text and m.text.isdigit())
def handle_decrease_attempts_value(message):
    user_id = waiting_decrease_attempts_value[OWNER_ID]
    decrease = int(message.text.strip())
    user_stats = db.get_user_stats(user_id)
    old_limit = user_stats['files_allowed'] if user_stats else 0
    if db.subtract_from_files_limit(user_id, decrease):
        new_limit = max(0, old_limit - decrease)
        bot.reply_to(
            message,
            f"✅ **تم خصم {decrease} محاولة رفع من المستخدم** `{user_id}`\n📂 الحد القديم: {old_limit}\n📂 الحد الجديد: {new_limit}",
            parse_mode="Markdown"
        )
        try:
            bot.send_message(int(user_id), f"⚠️ **تم خصم {decrease} محاولة رفع من حسابك**\n📂 الحد الجديد: {new_limit} ملف")
        except:
            pass
    else:
        bot.reply_to(message, f"❌ المستخدم `{user_id}` غير موجود.", parse_mode="Markdown")
    del waiting_decrease_attempts_value[OWNER_ID]

@bot.callback_query_handler(func=lambda c: c.data == "ban_user_panel")
def callback_ban_user_panel(call):
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ هذه الخاصية للمالك فقط", show_alert=True)
        return
    waiting_ban_user[OWNER_ID] = True
    markup = cancel_markup()
    bot.edit_message_text(
        "🚫 **حظر مستخدم**\n\nأرسل معرف المستخدم (الآيدي):",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_ban_user)
def handle_ban_user_id(message):
    if message.text == "/cancel":
        del waiting_ban_user[OWNER_ID]
        bot.reply_to(message, "✅ تم إلغاء العملية")
        return
    user_id = message.text.strip()
    if db.is_banned(user_id):
        bot.reply_to(message, f"⚠️ المستخدم `{user_id}` محظور بالفعل.", parse_mode="Markdown")
    else:
        db.ban_user(user_id)
        bot.reply_to(message, f"✅ **تم حظر المستخدم** `{user_id}`", parse_mode="Markdown")
        try:
            bot.send_message(int(user_id), "🚫 **لقد تم حظرك من استخدام هذا البوت.**\nإذا كنت تعتقد أن هذا خطأ، تواصل مع المالك.")
        except:
            pass
    del waiting_ban_user[OWNER_ID]

@bot.callback_query_handler(func=lambda c: c.data == "unban_user_panel")
def callback_unban_user_panel(call):
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ هذه الخاصية للمالك فقط", show_alert=True)
        return
    waiting_unban_user[OWNER_ID] = True
    markup = cancel_markup()
    bot.edit_message_text(
        "✅ **إلغاء حظر مستخدم**\n\nأرسل معرف المستخدم (الآيدي):",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.chat.id == OWNER_ID and m.chat.id in waiting_unban_user)
def handle_unban_user_id(message):
    if message.text == "/cancel":
        del waiting_unban_user[OWNER_ID]
        bot.reply_to(message, "✅ تم إلغاء العملية")
        return
    user_id = message.text.strip()
    if not db.is_banned(user_id):
        bot.reply_to(message, f"⚠️ المستخدم `{user_id}` ليس محظوراً.", parse_mode="Markdown")
    else:
        db.unban_user(user_id)
        bot.reply_to(message, f"✅ **تم إلغاء حظر المستخدم** `{user_id}`", parse_mode="Markdown")
        try:
            bot.send_message(int(user_id), "✅ **تم إلغاء حظرك.** يمكنك الآن استخدام البوت مرة أخرى.")
        except:
            pass
    del waiting_unban_user[OWNER_ID]

# ================= معالج الأزرار الرئيسي =================
@bot.callback_query_handler(func=lambda c: c.data and "|" in c.data)
def handle_actions(call):
    try:
        parts = call.data.split("|")
        if len(parts) < 2:
            return
        action = parts[0]
        
        if action == "owner_start":
            if call.message.chat.id != OWNER_ID:
                bot.answer_callback_query(call.id, "❌ هذه الخاصية للمالك فقط", show_alert=True)
                return
            file_path = parts[1]
            db.enable_bot(file_path)
            db.manual_start_bot(file_path)
            proc, error = start_bot_process(file_path)
            if proc:
                bot.answer_callback_query(call.id, "✅ تم تشغيل البوت")
            else:
                bot.answer_callback_query(call.id, f"❌ فشل التشغيل", show_alert=True)
            owner_bots_list(call.message)
            return
        
        elif action == "owner_stop":
            if call.message.chat.id != OWNER_ID:
                bot.answer_callback_query(call.id, "❌ هذه الخاصية للمالك فقط", show_alert=True)
                return
            file_path = parts[1]
            stop_bot_process(file_path)
            db.disable_bot(file_path)
            bot.answer_callback_query(call.id, "✅ تم إيقاف البوت وتعطيله")
            owner_bots_list(call.message)
            return
        
        if len(parts) != 3:
            return
        
        action, user_id, rel_path = parts
        
        if str(call.message.chat.id) != user_id and call.message.chat.id != OWNER_ID:
            bot.answer_callback_query(call.id, "❌ هذا البوت ليس لك", show_alert=True)
            return
        
        if db.is_banned(call.message.chat.id) and call.message.chat.id != OWNER_ID:
            bot.answer_callback_query(call.id, "🚫 أنت محظور", show_alert=True)
            return
        
        base_folder = os.path.join(BOTS_DIR, user_id)
        full_path = os.path.abspath(os.path.join(base_folder, rel_path))
        
        if not os.path.exists(full_path):
            found = None
            for root, dirs, files in os.walk(base_folder):
                if os.path.basename(full_path) in files:
                    found = os.path.abspath(os.path.join(root, os.path.basename(full_path)))
                    break
            if found:
                full_path = found
            else:
                bot.answer_callback_query(call.id, "❌ الملف غير موجود", show_alert=True)
                return
        
        bot_data = db.get_bot_by_path(full_path)
        
        if action == "start":
            if bot_data and bot_data['disabled'] == 1 and call.message.chat.id != OWNER_ID:
                bot.answer_callback_query(call.id, "🚫 هذا البوت معطل من المالك", show_alert=True)
                return
            db.manual_start_bot(full_path)
            proc, error = start_bot_process(full_path)
            if proc:
                bot.answer_callback_query(call.id, "✅ تم التشغيل")
                bot.edit_message_text(
                    f"📄 **{os.path.basename(full_path)}**\n🟢 **شغال**",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown"
                )
            else:
                bot.answer_callback_query(call.id, "❌ فشل التشغيل", show_alert=True)
                bot.edit_message_text(
                    f"📄 **{os.path.basename(full_path)}**\n🔴 **فشل التشغيل**",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown"
                )
        
        elif action == "stop":
            stop_bot_process(full_path)
            db.manual_stop_bot(full_path)
            bot.answer_callback_query(call.id, "✅ تم الإيقاف")
            bot.edit_message_text(
                f"📄 **{os.path.basename(full_path)}**\n🔴 **متوقف (يدوي)**",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
        
        elif action == "delete":
            stop_bot_process(full_path)
            if os.path.exists(full_path):
                os.remove(full_path)
            db.delete_bot(full_path)
            bot.answer_callback_query(call.id, "🗑 تم الحذف نهائياً")
            bot.delete_message(call.message.chat.id, call.message.message_id)
        
        elif action == "token":
            waiting_token[call.message.chat.id] = full_path
            markup = cancel_markup()
            bot.send_message(
                call.message.chat.id,
                "🔑 **أرسل التوكن الجديد الآن**\n(أو استخدم زر الإلغاء)",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"⚠️ خطأ في معالج الأزرار: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ", show_alert=True)

# ================= استقبال التوكن الجديد =================
@bot.message_handler(func=lambda m: m.chat.id in waiting_token)
def set_new_token(message):
    if message.text == "/cancel":
        del waiting_token[message.chat.id]
        bot.reply_to(message, "✅ تم إلغاء تغيير التوكن")
        return
    path = waiting_token[message.chat.id]
    new_token = message.text.strip()
    if replace_token_in_file(path, new_token):
        stop_bot_process(path)
        db.manual_start_bot(path)
        proc, error = start_bot_process(path)
        if proc:
            bot.reply_to(message, "✅ **تم تغيير التوكن وإعادة تشغيل البوت بنجاح**", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"✅ تم تغيير التوكن لكن فشل التشغيل:\n`{error[:200]}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ فشل تعديل التوكن", parse_mode="Markdown")
    del waiting_token[message.chat.id]

# ================= أوامر عامة =================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.chat.id)
    
    # التحقق من وجود كود إحالة
    args = message.text.split()
    referred_by = None
    if len(args) > 1 and args[1].startswith('ref_'):
        ref_code = args[1][4:]
        referred_by = db.get_user_by_referral(ref_code)
        if referred_by == user_id:
            referred_by = None  # لا يمكن إحالة النفس
    
    # إضافة المستخدم إذا كان جديداً
    db.add_user(user_id, message.from_user.username, message.from_user.first_name, referred_by)
    
    if db.is_banned(user_id) and user_id != str(OWNER_ID):
        bot.send_message(message.chat.id, "🚫 **لقد تم حظرك من استخدام هذا البوت.**", parse_mode="Markdown")
        return
    
    if not check_subscription(message.chat.id) and user_id != str(OWNER_ID):
        markup = subscription_markup()
        bot.send_message(message.chat.id, "❌ **يجب الاشتراك في القنوات التالية أولاً:**", reply_markup=markup, parse_mode="Markdown")
        return
    
    if user_id != str(OWNER_ID) and not db.is_approved(user_id):
        db.add_pending_request(user_id, message.from_user.username, message.from_user.first_name, "طلب دخول")
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ موافقة", callback_data=f"approve|{user_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"reject|{user_id}")
        )
        user_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        caption = f"📢 **طلب استخدام جديد**\n\n👤 المستخدم: `{user_id}`\n📛 الاسم: {user_info}\n📁 عبر الأمر /start"
        try:
            bot.send_message(OWNER_ID, caption, reply_markup=markup, parse_mode="Markdown")
        except:
            pass
        bot.send_message(message.chat.id, "⏳ حسابك بانتظار موافقة المالك. سيتم إشعارك فور الموافقة.")
        return
    
    # محاولة استلام المكافأة اليومية تلقائياً عند /start (للمستخدمين العاديين فقط)
    reward_msg = ""
    if user_id != str(OWNER_ID):
        success, result = db.claim_daily_reward(user_id)
        if success:
            reward_msg = f"\n🎁 تم إضافة 20 نقطة مكافأة يومية! رصيدك الآن: {db.get_points(user_id)}"
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📂 بوتاتي", callback_data="mybots_callback"))
    if message.chat.id == OWNER_ID:
        markup.add(InlineKeyboardButton("👑 لوحة المالك", callback_data="panel"))
        markup.add(InlineKeyboardButton("📋 كل البوتات", callback_data="owner_bots_panel"))
    
    stats = db.get_user_stats(user_id) if user_id != str(OWNER_ID) else None
    if user_id == str(OWNER_ID):
        limit_text = "\n📂 الملفات المجانية: غير محدود (مالك)"
        points_text = "\n💰 نقاطك: غير محدود (مالك)"
    else:
        limit_text = f"\n📂 الملفات المجانية: `{max(0, stats['files_allowed'] - stats['files_uploaded'])}`" if stats else ""
        points_text = f"\n💰 نقاطك: `{stats['points']}`" if stats else ""
    
    welcome_msg = f"""
🚀 **بوت استضافة بوتات تلغرام المتطور**

📤 **أرسل ملف `.py` أو `.zip`** لرفع بوت جديد.
📂 استخدم /mybots لعرض وإدارة بوتاتك.
💰 استخدم /points لعرض رصيد نقاطك (للمستخدمين).
🎁 استخدم /daily للمكافأة اليومية (للمستخدمين).
🔗 استخدم /referral للحصول على رابط الإحالة.

━━━━━━━━━━━━━━━━━━
👤 معرفك: `{message.chat.id}`{limit_text}{points_text}{reward_msg}
"""
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "mybots_callback")
def callback_mybots(call):
    if db.is_banned(call.message.chat.id) and call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "🚫 أنت محظور.", show_alert=True)
        return
    my_bots(call.message)

@bot.message_handler(commands=["cancel"])
def cancel(message):
    user_id = message.chat.id
    cleared = False
    dictionaries = [
        waiting_token, waiting_main_file, waiting_channel, waiting_approval_limit,
        waiting_broadcast, waiting_edit_user_limit, waiting_edit_user_limit_value,
        waiting_add_attempts, waiting_add_attempts_value, waiting_decrease_attempts,
        waiting_decrease_attempts_value, waiting_ban_user, waiting_unban_user,
        waiting_set_points, waiting_set_points_value, waiting_add_points, waiting_add_points_value,
        waiting_set_file_cost
    ]
    for d in dictionaries:
        if user_id in d:
            del d[user_id]
            cleared = True
    if cleared:
        bot.reply_to(message, "✅ تم إلغاء العملية/العمليات الجارية.")
    else:
        bot.reply_to(message, "ℹ️ لا توجد عملية جارية حالياً.")

# ================= تشغيل البوت =================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 بوت الاستضافة المتطور - بدون كشف البوتات الضارة + تمييز المالك")
    print("=" * 60)
    print(f"👤 معرف المالك: {OWNER_ID}")
    print(f"📁 المسار الأساسي: {BASE_DIR}")
    print(f"💾 قاعدة البيانات: {DB_FILE}")
    print(f"📂 مجلد البوتات: {BOTS_DIR}")
    print("=" * 60)
    
    stats_data = db.get_stats()
    print(f"📊 إحصائيات قاعدة البيانات:")
    print(f"   • مستخدمين: {stats_data['approved_users']}")
    print(f"   • بوتات: {stats_data['total_bots']}")
    print(f"   • طلبات: {stats_data['pending_requests']}")
    print(f"   • قنوات: {stats_data['channels_count']}")
    print(f"   • إجمالي النقاط: {stats_data['total_points']}")
    print("=" * 60)
    
    count = start_all_bots()
    print(f"🔄 تم تشغيل {count} بوت تلقائياً")
    print("=" * 60)
    print("✅ البوت شغال...")
    print("=" * 60)
    
    try:
        bot.polling(none_stop=True, interval=1, timeout=30)
    except Exception as e:
        print(f"❌ خطأ في البوت: {e}")
        time.sleep(5)
        bot.polling(none_stop=True, interval=1, timeout=30)
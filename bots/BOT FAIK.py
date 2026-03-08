#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت التشفير وفك التشفير المتطور
يدعم 10+ طرق تشفير، وفك تشفير متكرر ذكي
المطور: @mhand26
"""

import os
import base64
import marshal
import zlib
import lzma
import bz2
import dis
import io
import re
import sys
import json
import codecs
import binascii
import time
import difflib
import traceback
import hashlib
from datetime import datetime

import telebot
from telebot import types

# محاولة استيراد requests (اختياري)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ========== التوكن والإعدادات ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8349306836:AAHnCXYq7itpRvtkWADIMtBzRZfjYUOGIaY")
bot = telebot.TeleBot(BOT_TOKEN)

# مجلدات مؤقتة
os.makedirs("temp", exist_ok=True)

# إعدادات فك التشفير
MAX_RECURSION = 30
SIMILARITY_THRESHOLD = 0.95

# حالة المستخدمين (أي وضع هم فيه)
USER_STATE = {}  # chat_id -> 'encrypt' أو 'decrypt' أو None
USER_ENCRYPT_CHOICE = {}  # chat_id -> طريقة التشفير المختارة

# ========== دوال التشفير (من الكود القديم) ==========

def encrypt_base64(content):
    return base64.b64encode(content.encode()).decode()

def encrypt_base64_reverse(content):
    return base64.b64encode(content.encode())[::-1].decode()

def encrypt_zlib(content):
    return zlib.compress(content.encode())

def encrypt_marshal(content):
    return marshal.dumps(compile(content, '<string>', 'exec'))

def encrypt_lzma(content):
    return lzma.compress(content.encode())

def encrypt_bz2(content):
    return bz2.compress(content.encode())

def encrypt_json(content):
    return json.dumps(content)

def encrypt_rot13(content):
    return codecs.encode(content, 'rot_13')

def encrypt_hex(content):
    return content.encode().hex()

# ========== دوال فك التشفير (مطورة) ==========

def decrypt_base64(content):
    # البحث عن أي base64 داخل النص
    pattern = r'[\'\"]([A-Za-z0-9+/=]{20,})[\'\"]'
    match = re.search(pattern, content)
    if match:
        try:
            return base64.b64decode(match.group(1)).decode('utf-8')
        except:
            pass
    return None

def decrypt_base64_reverse(content):
    # النمط القديم: exec((_)(b64string))
    match = re.search(r'exec\(\(_\)\(([^)]+)\)\)', content)
    if match:
        try:
            encoded = eval(match.group(1))
            return base64.b64decode(encoded[::-1]).decode('utf-8')
        except:
            pass
    return None

def decrypt_zlib(content):
    match = re.search(r'zlib\.decompress\(([^)]+)\)', content)
    if match:
        try:
            data = eval(match.group(1))
            return zlib.decompress(data).decode('utf-8')
        except:
            pass
    return None

def decrypt_marshal(content):
    match = re.search(r'marshal\.loads\(([^)]+)\)', content)
    if match:
        try:
            marshal_bytes = eval(match.group(1))
            code_obj = marshal.loads(marshal_bytes)
            out = io.StringIO()
            dis.dis(code_obj, file=out)
            return "# (تم فك Marshal جزئياً)\n" + out.getvalue()
        except:
            pass
    return None

def decrypt_lzma(content):
    match = re.search(r'lzma\.decompress\(([^)]+)\)', content)
    if match:
        try:
            data = eval(match.group(1))
            return lzma.decompress(data).decode('utf-8')
        except:
            pass
    return None

def decrypt_bz2(content):
    match = re.search(r'bz2\.decompress\(([^)]+)\)', content)
    if match:
        try:
            data = eval(match.group(1))
            return bz2.decompress(data).decode('utf-8')
        except:
            pass
    return None

def decrypt_json(content):
    match = re.search(r'json\.loads\(([^)]+)\)', content)
    if match:
        try:
            return json.loads(eval(match.group(1)))
        except:
            pass
    return None

def decrypt_rot13(content):
    match = re.search(r'codecs\.decode\([\'\"](.+?)[\'\"], [\'\"]rot_13[\'\"]\)', content)
    if match:
        try:
            return codecs.decode(match.group(1), 'rot_13')
        except:
            pass
    return None

def decrypt_hex(content):
    match = re.search(r'bytes\.fromhex\([\'\"]([0-9a-fA-F]+)[\'\"]\)', content)
    if match:
        try:
            return bytes.fromhex(match.group(1)).decode('utf-8')
        except:
            pass
    return None

# قاموس طرق فك التشفير (للتكرار)
DECRYPTORS = [
    ("base64 عادي", decrypt_base64),
    ("base64 معكوس", decrypt_base64_reverse),
    ("zlib", decrypt_zlib),
    ("marshal", decrypt_marshal),
    ("lzma", decrypt_lzma),
    ("bz2", decrypt_bz2),
    ("json", decrypt_json),
    ("rot13", decrypt_rot13),
    ("hex", decrypt_hex),
]

# ========== دالة التشابه ==========
def similarity(a, b):
    if not a or not b:
        return 0
    return difflib.SequenceMatcher(None, a, b).ratio()

# ========== فك التشفير المتكرر الذكي ==========
def recursive_decrypt(content, depth=0, history=None, seen=None):
    if history is None:
        history = []
    if seen is None:
        seen = set()
    
    if depth >= MAX_RECURSION:
        history.append("⚠️ توقف: الحد الأقصى للتكرار")
        return content, history
    
    # تجنب الدوران
    h = hashlib.md5(content.encode()).hexdigest()
    if h in seen:
        history.append("⏹️ توقف: دورة تكرار")
        return content, history
    seen.add(h)
    
    for name, func in DECRYPTORS:
        try:
            result = func(content)
            if result and isinstance(result, str) and len(result) > 20:
                sim = similarity(content, result)
                if sim < SIMILARITY_THRESHOLD and len(result) < len(content) * 3:
                    history.append(name)
                    return recursive_decrypt(result, depth+1, history, seen)
        except Exception as e:
            continue
    
    return content, history

# ========== معالجة ملفات .pyc ==========
def process_pyc(file_path):
    with open(file_path, 'rb') as f:
        magic = f.read(4)
        if sys.version_info >= (3, 7):
            f.read(12)
        else:
            f.read(8)
        try:
            code_obj = marshal.load(f)
            out = io.StringIO()
            dis.dis(code_obj, file=out)
            return out.getvalue()
        except:
            return "# فشل تحميل pyc"

# ========== رفع الملفات الكبيرة (اختياري) ==========
def upload_to_gofile(file_path):
    if not REQUESTS_AVAILABLE:
        return None
    try:
        server_resp = requests.get('https://api.gofile.io/getServer')
        if server_resp.status_code != 200:
            return None
        server = server_resp.json()['data']['server']
        with open(file_path, 'rb') as f:
            upload_resp = requests.post(
                f'https://{server}.gofile.io/uploadFile',
                files={'file': f}
            )
        if upload_resp.status_code == 200:
            data = upload_resp.json()
            if data['status'] == 'ok':
                return data['data']['downloadPage']
    except:
        pass
    return None

# ========== أوامر البوت ==========

@bot.message_handler(commands=['start'])
def start(message):
    """القائمة الرئيسية"""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔐 تشفير", callback_data="mode_encrypt"),
        types.InlineKeyboardButton("🔓 فك تشفير", callback_data="mode_decrypt")
    )
    bot.send_message(
        message.chat.id,
        "<b>مرحباً بك في بوت التشفير المتطور</b>\n\n"
        "اختر الوضع الذي تريده:",
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "mode_encrypt":
        # عرض طرق التشفير
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            types.InlineKeyboardButton("Base64 عادي", callback_data="enc_base64"),
            types.InlineKeyboardButton("Base64 معكوس", callback_data="enc_base64_rev"),
            types.InlineKeyboardButton("Zlib", callback_data="enc_zlib"),
            types.InlineKeyboardButton("Marshal", callback_data="enc_marshal"),
            types.InlineKeyboardButton("LZMA", callback_data="enc_lzma"),
            types.InlineKeyboardButton("Bz2", callback_data="enc_bz2"),
            types.InlineKeyboardButton("JSON", callback_data="enc_json"),
            types.InlineKeyboardButton("ROT13", callback_data="enc_rot13"),
            types.InlineKeyboardButton("Hex", callback_data="enc_hex"),
        ]
        markup.add(*buttons)
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        bot.edit_message_text(
            "اختر طريقة التشفير:",
            chat_id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
        USER_STATE[chat_id] = "encrypt"

    elif data.startswith("enc_"):
        method = data.replace("enc_", "")
        USER_ENCRYPT_CHOICE[chat_id] = method
        bot.edit_message_text(
            f"تم اختيار <b>{method}</b>\n"
            "أرسل ملف `.py` لتشفيره.",
            chat_id,
            call.message.message_id,
            parse_mode="HTML"
        )
        # البوت سينتظر الملف في الدالة handle_document

    elif data == "mode_decrypt":
        USER_STATE[chat_id] = "decrypt"
        bot.edit_message_text(
            "🔓 أرسل لي ملف `.py` أو `.pyc` مشفر وسأقوم بفك تشفيره.",
            chat_id,
            call.message.message_id,
            parse_mode="HTML"
        )

    elif data == "back_main":
        USER_STATE.pop(chat_id, None)
        USER_ENCRYPT_CHOICE.pop(chat_id, None)
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🔐 تشفير", callback_data="mode_encrypt"),
            types.InlineKeyboardButton("🔓 فك تشفير", callback_data="mode_decrypt")
        )
        bot.edit_message_text(
            "القائمة الرئيسية:",
            chat_id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )

# ========== معالج الملفات ==========

@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    file_name = message.document.file_name or "unknown"
    ext = os.path.splitext(file_name)[1].lower()

    # التحقق من حالة المستخدم
    state = USER_STATE.get(chat_id)
    if not state:
        bot.reply_to(
            message,
            "⚠️ لم تختار وضعاً بعد. أرسل /start للبدء.",
            parse_mode="HTML"
        )
        return

    processing = bot.reply_to(message, "⏳ جاري المعالجة...")

    temp_input = f"temp/input_{user_id}_{int(time.time())}"
    temp_output = None

    try:
        # تحميل الملف
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        with open(temp_input, 'wb') as f:
            f.write(downloaded)

        if state == "encrypt":
            # ========== التشفير ==========
            method = USER_ENCRYPT_CHOICE.get(chat_id)
            if not method:
                bot.edit_message_text(
                    "❌ لم يتم اختيار طريقة تشفير. حاول مرة أخرى.",
                    chat_id,
                    processing.message_id
                )
                return

            # قراءة محتوى الملف
            try:
                with open(temp_input, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                with open(temp_input, 'r', encoding='latin-1') as f:
                    content = f.read()

            # تطبيق التشفير
            if method == "base64":
                encrypted = base64.b64encode(content.encode()).decode()
                result = f"# مشفر بـ Base64\n{encrypted}"
            elif method == "base64_rev":
                encrypted = base64.b64encode(content.encode())[::-1].decode()
                result = f"import base64\nexec(base64.b64decode('{encrypted}'[::-1]))"
            elif method == "zlib":
                compressed = zlib.compress(content.encode())
                result = f"import zlib\nexec(zlib.decompress({compressed!r}))"
            elif method == "marshal":
                code_obj = compile(content, '<string>', 'exec')
                marshalled = marshal.dumps(code_obj)
                result = f"import marshal\nexec(marshal.loads({marshalled!r}))"
            elif method == "lzma":
                compressed = lzma.compress(content.encode())
                result = f"import lzma\nexec(lzma.decompress({compressed!r}))"
            elif method == "bz2":
                compressed = bz2.compress(content.encode())
                result = f"import bz2\nexec(bz2.decompress({compressed!r}))"
            elif method == "json":
                result = f"import json\nexec(json.loads({json.dumps(content)!r}))"
            elif method == "rot13":
                encoded = codecs.encode(content, 'rot_13')
                result = f"import codecs\nexec(codecs.decode({repr(encoded)}, 'rot_13'))"
            elif method == "hex":
                encoded = content.encode().hex()
                result = f"exec(bytes.fromhex({repr(encoded)}).decode())"
            else:
                result = "# طريقة غير معروفة"

            # حفظ الملف المشفر
            temp_output = f"temp/encrypted_{user_id}_{int(time.time())}.py"
            with open(temp_output, 'w', encoding='utf-8') as f:
                f.write(result)

            bot.edit_message_text(
                f"✅ تم تشفير الملف بطريقة <b>{method}</b>",
                chat_id,
                processing.message_id,
                parse_mode="HTML"
            )

        elif state == "decrypt":
            # ========== فك التشفير ==========
            if ext == '.pyc':
                decrypted = process_pyc(temp_input)
                history = ["pyc_disassembly"]
            else:
                # قراءة المحتوى
                with open(temp_input, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                # فك التشفير المتكرر
                decrypted, history = recursive_decrypt(content)

            temp_output = f"temp/decoded_{user_id}_{int(time.time())}.py"
            with open(temp_output, 'w', encoding='utf-8') as f:
                f.write(decrypted)

            # إعداد تقرير HTML
            report = "<b>🔓 تقرير فك التشفير</b>\n\n"
            report += f"📁 الملف: {file_name}\n"
            if history:
                report += "\n<b>خطوات فك التشفير:</b>\n"
                for i, step in enumerate(history, 1):
                    report += f"{i}. {step}\n"
            else:
                report += "\nلم يتم تطبيق أي فك تشفير.\n"

            bot.edit_message_text(report, chat_id, processing.message_id, parse_mode="HTML")

        # إرسال الملف الناتج
        if temp_output:
            file_size = os.path.getsize(temp_output)
            if file_size > 50 * 1024 * 1024 and REQUESTS_AVAILABLE:
                bot.send_message(chat_id, "📤 الملف كبير جداً، جاري الرفع إلى gofile.io...")
                link = upload_to_gofile(temp_output)
                if link:
                    bot.send_message(chat_id, f"📥 رابط التحميل: {link}")
                else:
                    bot.send_document(chat_id, open(temp_output, 'rb'))
            else:
                with open(temp_output, 'rb') as f:
                    bot.send_document(chat_id, f, reply_to_message_id=message.message_id)

    except Exception as e:
        bot.edit_message_text(
            f"❌ حدث خطأ: <code>{str(e)}</code>",
            chat_id,
            processing.message_id,
            parse_mode="HTML"
        )
        traceback.print_exc()
    finally:
        # تنظيف الملفات المؤقتة
        for f in [temp_input, temp_output] if temp_output else [temp_input]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except:
                pass

# ========== تشغيل البوت ==========
if __name__ == "__main__":
    print("🔥 بوت التشفير وفك التشفير المتطور يعمل...")
    bot.infinity_polling()
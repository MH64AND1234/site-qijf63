import os
import re
import struct
import json
import time
from io import BytesIO
from typing import Dict, List, Tuple, Optional

import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= الإعدادات الثابتة =================
BOT_TOKEN = "8348435278:AAE1wXi7QOCUHoRgHnIdxfkLEHQwukFmtg0"
BOT_OWNER_ID = 6550748735  # ضع هنا معرف المالك (رقمي)
DEFAULT_MAX_FILES = 1
DB_FILE = "users_db.json"

# ================= إدارة قاعدة البيانات (JSON) =================
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def get_user_data(user_id: int) -> dict:
    db = load_db()
    user_id_str = str(user_id)
    if user_id_str not in db:
        db[user_id_str] = {
            "approved": False,
            "file_count": 0,
            "max_files": DEFAULT_MAX_FILES
        }
        save_db(db)
    else:
        # تأكد من وجود جميع المفاتيح
        changed = False
        if "approved" not in db[user_id_str]:
            db[user_id_str]["approved"] = False
            changed = True
        if "file_count" not in db[user_id_str]:
            db[user_id_str]["file_count"] = 0
            changed = True
        if "max_files" not in db[user_id_str]:
            db[user_id_str]["max_files"] = DEFAULT_MAX_FILES
            changed = True
        if changed:
            save_db(db)
    return db[user_id_str]

def update_user_data(user_id: int, approved: bool = None, file_count: int = None, max_files: int = None):
    db = load_db()
    user_id_str = str(user_id)
    if user_id_str not in db:
        db[user_id_str] = {
            "approved": False,
            "file_count": 0,
            "max_files": DEFAULT_MAX_FILES
        }
    if approved is not None:
        db[user_id_str]["approved"] = approved
    if file_count is not None:
        db[user_id_str]["file_count"] = file_count
    if max_files is not None:
        db[user_id_str]["max_files"] = max_files
    save_db(db)

def increment_file_count(user_id: int):
    data = get_user_data(user_id)
    data["file_count"] += 1
    update_user_data(user_id, file_count=data["file_count"])

def get_user_max_files(user_id: int) -> int:
    data = get_user_data(user_id)
    return data.get("max_files", DEFAULT_MAX_FILES)

# ================= ELF UTILS =================
def safe_unpack(fmt, data, offset):
    size = struct.calcsize(fmt)
    if offset + size > len(data):
        raise ValueError
    return struct.unpack(fmt, data[offset:offset+size])

def get_section_name(offset, elf_data, shstr_offset):
    name = b""
    while shstr_offset + offset < len(elf_data) and elf_data[shstr_offset + offset] != 0:
        name += bytes([elf_data[shstr_offset + offset]])
        offset += 1
    return name.decode(errors="ignore")

def extract_text_section(elf_data):
    is_64 = elf_data[4] == 2
    try:
        if is_64:
            sh_off = safe_unpack("<Q", elf_data, 0x28)[0]
            sh_sz  = safe_unpack("<H", elf_data, 0x3A)[0]
            sh_num = safe_unpack("<H", elf_data, 0x3C)[0]
            sh_str = safe_unpack("<H", elf_data, 0x3E)[0]
            shstr  = safe_unpack("<Q", elf_data, sh_off + sh_str * sh_sz + 0x18)[0]
        else:
            sh_off = safe_unpack("<I", elf_data, 0x20)[0]
            sh_sz  = safe_unpack("<H", elf_data, 0x2E)[0]
            sh_num = safe_unpack("<H", elf_data, 0x30)[0]
            sh_str = safe_unpack("<H", elf_data, 0x32)[0]
            shstr  = safe_unpack("<I", elf_data, sh_off + sh_str * sh_sz + 0x14)[0]
    except:
        return None, None

    for i in range(sh_num):
        off = sh_off + i * sh_sz
        try:
            if is_64:
                sh_name = safe_unpack("<I", elf_data, off)[0]
                sh_addr = safe_unpack("<Q", elf_data, off+0x10)[0]
                sh_ofs  = safe_unpack("<Q", elf_data, off+0x18)[0]
                sh_size = safe_unpack("<Q", elf_data, off+0x20)[0]
            else:
                sh_name = safe_unpack("<I", elf_data, off)[0]
                sh_addr = safe_unpack("<I", elf_data, off+0x0C)[0]
                sh_ofs  = safe_unpack("<I", elf_data, off+0x10)[0]
                sh_size = safe_unpack("<I", elf_data, off+0x14)[0]

            if get_section_name(sh_name, elf_data, shstr) == ".text":
                return sh_addr, elf_data[sh_ofs:sh_ofs+sh_size]
        except:
            continue
    return None, None

# ================= STRINGS (موسعة) =================
protection_strings = {
    "report": "يحصل بيانات تقارير الغش",   
    "SDK": "خاص بل UE4",   
    "TSS": "تحقق سلامة البيانات",
    "log_print": "يحمي من تسجيل أحداث الغش",
    "cacheflush": "يعطل تنظيف الكاش المرتبط بالحماية",
    "mmap": "إدارة ذاكرة حساسة",
    "open": "منع فتح ملفات SDK الحساسة",
    "CrashReport": "منع إرسال تقارير الكراش",
    "SendUnityBuffer": "يمنع إرسال بيانات اللاعبين",
    "SendUnityResult": "يمنع إرسال نتائج العمليات",
    "RiskControl": "يحمي من باند تلقائي أو flagged",
    "flagged": "يحمي من وضع الحساب معلق",
    "Your account has been flagged": "يحمي من رسالة حظر الحساب",
    "getnameinfo": "يعطل جمع معلومات الشبكة",
    "recv": "يعطل استقبال بيانات الشبكة",
    "recvfrom": "يعطل استقبال UDP",
    "send": "يعطل إرسال بيانات الشبكة المهمة",
    "sendto": "يعطل إرسال UDP",
    "gcloud_account_login": "يحمي من تسجيل دخول حساب GCloud",
    "SendUnityMessage": "يحمي من إرسال رسائل Unity",
    "UnitySendMessage": "يحمي من إرسال رسائل Unity",
    "GCloudLog": "يحمي من تسجيل أحداث على السيرفر",
    "ReportUpload": "يحمي من رفع تقارير اللاعبين",
    "report_id": "يحمي معرف التقارير",
    "device_id": "يحمي معرف الجهاز لمنع باند دائم",
    "send_packet": "يحمي من إرسال باكيت حساس",
    "recv_packet": "يحمي من استقبال باكيت حساس",
    "risk_level": "يحمي من تقييم المخاطر و flagged",
    "report_upload_finish": "يحمي من إنهاء رفع التقرير وإرسال البيانات",
    "writeLogToFile": "يكتب سجل الأحداث إلى ملف محلي",
    "sendLogToServer": "يرسل السجلات التفصيلية إلى السيرفر",
    "uploadCrashLog": "يرفع سجل حدوث الكراش إلى السيرفر للتحليل",
    "deviceinfo": "معلومات الجهاز الحساسة (IMEI، AndroidID، طراز...)",
    "risk_flag": "علم/علمة تقييم المخاطر (flagged) على الحساب",
    "Http": "مؤشرات/نداءات متعلقة باتصالات HTTPS الآمنة",
    "SendToServer": "دالة عامة لإرسال بيانات أو لوج إلى السيرفر",
    "uploadlog": "رفع السجلات (log upload) إلى مخدم الحدود",     
    "gettimeofday": "منع باند اليوم" 
}

activation_strings = {
    "Aimbot": "ايم بوت",
    "NoRecoil": "ازالة الارتداد",
    "Recoil": "ارتداد",
    "Stability": "ثبات السلاح",
    "ESP": "اظهار اللاعبين",
    "ESP_Line": "خطوط ESP",
    "ESP_Box": "مربعات ESP",
    "ESP_Health": "دم اللاعب",
    "ESP_Distance": "مسافة ESP",
    "ESP_Name": "أسماء ESP",
    "Radar": "رادار",
    "RadarHack": "رادار هاك",
    "MagicBullet": "رصاص سحري",
    "BulletTracking": "تتبع الرصاص",
    "Headshot": "هيد شوت",
    "HeadshotOnly": "هيد شوت فقط",
    "AntiShake": "منع الاهتزاز",
    "NoSpread": "بدون تشتت",
    "NoSway": "بدون تمايل",
    "Fov": "توسيع الزاوية",
    "FovChanger": "تغيير مجال الرؤية",
    "AutoFire": "اطلاق تلقائي",
    "AutoShoot": "تصويب تلقائي",
    "TriggerBot": "تريقر بوت",
    "Wallhack": "وول هاك",
    "Chams": "شامس",
    "Glow": "توهج",
    "GodMode": "وضع الإله",
    "InfiniteAmmo": "ذخيرة لا نهائية",
    "RapidFire": "اطلاق سريع",
    "SpeedHack": "سرعة حركة",
    "FlyHack": "طيران",
    "JumpHack": "قفز عالي",
    "NoClip": "اختراق الجدران",
    "UnlimitedHealth": "صحة لا نهائية",
    "UnlimitedShield": "درع لا نهائي",
    "AntiBan": "منع الحظر",
    "AntiFlag": "منع العلم",
}

sub_bin = re.compile(rb'sub_[0-9A-Fa-f]+')
sub_txt = re.compile(r'sub_[0-9A-Fa-f]+')

SEARCH_RANGE = 500

# ================= دوال المساعدة لتوليد ملفات بايثون =================
def generate_py_from_lines(lines: List[str], lib_name: str, description: str = "") -> str:
    py_lines = ["# -*- coding: utf-8 -*-", f"# {description}", "# Auto-generated patches\n"]
    for line in lines:
        if "➜" in line:
            parts = line.split("➜", 1)
            offset = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ""
            py_lines.append(f"# {desc}")
            py_lines.append(f'PATCH_LIB("{lib_name}", "{offset}", "00 20 70 47");\n')
        else:
            py_lines.append(f"# {line}")
    return "\n".join(py_lines)

def generate_py_from_patch_lines(patch_lines: List[str], lib_name: str, description: str = "") -> str:
    py_lines = ["# -*- coding: utf-8 -*-", f"# {description}", "# Auto-generated patches\n"]
    py_lines.extend(patch_lines)
    return "\n".join(py_lines)

# ================= Processing functions =================
def process_protection(file_data: bytes, filename: str, lib_name: str) -> Tuple[str, str]:
    ext = os.path.splitext(filename)[1].lower()
    results = []
    if ext == ".so":
        base, text = extract_text_section(file_data)
        if base is None:
            return "❌ لم أتمكن من استخراج مقطع .text من ملف ELF.", ""
        for s, d in protection_strings.items():
            for m in re.finditer(s.encode(), text):
                start = m.start()
                sub = sub_bin.search(text[start:start+SEARCH_RANGE])
                if sub:
                    off = hex(base + start + sub.start())
                    results.append(f"{off} ➜ {d}")
    else:
        try:
            data = file_data.decode('utf-8', errors='ignore')
        except:
            return "❌ لا يمكن فك ترميز الملف كنص.", ""
        for s, d in protection_strings.items():
            for m in re.finditer(s, data):
                start = m.start()
                sub = sub_txt.search(data[start:start+SEARCH_RANGE])
                if sub:
                    off = "0x" + sub.group().replace("sub_", "")
                    results.append(f"{off} ➜ {d}")

    if not results:
        return "لم يتم العثور على أي نتائج.", ""

    result_text = "\n".join(results)
    python_content = generate_py_from_lines(results, lib_name, "Protection Offsets")
    return result_text, python_content

def process_custom_strings(file_data: bytes, filename: str, lib_name: str, custom_dict: Dict[str,str]) -> Tuple[str, str]:
    ext = os.path.splitext(filename)[1].lower()
    results = []
    if ext == ".so":
        base, text = extract_text_section(file_data)
        if base is None:
            return "❌ لم أتمكن من استخراج مقطع .text من ملف ELF.", ""
        for s, d in custom_dict.items():
            for m in re.finditer(s.encode(), text):
                start = m.start()
                sub = sub_bin.search(text[start:start+SEARCH_RANGE])
                if sub:
                    off = hex(base + start + sub.start())
                    results.append(f"{off} ➜ {d}")
    else:
        try:
            data = file_data.decode('utf-8', errors='ignore')
        except:
            return "❌ لا يمكن فك ترميز الملف كنص.", ""
        for s, d in custom_dict.items():
            for m in re.finditer(s, data):
                start = m.start()
                sub = sub_txt.search(data[start:start+SEARCH_RANGE])
                if sub:
                    off = "0x" + sub.group().replace("sub_", "")
                    results.append(f"{off} ➜ {d}")

    if not results:
        return "لم يتم العثور على أي نتائج.", ""

    result_text = "\n".join(results)
    python_content = generate_py_from_lines(results, lib_name, "Custom Strings Offsets")
    return result_text, python_content

def process_patch_extract(file_data: bytes, filename: str, lib_name: str) -> Tuple[str, str]:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".so":
        return "❌ الوضع الثالث يعمل فقط على الملفات النصية (.c/.lst).", ""
    try:
        data = file_data.decode('utf-8', errors='ignore')
    except:
        return "❌ لا يمكن فك ترميز الملف كنص.", ""
    subs = sorted(set(re.findall(r'sub_([0-9A-Fa-f]+)', data)))
    if not subs:
        return "لم يتم العثور على دوال sub_.", ""
    lines = []
    for s in subs:
        lines.append(f'PATCH_LIB("{lib_name}","0x{s}","00 20 70 47");')
    result_text = "\n".join(lines)
    python_content = generate_py_from_patch_lines(lines, lib_name, "Sub_ functions patches")
    return result_text, python_content

def process_activation(file_data: bytes, filename: str, lib_name: str) -> Tuple[str, str, str]:
    ext = os.path.splitext(filename)[1].lower()
    results = []
    if ext == ".so":
        base, text = extract_text_section(file_data)
        if base is None:
            return "❌ لم أتمكن من استخراج مقطع .text من ملف ELF.", "", ""
        for key, typ in activation_strings.items():
            for m in re.finditer(key.encode(), text):
                start = m.start()
                sub = sub_bin.search(text[start:start+SEARCH_RANGE])
                if sub:
                    off = hex(base + start + sub.start())
                    results.append((typ, off))
    else:
        try:
            data = file_data.decode('utf-8', errors='ignore')
        except:
            return "❌ لا يمكن فك ترميز الملف كنص.", "", ""
        for key, typ in activation_strings.items():
            for m in re.finditer(key, data, re.IGNORECASE):
                start = m.start()
                sub = sub_txt.search(data[start:start+SEARCH_RANGE])
                if sub:
                    off = "0x" + sub.group().replace("sub_", "")
                    results.append((typ, off))

    results = list(dict.fromkeys(results))

    offsets_lines = [f"{o} ➜ {t}" for t, o in results]
    offsets_text = "\n".join(offsets_lines) if offsets_lines else "لم يتم العثور على نتائج."

    codes_lines = []
    for t, o in results:
        codes_lines.append(f"// {t}")
        codes_lines.append(f'PATCH_LIB("{lib_name}","{o}","00 20 70 47");\n')
    codes_text = "\n".join(codes_lines) if codes_lines else "لم يتم العثور على نتائج."

    py_lines = ["# -*- coding: utf-8 -*-", "# Activation Offsets and Patches", ""]
    for t, o in results:
        py_lines.append(f"# {t} : {o}")
        py_lines.append(f'PATCH_LIB("{lib_name}","{o}","00 20 70 47");\n')
    python_content = "\n".join(py_lines) if results else ""

    return offsets_text, codes_text, python_content

# ================= إنشاء البوت =================
bot = telebot.TeleBot(BOT_TOKEN)

# تخزين مؤقت لحالة المستخدمين (لجلسة العمل)
user_sessions = {}  # key: user_id, value: dict

# ================= معالج الأوامر =================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    if user_id == BOT_OWNER_ID:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔐 قسم الحماية", callback_data="protection_section"))
        markup.add(InlineKeyboardButton("👑 قسم المالك", callback_data="owner_section"))
        bot.send_message(user_id, "🤖 *مرحباً بك يا مالك البوت*\nاختر القسم الذي تريد:",
                         reply_markup=markup, parse_mode="Markdown")
    else:
        if user_data["approved"]:
            if user_data["file_count"] >= user_data["max_files"]:
                bot.send_message(user_id, f"⚠️ لقد تجاوزت الحد الأقصى المسموح به ({user_data['max_files']} ملفات). لا يمكنك استخدام البوت أكثر.")
                return
            # دخول مباشر لقسم الحماية
            protection_menu(message)
        else:
            # طلب موافقة المالك
            user = message.from_user
            mention = f"@{user.username}" if user.username else f"المستخدم"
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("✅ موافقة", callback_data=f"approve:yes:{user.id}"),
                       InlineKeyboardButton("❌ رفض", callback_data=f"approve:no:{user.id}"), row_width=2)
            bot.send_message(BOT_OWNER_ID,
                             f"📩 طلب استخدام البوت من:\n"
                             f"الاسم: {user.full_name}\n"
                             f"المعرف: {mention}\n"
                             f"الآيدي: <code>{user.id}</code>\n"
                             f"الرابط: tg://user?id={user.id}",
                             reply_markup=markup, parse_mode="HTML")
            bot.send_message(user_id, "⏳ تم إرسال طلبك إلى المالك. انتظر الموافقة.\nسيتم إعلامك عندما يوافق المالك.")

def protection_menu(message):
    user_id = message.from_user.id
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔐 1 - استخراج أوفستات الحماية", callback_data="mode1"))
    markup.add(InlineKeyboardButton("📝 2 - سلاسل نصية مخصصة", callback_data="mode2"))
    markup.add(InlineKeyboardButton("🔧 3 - استخراج sub_ وإنشاء أكواد PATCH", callback_data="mode3"))
    markup.add(InlineKeyboardButton("⚡ 4 - استخراج أوفستات التفعيلات + أكواد", callback_data="mode4"))
    markup.add(InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main"))
    bot.send_message(user_id, "🔐 *قسم الحماية*\nاختر الوضع الذي تريد:",
                     reply_markup=markup, parse_mode="Markdown")

# ================= معالج الكول باك =================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    data = call.data

    if data == "protection_section":
        if user_id == BOT_OWNER_ID:
            protection_menu(call.message)
        else:
            user_data = get_user_data(user_id)
            if user_data["approved"]:
                protection_menu(call.message)
            else:
                bot.answer_callback_query(call.id, "غير مصرح لك", show_alert=True)
    elif data == "owner_section":
        if user_id != BOT_OWNER_ID:
            bot.answer_callback_query(call.id, "هذا القسم للمالك فقط", show_alert=True)
            return
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📋 عرض جميع المستخدمين", callback_data="owner:list"))
        markup.add(InlineKeyboardButton("🔍 معلومات مستخدم", callback_data="owner:info"))
        markup.add(InlineKeyboardButton("📈 تغيير حد المستخدم", callback_data="owner:setlimit"))
        markup.add(InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main"))
        bot.edit_message_text("👑 *قسم المالك*\nاختر ما تريد:", chat_id=user_id, message_id=call.message.message_id,
                              reply_markup=markup, parse_mode="Markdown")
    elif data == "back_to_main":
        # العودة للقائمة الرئيسية
        if user_id == BOT_OWNER_ID:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔐 قسم الحماية", callback_data="protection_section"))
            markup.add(InlineKeyboardButton("👑 قسم المالك", callback_data="owner_section"))
            bot.edit_message_text("🤖 *مرحباً بك يا مالك البوت*\nاختر القسم الذي تريد:",
                                  chat_id=user_id, message_id=call.message.message_id,
                                  reply_markup=markup, parse_mode="Markdown")
        else:
            start(call.message)
    elif data.startswith("mode"):
        # حفظ الوضع مؤقتاً
        user_sessions[user_id] = {'mode': data}
        if data == "mode2":
            bot.edit_message_text("📁 *الوضع الثاني: سلاسل نصية مخصصة*\n\n"
                                  "الرجاء إرسال ملف نصي (txt) يحتوي في كل سطر على:\n"
                                  "`النص:الوصف`\n\n"
                                  "مثال:\n"
                                  "```\n"
                                  "checkLicense:التحقق من الترخيص\n"
                                  "sendData:إرسال البيانات\n"
                                  "```\n"
                                  "يمكنك استخدام # للتعليقات.",
                                  chat_id=user_id, message_id=call.message.message_id,
                                  parse_mode="Markdown")
            bot.register_next_step_handler(call.message, handle_custom_strings_file)
        else:
            bot.edit_message_text(f"✅ تم اختيار الوضع {data[-1]}.\n\n"
                                  "الآن أرسل لي الملف المراد تحليله (.so أو .c أو .lst).",
                                  chat_id=user_id, message_id=call.message.message_id)
            bot.register_next_step_handler(call.message, handle_file)
    elif data.startswith("approve:"):
        # معالجة موافقة المالك
        parts = data.split(':')
        if len(parts) != 3:
            return
        decision = parts[1]
        target_user_id = int(parts[2])
        if user_id != BOT_OWNER_ID:
            bot.answer_callback_query(call.id, "أنت لست المالك", show_alert=True)
            return
        if decision == 'yes':
            update_user_data(target_user_id, approved=True)
            bot.edit_message_text(f"✅ تمت الموافقة على المستخدم {target_user_id}.",
                                  chat_id=user_id, message_id=call.message.message_id)
            try:
                bot.send_message(target_user_id, "✅ تمت موافقة المالك على طلبك. يمكنك الآن استخدام البوت بإرسال /start")
            except:
                pass
        elif decision == 'no':
            update_user_data(target_user_id, approved=False)
            bot.edit_message_text(f"❌ تم رفض المستخدم {target_user_id}.",
                                  chat_id=user_id, message_id=call.message.message_id)
            try:
                bot.send_message(target_user_id, "❌ للأسف، رفض المالك طلب استخدام البوت.")
            except:
                pass
    elif data.startswith("owner:"):
        if user_id != BOT_OWNER_ID:
            bot.answer_callback_query(call.id, "للمالك فقط", show_alert=True)
            return
        action = data.split(":")[1]
        if action == "list":
            db = load_db()
            if not db:
                bot.send_message(user_id, "لا يوجد مستخدمين بعد.")
            else:
                lines = ["📋 *قائمة المستخدمين:*"]
                for uid, udata in db.items():
                    lines.append(f"👤 `{uid}`: موافق: {'✅' if udata.get('approved', False) else '❌'}, ملفات: {udata.get('file_count', 0)}/{udata.get('max_files', DEFAULT_MAX_FILES)}")
                bot.send_message(user_id, "\n".join(lines), parse_mode="Markdown")
            # نرجع لقسم المالك
            owner_menu(call.message)
        elif action == "info":
            msg = bot.send_message(user_id, "🔍 أرسل الآيدي الذي تريد معلوماته:")
            bot.register_next_step_handler(msg, owner_info_handler)
        elif action == "setlimit":
            msg = bot.send_message(user_id, "📈 أرسل الآيدي الذي تريد تغيير حده:")
            bot.register_next_step_handler(msg, owner_setlimit_user_handler)
    elif data.startswith("limit:"):
        if user_id != BOT_OWNER_ID:
            bot.answer_callback_query(call.id, "للمالك فقط", show_alert=True)
            return
        action = data.split(":")[1]  # increase or decrease
        # نحتاج إلى المستخدم الهدف من session
        target = user_sessions.get(user_id, {}).get('target_user_id')
        if not target:
            bot.send_message(user_id, "❌ حدث خطأ، لم يتم تحديد المستخدم. أعد المحاولة.")
            return
        user_sessions[user_id]['limit_action'] = action
        msg = bot.send_message(user_id, "🔢 أرسل القيمة (رقم):")
        bot.register_next_step_handler(msg, owner_setlimit_value_handler)

def owner_menu(message):
    user_id = message.chat.id
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📋 عرض جميع المستخدمين", callback_data="owner:list"))
    markup.add(InlineKeyboardButton("🔍 معلومات مستخدم", callback_data="owner:info"))
    markup.add(InlineKeyboardButton("📈 تغيير حد المستخدم", callback_data="owner:setlimit"))
    markup.add(InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main"))
    bot.send_message(user_id, "👑 *قسم المالك*\nاختر ما تريد:", reply_markup=markup, parse_mode="Markdown")

def owner_info_handler(message):
    user_id = message.chat.id
    try:
        target = int(message.text.strip())
        data = get_user_data(target)
        text = (f"🔍 *معلومات المستخدم {target}:*\n"
                f"✅ موافق عليه: {'نعم' if data['approved'] else 'لا'}\n"
                f"📊 عدد الملفات المستخدمة: {data['file_count']}\n"
                f"🔢 الحد الأقصى: {data['max_files']}")
        bot.send_message(user_id, text, parse_mode="Markdown")
    except ValueError:
        bot.send_message(user_id, "❌ الآيدي يجب أن يكون رقماً.")
    finally:
        # العودة لقسم المالك
        owner_menu(message)

def owner_setlimit_user_handler(message):
    user_id = message.chat.id
    try:
        target = int(message.text.strip())
        user_sessions[user_id] = {'target_user_id': target}
        current = get_user_max_files(target)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("➕ زيادة", callback_data="limit:increase"),
                   InlineKeyboardButton("➖ نقصان", callback_data="limit:decrease"), row_width=2)
        bot.send_message(user_id, f"المستخدم {target} حده الحالي: {current}\nهل تريد زيادة أم نقصان؟",
                         reply_markup=markup)
    except ValueError:
        bot.send_message(user_id, "❌ الآيدي يجب أن يكون رقماً. أعد المحاولة:")
        bot.register_next_step_handler(message, owner_setlimit_user_handler)

def owner_setlimit_value_handler(message):
    user_id = message.chat.id
    try:
        value = int(message.text.strip())
        if value < 0:
            bot.send_message(user_id, "❌ القيمة يجب أن تكون 0 أو أكثر. أعد المحاولة:")
            bot.register_next_step_handler(message, owner_setlimit_value_handler)
            return
        sess = user_sessions.get(user_id, {})
        target = sess.get('target_user_id')
        action = sess.get('limit_action')
        if not target or not action:
            bot.send_message(user_id, "❌ حدث خطأ، لم يتم تحديد المستهدف. أعد المحاولة.")
            return
        current = get_user_max_files(target)
        if action == 'increase':
            new_max = current + value
        elif action == 'decrease':
            new_max = current - value
            if new_max < 0:
                new_max = 0
        else:
            bot.send_message(user_id, "❌ إجراء غير معروف.")
            return
        update_user_data(target, max_files=new_max)
        bot.send_message(user_id, f"✅ تم تحديث حد المستخدم {target} من {current} إلى {new_max}.")
    except ValueError:
        bot.send_message(user_id, "❌ القيمة يجب أن تكون رقماً صحيحاً. أعد المحاولة:")
        bot.register_next_step_handler(message, owner_setlimit_value_handler)
    finally:
        if user_id in user_sessions:
            del user_sessions[user_id]
        owner_menu(message)

# ================= معالجات الملفات =================
def handle_custom_strings_file(message):
    user_id = message.chat.id
    if not message.document:
        bot.send_message(user_id, "❌ الرجاء إرسال ملف.")
        bot.register_next_step_handler(message, handle_custom_strings_file)
        return
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    try:
        content = downloaded_file.decode('utf-8', errors='ignore')
    except:
        bot.send_message(user_id, "❌ لا يمكن قراءة الملف. تأكد من أنه نصي بصيغة UTF-8.")
        bot.register_next_step_handler(message, handle_custom_strings_file)
        return

    custom_dict = {}
    errors = []
    for line_num, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' not in line:
            errors.append(f"السطر {line_num}: لا يحتوي على ':' - تم تجاهله")
            continue
        s, d = line.split(':', 1)
        custom_dict[s.strip()] = d.strip()

    if errors:
        bot.send_message(user_id, "\n".join(errors[:5]) + ("\n..." if len(errors)>5 else ""))

    if not custom_dict:
        bot.send_message(user_id, "❌ لم يتم العثور على أي أزواج صحيحة (نص:وصف).")
        bot.register_next_step_handler(message, handle_custom_strings_file)
        return

    # حفظ custom_dict مؤقتاً
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    user_sessions[user_id]['custom_dict'] = custom_dict

    bot.send_message(user_id, f"✅ تم تحميل {len(custom_dict)} سلسلة نصية.\n\nالآن أرسل الملف المراد تحليله (.so أو .c/.lst).")
    bot.register_next_step_handler(message, handle_file)

def handle_file(message):
    user_id = message.chat.id
    if not message.document:
        bot.send_message(user_id, "❌ الرجاء إرسال ملف.")
        bot.register_next_step_handler(message, handle_file)
        return

    # التحقق من الحد المسموح به
    if user_id != BOT_OWNER_ID:
        user_data = get_user_data(user_id)
        max_files = get_user_max_files(user_id)
        if user_data["file_count"] >= max_files:
            bot.send_message(user_id, f"⚠️ لقد تجاوزت الحد الأقصى المسموح به ({max_files} ملفات). لا يمكنك استخدام البوت أكثر.")
            return

    # حفظ معلومات الملف مؤقتاً
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    user_sessions[user_id]['file_id'] = message.document.file_id
    user_sessions[user_id]['filename'] = message.document.file_name

    bot.send_message(user_id, "📛 الآن أرسل اسم المكتبة (مثال: libil2cpp.so):")
    bot.register_next_step_handler(message, handle_lib_name)

def handle_lib_name(message):
    user_id = message.chat.id
    lib_name = message.text.strip()
    if not lib_name:
        bot.send_message(user_id, "❌ اسم المكتبة لا يمكن أن يكون فارغاً. أعد المحاولة:")
        bot.register_next_step_handler(message, handle_lib_name)
        return

    sess = user_sessions.get(user_id, {})
    mode = sess.get('mode')
    if not mode:
        bot.send_message(user_id, "⚠️ انتهت الجلسة. أرسل /start للبدء من جديد.")
        return

    file_id = sess.get('file_id')
    filename = sess.get('filename')
    if not file_id or not filename:
        bot.send_message(user_id, "⚠️ لم يتم تحديد ملف. أعد المحاولة.")
        return

    # تحميل الملف
    file_info = bot.get_file(file_id)
    file_bytes = bot.download_file(file_info.file_path)

    status_msg = bot.send_message(user_id, "🔄 جاري المعالجة... الرجاء الانتظار.")

    if mode == "mode1":
        result_text, python_content = process_protection(file_bytes, filename, lib_name)
        if python_content:
            bot.delete_message(user_id, status_msg.message_id)
            # إرسال ملف بايثون
            bot.send_document(user_id, BytesIO(python_content.encode()), visible_file_name="protection_offsets.py",
                              caption="🔐 أوفستات الحماية (ملف بايثون)")
            if len(result_text) < 1000:
                bot.send_message(user_id, f"*النتائج (معاينة):*\n```\n{result_text}\n```", parse_mode="Markdown")
            if user_id != BOT_OWNER_ID:
                increment_file_count(user_id)
        else:
            bot.edit_message_text(result_text, user_id, status_msg.message_id)

    elif mode == "mode2":
        custom_dict = sess.get('custom_dict', {})
        if not custom_dict:
            bot.edit_message_text("❌ لم يتم تحميل سلاسل مخصصة.", user_id, status_msg.message_id)
            return
        result_text, python_content = process_custom_strings(file_bytes, filename, lib_name, custom_dict)
        if python_content:
            bot.delete_message(user_id, status_msg.message_id)
            bot.send_document(user_id, BytesIO(python_content.encode()), visible_file_name="custom_offsets.py",
                              caption="📝 أوفستات السلاسل المخصصة (ملف بايثون)")
            if len(result_text) < 1000:
                bot.send_message(user_id, f"*النتائج (معاينة):*\n```\n{result_text}\n```", parse_mode="Markdown")
            if user_id != BOT_OWNER_ID:
                increment_file_count(user_id)
        else:
            bot.edit_message_text(result_text, user_id, status_msg.message_id)

    elif mode == "mode3":
        result_text, python_content = process_patch_extract(file_bytes, filename, lib_name)
        if python_content:
            bot.delete_message(user_id, status_msg.message_id)
            bot.send_document(user_id, BytesIO(python_content.encode()), visible_file_name="patch_results.py",
                              caption="🔧 أكواد PATCH (ملف بايثون)")
            if len(result_text) < 1000:
                bot.send_message(user_id, f"*النتائج (معاينة):*\n```\n{result_text}\n```", parse_mode="Markdown")
            if user_id != BOT_OWNER_ID:
                increment_file_count(user_id)
        else:
            bot.edit_message_text(result_text, user_id, status_msg.message_id)

    elif mode == "mode4":
        offsets_text, codes_text, python_content = process_activation(file_bytes, filename, lib_name)
        bot.delete_message(user_id, status_msg.message_id)
        if python_content:
            bot.send_document(user_id, BytesIO(python_content.encode()), visible_file_name="activation_patches.py",
                              caption="⚡ أوفستات التفعيلات وأكواد الباتش (ملف بايثون)")
            if offsets_text and offsets_text != "لم يتم العثور على نتائج." and len(offsets_text) < 1000:
                bot.send_message(user_id, f"*الأوفستات:*\n```\n{offsets_text}\n```", parse_mode="Markdown")
            if codes_text and codes_text != "لم يتم العثور على نتائج." and len(codes_text) < 1000:
                bot.send_message(user_id, f"*أكواد الباتش:*\n```\n{codes_text}\n```", parse_mode="Markdown")
            if user_id != BOT_OWNER_ID:
                increment_file_count(user_id)
        else:
            bot.send_message(user_id, "❌ لم يتم العثور على أي نتائج.")

    # تنظيف الجلسة
    if user_id in user_sessions:
        del user_sessions[user_id]

# ================= تشغيل البوت =================
if __name__ == "__main__":
    print("🤖 البوت يعمل...")
    bot.infinity_polling()
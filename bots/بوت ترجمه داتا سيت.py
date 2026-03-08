import telebot
import os
import json
import csv
import requests
import re

TOKEN = "8554813556:AAE8xn3NtsCgBmsTN9DgKJ7uvU6j45CLOWg"
bot = telebot.TeleBot(TOKEN)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "translated"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# دالة الترجمة دفعة واحدة
def translate_bulk(text):
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "en", "tl": "ar", "dt": "t", "q": text}
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return "".join([t[0] for t in result[0]])
        else:
            return text
    except:
        return text

# دالة ذكية جدًا لتحديد سطر كود
def is_code_line(line):
    line = line.strip()
    if not line:
        return False
    # مؤشرات الأكواد
    code_patterns = [
        r"^\s*(import|from|def|class|function|const|let|var|#|//)",
        r"[{}();<>$=\\[\]]",
        r"\.py|\.js|\.cpp|\.java|\.sh|\.html|\.css"
    ]
    symbols = sum(1 for c in line if c in "{}();<>=$\\[]")
    words = len(re.findall(r"[a-zA-Z]{2,}", line))
    # أكثر الرموز من الكلمات → كود
    if symbols > words:
        return True
    # أي نمط أكواد معروف
    if any(re.search(pat, line) for pat in code_patterns):
        return True
    return False

def read_txt(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return [line.rstrip("\n") for line in f]

def read_csv(file_path):
    rows = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append([cell.rstrip() for cell in row])
    return rows

def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        try:
            return json.load(f)
        except:
            return None

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id,
                     "👋 هلا! أرسل ملف TXT, CSV, أو JSON.\n"
                     "سأترجم النصوص الإنجليزية فقط بسرعة.\n"
                     "✅ الأكواد والسكربتات لا تتأثر.\n"
                     "✅ الملفات الكبيرة مقسمة لسرعة الترجمة.")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    input_path = os.path.join(UPLOAD_DIR, message.document.file_name)
    output_path = os.path.join(OUTPUT_DIR, "translated_" + message.document.file_name)

    with open(input_path, 'wb') as f:
        f.write(downloaded_file)

    ext = message.document.file_name.split('.')[-1].lower()
    bot.send_message(message.chat.id, "⏳ جاري الترجمة…")

    try:
        if ext == "txt":
            lines = read_txt(input_path)
            translated_lines = []

            batch_size = 300  # دفعات أكبر → أسرع
            text_batch = []

            for line in lines:
                if is_code_line(line):
                    if text_batch:
                        translated_batch = translate_bulk("\n".join(text_batch))
                        translated_lines.extend(translated_batch.split("\n"))
                        text_batch = []
                    translated_lines.append(line)
                else:
                    text_batch.append(line)

                if len(text_batch) >= batch_size:
                    translated_batch = translate_bulk("\n".join(text_batch))
                    translated_lines.extend(translated_batch.split("\n"))
                    text_batch = []

            if text_batch:
                translated_batch = translate_bulk("\n".join(text_batch))
                translated_lines.extend(translated_batch.split("\n"))

            with open(output_path, 'w', encoding='utf-8') as f:
                f.writelines([line + "\n" for line in translated_lines])

            with open(output_path, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="✅ تم ترجمة الملف بالكامل بسرعة وبدون المساس بالكود.")

        elif ext == "csv":
            rows = read_csv(input_path)
            translated_rows = []
            batch_size = 150
            text_batch = []

            for row in rows:
                line = " , ".join(row)
                if any(is_code_line(cell) for cell in row):
                    if text_batch:
                        translated_batch = translate_bulk("\n".join(text_batch))
                        for t_line in translated_batch.split("\n"):
                            translated_rows.append([cell.strip() for cell in t_line.split(",")])
                        text_batch = []
                    translated_rows.append(row)
                else:
                    text_batch.append(line)

                if len(text_batch) >= batch_size:
                    translated_batch = translate_bulk("\n".join(text_batch))
                    for t_line in translated_batch.split("\n"):
                        translated_rows.append([cell.strip() for cell in t_line.split(",")])
                    text_batch = []

            if text_batch:
                translated_batch = translate_bulk("\n".join(text_batch))
                for t_line in translated_batch.split("\n"):
                    translated_rows.append([cell.strip() for cell in t_line.split(",")])

            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(translated_rows)

            with open(output_path, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="✅ تم ترجمة الملف بالكامل بسرعة وبدون المساس بالكود.")

        elif ext == "json":
            data = read_json(input_path)
            if data:
                def translate_json(obj):
                    if isinstance(obj, dict):
                        return {k: translate_json(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [translate_json(i) for i in obj]
                    elif isinstance(obj, str):
                        if is_code_line(obj):
                            return obj
                        else:
                            return translate_bulk(obj)
                    else:
                        return obj

                translated_data = translate_json(data)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(translated_data, f, ensure_ascii=False, indent=2)

                with open(output_path, 'rb') as f:
                    bot.send_document(message.chat.id, f, caption="✅ تم ترجمة الملف بالكامل بسرعة وبدون المساس بالكود.")

        else:
            bot.send_message(message.chat.id, "❌ صيغة الملف غير مدعومة. استخدم TXT, CSV, JSON فقط.")
            return

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء الترجمة: {str(e)}")
        return

bot.polling()
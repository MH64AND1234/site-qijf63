import telebot
import requests
import tempfile

TOKEN = "PUT_BOT_TOKEN"

bot = telebot.TeleBot(TOKEN)

API = "https://darkaiwormgptvercel.vercel.app/api/sendError"

session = requests.Session()

history = {}
last_code = {}

# فهم نوع المشروع
def detect_project_type(text):

    t = text.lower()

    if "موقع" in t or "html" in t or "website" in t:
        return "html"

    if "بوت" in t or "telegram bot" in t:
        return "py"

    if "سكربت" in t or "script" in t:
        return "py"

    if "api" in t:
        return "json"

    if "css" in t:
        return "css"

    if "javascript" in t or "js" in t:
        return "js"

    return "txt"


def ask_ai(text):

    payload = {"text": text}

    r = session.post(API, json=payload)

    try:
        data = r.json()
        return data.get("response", "")
    except:
        return r.text


def split_code_explain(text):

    if "```" in text:

        parts = text.split("```")

        if len(parts) >= 2:

            code = parts[1]

            explain = parts[0] + (parts[2] if len(parts) > 2 else "")

            return code.strip(), explain.strip()

    return text, ""


def send_code(chat_id, code, explain, user_text):

    ext = detect_project_type(user_text)

    file = tempfile.NamedTemporaryFile(delete=False, suffix="."+ext)

    file.write(code.encode())

    file.close()

    bot.send_document(
        chat_id,
        open(file.name, "rb"),
        caption=explain if explain else f"📂 file type: {ext}"
    )


@bot.message_handler(commands=["start"])
def start(message):

    bot.send_message(
        message.chat.id,
        "🤖 ارسل طلبك لصنع او تعديل كود"
    )


@bot.message_handler(content_types=["text"])
def chat(message):

    chat = message.chat.id

    bot.send_chat_action(chat, "typing")

    text = message.text

    if chat not in history:
        history[chat] = []

    if chat in last_code:

        prompt = f"""
هذا الكود السابق:

{last_code[chat]}

طلب المستخدم:
{text}

عدل الكود حسب الطلب وارجع الكود فقط.
"""

    else:

        prompt = text


    history[chat].append(prompt)

    response = ask_ai(prompt)

    code, explain = split_code_explain(response)

    last_code[chat] = code

    send_code(chat, code, explain, text)


@bot.message_handler(content_types=["document"])
def file_handler(message):

    chat = message.chat.id

    bot.send_chat_action(chat, "typing")

    file_info = bot.get_file(message.document.file_id)

    downloaded = bot.download_file(file_info.file_path)

    code = downloaded.decode(errors="ignore")

    desc = message.caption if message.caption else "عدل الكود"

    prompt = f"""
عدل الكود حسب الوصف

الوصف:
{desc}

الكود:
{code}
"""

    response = ask_ai(prompt)

    new_code, explain = split_code_explain(response)

    last_code[chat] = new_code

    send_code(chat, new_code, explain, desc)


print("BOT RUNNING")

bot.infinity_polling()
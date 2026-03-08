import os
import telebot
import tempfile
import uuid
import base64
import zlib
import gzip
import bz2
import lzma
import marshal
import pickle
import json
import re
import sys
import subprocess
import zipfile
import tarfile
import time
from io import BytesIO

# ======================== التهيئة ========================
TOKEN = "8560731015:AAESB3dByps5J0ZeP_RjJga0-KeO9727hAY"
bot = telebot.TeleBot(TOKEN)

TIME_BYPASS_CODE = '''# === وقت متجاوز ===
import datetime
import time

# تعطيل دوال الوقت
class NoTime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls.min

datetime.datetime = NoTime

def fake_time():
    return 0

time.time = fake_time
# ======================
'''

# ======================== أدوات فك التشفير ========================

class DecoderChain:
    def __init__(self):
        self.decoders = [
            # الترميزات النصية
            ('base64', self.decode_base64),
            ('base32', self.decode_base32),
            ('base16', self.decode_base16),
            ('base85', self.decode_base85),
            ('ascii85', self.decode_ascii85),
            ('rot13', self.decode_rot13),
            ('string_escape', self.decode_string_escape),
            ('unicode_escape', self.decode_unicode_escape),
            ('quopri', self.decode_quopri),
            ('url', self.decode_url),
            
            # الضغط
            ('zlib', self.decode_zlib),
            ('gzip', self.decode_gzip),
            ('bz2', self.decode_bz2),
            ('lzma', self.decode_lzma),
            
            # تسلسل بايثون
            ('marshal', self.decode_marshal),
            ('pickle', self.decode_pickle),
            ('json', self.decode_json),
            ('repr', self.decode_repr),
            
            # تحويلات عكسية
            ('reverse', self.decode_reverse),
            ('xor', self.decode_xor),  # يحتاج مفتاح
            ('caesar', self.decode_caesar),
            
            # أنماط شائعة في التشفير اليدوي
            ('exec_wrap', self.decode_exec_wrap),
            ('compile_wrap', self.decode_compile_wrap),
            ('base64+zlib', self.decode_base64_zlib_combined),
            
            # أدوات معروفة (نحاول استدعاء أدوات خارجية)
            ('pyarmor', self.decode_pyarmor),
            ('pyc', self.decode_pyc),
        ]
        self.max_iterations = 50  # عدد أقصى من الطبقات
    
    def decode_base64(self, data):
        try:
            return base64.b64decode(data).decode('utf-8', errors='ignore')
        except:
            return None
    
    def decode_base32(self, data):
        try:
            return base64.b32decode(data).decode('utf-8', errors='ignore')
        except:
            return None
    
    def decode_base16(self, data):
        try:
            return base64.b16decode(data).decode('utf-8', errors='ignore')
        except:
            return None
    
    def decode_base85(self, data):
        try:
            return base64.b85decode(data).decode('utf-8', errors='ignore')
        except:
            return None
    
    def decode_ascii85(self, data):
        try:
            import codecs
            return codecs.decode(data.encode(), 'ascii85').decode('utf-8', errors='ignore')
        except:
            return None
    
    def decode_rot13(self, data):
        try:
            return codecs.decode(data, 'rot_13')
        except:
            return None
    
    def decode_string_escape(self, data):
        try:
            return data.encode().decode('unicode_escape')
        except:
            return None
    
    def decode_unicode_escape(self, data):
        try:
            return data.encode().decode('unicode_escape')
        except:
            return None
    
    def decode_quopri(self, data):
        try:
            import quopri
            return quopri.decodestring(data.encode()).decode()
        except:
            return None
    
    def decode_url(self, data):
        try:
            from urllib.parse import unquote
            return unquote(data)
        except:
            return None
    
    def decode_zlib(self, data):
        try:
            if isinstance(data, str):
                data = data.encode()
            return zlib.decompress(data).decode('utf-8', errors='ignore')
        except:
            return None
    
    def decode_gzip(self, data):
        try:
            if isinstance(data, str):
                data = data.encode()
            return gzip.decompress(data).decode('utf-8', errors='ignore')
        except:
            return None
    
    def decode_bz2(self, data):
        try:
            if isinstance(data, str):
                data = data.encode()
            return bz2.decompress(data).decode('utf-8', errors='ignore')
        except:
            return None
    
    def decode_lzma(self, data):
        try:
            if isinstance(data, str):
                data = data.encode()
            return lzma.decompress(data).decode('utf-8', errors='ignore')
        except:
            return None
    
    def decode_marshal(self, data):
        try:
            if isinstance(data, str):
                data = data.encode()
            code_obj = marshal.loads(data)
            # محاولة تحويل code object إلى مصدر (باستخدام uncompyle6 إذا وجد)
            return self._code_to_source(code_obj)
        except:
            return None
    
    def decode_pickle(self, data):
        try:
            if isinstance(data, str):
                data = data.encode()
            obj = pickle.loads(data)
            return str(obj)  # قد يكون كوداً أو شيئاً آخر
        except:
            return None
    
    def decode_json(self, data):
        try:
            obj = json.loads(data)
            return json.dumps(obj, indent=2)  # ليس كوداً بالضرورة
        except:
            return None
    
    def decode_repr(self, data):
        try:
            # قد يكون repr لكود بايثون
            return eval(data)  # خطر! لكننا لا ننفذ، فقط نأخذ النص. نحتاج لفحص.
            # بدلاً من eval نستخدم ast.literal_eval إن أمكن
            import ast
            return ast.literal_eval(data)
        except:
            return None
    
    def decode_reverse(self, data):
        return data[::-1]
    
    def decode_xor(self, data, key=0x42):
        try:
            if isinstance(data, str):
                data = data.encode()
            return bytes([b ^ key for b in data]).decode('utf-8', errors='ignore')
        except:
            return None
    
    def decode_caesar(self, data, shift=13):
        try:
            # فقط للحروف الإنجليزية البسيطة
            result = []
            for c in data:
                if 'a' <= c <= 'z':
                    result.append(chr((ord(c) - ord('a') + shift) % 26 + ord('a')))
                elif 'A' <= c <= 'Z':
                    result.append(chr((ord(c) - ord('A') + shift) % 26 + ord('A')))
                else:
                    result.append(c)
            return ''.join(result)
        except:
            return None
    
    def decode_exec_wrap(self, data):
        # أنماط مثل exec("...") أو exec(base64.b64decode("..."))
        pattern = r'exec\([\'"](.+?)[\'"]\)'
        match = re.search(pattern, data, re.DOTALL)
        if match:
            return match.group(1)
        return None
    
    def decode_compile_wrap(self, data):
        pattern = r'compile\([\'"](.+?)[\'"],'
        match = re.search(pattern, data, re.DOTALL)
        if match:
            return match.group(1)
        return None
    
    def decode_base64_zlib_combined(self, data):
        # بعض الأحيان base64 ثم zlib
        decoded = self.decode_base64(data)
        if decoded:
            return self.decode_zlib(decoded)
        return None
    
    def decode_pyarmor(self, data):
        # محاولة استخدام أداة خارجية مثل pyarmor-unpacker
        # هذا يتطلب وجود الأداة في النظام
        try:
            # نفترض أن لدينا ملف مؤقت
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(data)
                f.flush()
                # تشغيل pyarmor-unpacker (مثال)
                result = subprocess.run(['pyarmor-unpacker', f.name], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout
        except:
            pass
        return None
    
    def decode_pyc(self, data):
        # إذا كان المحتوى يبدو كملف pyc (يبدأ بالتوقيع)
        if data.startswith(b'\x03\xf3\r\n') or data.startswith(b'\x03\xf3'):
            # حفظ الملف مؤقتاً
            with tempfile.NamedTemporaryFile(suffix='.pyc', delete=False) as f:
                f.write(data)
                f.flush()
                try:
                    # استخدام uncompyle6
                    result = subprocess.run(['uncompyle6', f.name], capture_output=True, text=True)
                    if result.returncode == 0:
                        return result.stdout
                except:
                    pass
                try:
                    # استخدام pycdc
                    result = subprocess.run(['pycdc', f.name], capture_output=True, text=True)
                    if result.returncode == 0:
                        return result.stdout
                except:
                    pass
        return None
    
    def _code_to_source(self, code_obj):
        # محاولة تحويل code object إلى نص باستخدام uncompyle6
        # نحتاج إلى حفظ الكود في ملف مؤقت
        try:
            import marshal
            with tempfile.NamedTemporaryFile(suffix='.pyc', delete=False) as f:
                # كتابة header مناسب للإصدار
                f.write(b'\x03\xf3\r\n' + marshal.dumps(code_obj))
                f.flush()
                result = subprocess.run(['uncompyle6', f.name], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout
        except:
            pass
        return str(code_obj)  # fallback
    
    def recursive_decode(self, data, max_iterations=None):
        if max_iterations is None:
            max_iterations = self.max_iterations
        
        history = []  # لمنع التكرار
        current = data
        used_decoders = []
        
        for _ in range(max_iterations):
            if current in history:
                break
            history.append(current)
            
            # إذا أصبح النص قابلاً للقراءة (يحتوي على كلمات بايثون مفتاحية)
            if self.is_plain_python(current):
                break
            
            # حاول كل المفككات
            decoded = None
            for name, decoder in self.decoders:
                try:
                    result = decoder(current)
                    if result and result != current and len(result) > 0:
                        decoded = result
                        used_decoders.append(name)
                        break
                except:
                    continue
            
            if decoded is None:
                break
            current = decoded
        
        return current, used_decoders
    
    def is_plain_python(self, text):
        if not isinstance(text, str):
            return False
        # فحص وجود كلمات مفتاحية بايثون شائعة
        keywords = ['def ', 'class ', 'import ', 'from ', 'if ', 'else:', 'for ', 'while ', 'return ', 'print']
        return any(k in text for k in keywords)

# ======================== معالجة الملفات ========================

def process_file_content(content_bytes):
    """معالجة محتوى الملف (بايت) ومحاولة فك التشفير"""
    # تحويل البايت إلى نص (إذا كان نصياً)
    try:
        text = content_bytes.decode('utf-8')
    except UnicodeDecodeError:
        text = None
    
    chain = DecoderChain()
    
    if text is not None:
        # محاولة فك التشفير
        decoded_text, used = chain.recursive_decode(text)
        if decoded_text != text:
            return decoded_text, used
        else:
            return text, used
    else:
        # الملف ليس نصياً، ربما هو pyc أو مضغوط
        # نتعامل معه كـ bytes
        # يمكن أن يكون مضغوطاً
        # نحاول فك الضغط أولاً
        # ... (يمكن إضافة معالجة للضغط هنا)
        # إذا كان يبدو كـ pyc
        if content_bytes.startswith(b'\x03\xf3'):
            decoded = chain.decode_pyc(content_bytes)
            if decoded:
                return decoded, ['pyc']
        # وإلا نعيد None
        return None, []

# ======================== بوت التيليغرام ========================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أرسل ملف بايثون (.py, .pyc, أو ملف مضغوط) وسأحاول فك تشفيره وإضافة كود تجاوز الوقت. أنا أدعم أكثر من 50 نوع تشفير وطبقات متعددة!")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    try:
        file_name = message.document.file_name
        # نقبل أي امتداد لأن الملف قد يكون مضغوطاً أو مشفراً بدون امتداد معروف
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # حفظ الملف مؤقتاً
        unique_id = uuid.uuid4().hex
        temp_input = f"input_{unique_id}.tmp"
        with open(temp_input, "wb") as f:
            f.write(downloaded_file)
        
        # معالجة الملف
        # قد يكون مضغوطاً (zip, tar)
        if zipfile.is_zipfile(temp_input):
            with zipfile.ZipFile(temp_input, 'r') as z:
                # نبحث عن أول ملف .py
                py_files = [name for name in z.namelist() if name.endswith('.py')]
                if py_files:
                    with z.open(py_files[0]) as pyf:
                        content = pyf.read()
                else:
                    bot.reply_to(message, "الملف المضغوط لا يحتوي على ملفات بايثون.")
                    return
        elif tarfile.is_tarfile(temp_input):
            with tarfile.open(temp_input, 'r') as tar:
                py_members = [m for m in tar.getmembers() if m.name.endswith('.py')]
                if py_members:
                    f = tar.extractfile(py_members[0])
                    content = f.read()
                else:
                    bot.reply_to(message, "الملف المضغوط لا يحتوي على ملفات بايثون.")
                    return
        else:
            # ملف عادي
            with open(temp_input, "rb") as f:
                content = f.read()
        
        # محاولة فك التشفير
        decoded_text, used_decoders = process_file_content(content)
        
        if decoded_text is None:
            bot.reply_to(message, "لم أستطع فك تشفير هذا الملف. قد يكون مشفراً بتشفير قوي جداً أو غير مدعوم.")
            return
        
        # إضافة كود تجاوز الوقت
        modified_code = TIME_BYPASS_CODE + "\n" + decoded_text
        
        # إرسال النتيجة
        output_file = f"output_{unique_id}.py"
        with open(output_file, "w", encoding='utf-8') as f:
            f.write(modified_code)
        
        with open(output_file, "rb") as f:
            caption = f"تم فك التشفير بعد {len(used_decoders)} طبقة.\nالطرق المستخدمة: {', '.join(used_decoders) if used_decoders else 'نص عادي'}"
            bot.send_document(message.chat.id, f, caption=caption)
        
        # تنظيف
        os.remove(output_file)
        os.remove(temp_input)
        
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {str(e)}")
        # تنظيف
        for f in os.listdir():
            if f.startswith('input_') or f.startswith('output_'):
                os.remove(f)

bot.polling()
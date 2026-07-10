import os
import telebot
import re
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# بخش اول: روشن نگه داشتن سرور
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_server():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, DummyHandler)
    httpd.serve_forever()

threading.Thread(target=run_server).start()

# بخش دوم: اتصال رمزها
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! لینک ویدیوی یوتیوب را برای من بفرست تا جادوی هوش مصنوعی را ببینی 🪄")

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    if match:
        return match.group(1)
    return None

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    video_id = extract_video_id(url)
    
    if not video_id:
        bot.reply_to(message, "لطفاً یک لینک معتبر از یوتیوب بفرستید ❌")
        return
        
    bot.reply_to(message, "در حال استخراج متن ویدیو... لطفاً کمی صبر کنید ⏳")
    
    try:
        # روش ضدگلوله: اول دنبال فارسی و انگلیسی می‌گردیم، اگر نبود هر زبانی که ویدیو داشت را می‌گیریم
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['fa', 'fa-IR', 'en', 'en-US', 'en-GB'])
        except:
            # گرفتن زیرنویس پیش‌فرض (هر زبانی که باشد جمینای آن را می‌فهمد)
            transcript = YouTubeTranscriptApi.get_transcript(video_id)

        text = " ".join([t['text'] for t in transcript])
        text = text[:15000] # جلوگیری از خطای طولانی شدن بیش از حد
        
        bot.reply_to(message, "متن استخراج شد! در حال تحلیل توسط هوش مصنوعی... 🤖")
        
        # پرامپت با تاکید بر خروجی فارسی
        prompt = f"""
        من متن یک ویدیوی یوتیوب را به تو می‌دهم (ممکن است متن به زبان انگلیسی یا زبان دیگری باشد). 
        لطفاً آن را به دقت بخوان و بر اساس آن، یک تیتر جذاب، یک پاراگراف دیسکریپشن، چند هشتگ مرتبط، و مجموعه‌ای از کلمات کلیدی (تگ‌ها) **تماماً به زبان فارسی** به من بده.
        
        قانون مهم: تگ‌ها باید با کاما از هم جدا شده باشند، مجموع کاراکترهای تگ‌ها تحت هیچ شرایطی بیشتر از 500 کاراکتر نشود تا بتوانم مستقیم در یوتیوب کپی کنم.
        
        متن ویدیو:
        {text}
        """
        
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
        
    except Exception as e:
        bot.reply_to(message, f"این ویدیو هیچ زیرنویس متنی (حتی انگلیسی) ندارد که بتوانم استخراج کنم. 🚫\nدلیل فنی: {str(e)[:70]}")

bot.polling(non_stop=True)

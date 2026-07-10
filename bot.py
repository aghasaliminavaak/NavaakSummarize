import os
import telebot
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# بخش اول: ساخت یک سرور مجازی برای روشن ماندن 24 ساعته ربات
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

# بخش دوم: دریافت رمزها به صورت امن
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# بخش سوم: اتصال ربات و هوش مصنوعی
bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# بخش چهارم: دستور شروع ربات
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! لینک ویدیوی یوتیوب را برای من بفرست تا جادوی هوش مصنوعی را ببینی 🪄")

def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None

# بخش پنجم: پردازش لینک یوتیوب
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    video_id = extract_video_id(url)
    
    if not video_id:
        bot.reply_to(message, "لطفاً یک لینک معتبر از یوتیوب بفرستید ❌")
        return
        
    bot.reply_to(message, "در حال استخراج متن ویدیو... لطفاً کمی صبر کنید ⏳")
    
    try:
        # استخراج زیرنویس
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['fa', 'en'])
        text = " ".join([t['text'] for t in transcript])
        text = text[:15000] # محدودیت برای جلوگیری از خطای طولانی شدن متن
        
        bot.reply_to(message, "متن استخراج شد! در حال تحلیل توسط جمینای... 🤖")
        
        # پرامپتی که شما خواستید
        prompt = f"""
        من متن یک ویدیوی یوتیوب را به تو می‌دهم. بر اساس آن، یک تیتر جذاب، یک پاراگراف دیسکریپشن، چند هشتگ مرتبط، و مجموعه‌ای از کلمات کلیدی (تگ‌ها) به من بده.
        قانون مهم: تگ‌ها باید با کاما از هم جدا شده باشند، مجموع کاراکترهای تگ‌ها تحت هیچ شرایطی بیشتر از 500 کاراکتر نشود تا بتوانم مستقیم در یوتیوب کپی کنم.
        
        متن ویدیو:
        {text}
        """
        
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
        
    except Exception as e:
        bot.reply_to(message, "متأسفانه نتوانستم زیرنویس این ویدیو را پیدا کنم. دقت کنید که ویدیو حتماً باید زیرنویس (کپشن) فعال داشته باشد. 🚫")

# بخش ششم: روشن نگه داشتن ربات
bot.polling(non_stop=True)

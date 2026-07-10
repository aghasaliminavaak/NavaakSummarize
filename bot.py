import os
import telebot
import re
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# بخش اول: ساخت یک سرور مجازی
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

# بخش دوم: متغیرها
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! لینک ویدیوی یوتیوب را برای من بفرست تا جادوی هوش مصنوعی را ببینی 🪄")

# یک روش بسیار قدرتمندتر برای پیدا کردن ID ویدیو
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
        
    bot.reply_to(message, f"در حال استخراج متن ویدیو... لطفاً کمی صبر کنید ⏳")
    
    try:
        # گرفتن تمام زیرنویس‌های موجود برای این ویدیو
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        try:
            # اول سعی می‌کنیم زیرنویس فارسی یا انگلیسی (دستی یا خودکار) را بگیریم
            transcript = transcript_list.find_transcript(['fa', 'en']).fetch()
        except:
            # اگر فارسی یا انگلیسی نبود، اولین زیرنویسی که ویدیو داره رو می‌گیریم
            # جمینای اونقدر باهوش هست که خودش بقیه کارها رو هندل کنه!
            first_transcript = next(iter(transcript_list))
            transcript = first_transcript.fetch()

        text = " ".join([t['text'] for t in transcript])
        text = text[:15000] # محدودیت برای جلوگیری از خطای طولانی شدن متن
        
        bot.reply_to(message, "متن استخراج شد! در حال تحلیل توسط هوش مصنوعی... 🤖")
        
        prompt = f"""
        من متن یک ویدیوی یوتیوب را به تو می‌دهم. بر اساس آن، یک تیتر جذاب، یک پاراگراف دیسکریپشن، چند هشتگ مرتبط، و مجموعه‌ای از کلمات کلیدی (تگ‌ها) به من بده.
        قانون مهم: تگ‌ها باید با کاما از هم جدا شده باشند، مجموع کاراکترهای تگ‌ها تحت هیچ شرایطی بیشتر از 500 کاراکتر نشود تا بتوانم مستقیم در یوتیوب کپی کنم.
        
        متن ویدیو:
        {text}
        """
        
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
        
    except Exception as e:
        # اگر واقعا هیچ زیرنویسی نداشت، بخشی از خطای تخصصی را هم نشان می‌دهد تا مشکل را بفهمیم
        bot.reply_to(message, f"متأسفانه این ویدیو هیچ زیرنویسی ندارد یا محدودیت دسترسی دارد. 🚫\nدلیل فنی: {str(e)[:50]}")

bot.polling(non_stop=True)

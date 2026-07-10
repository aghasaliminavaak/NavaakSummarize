import os
import telebot
import re
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# بخش اول: سرور
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

# بخش دوم: ربات و جمینای
bot = telebot.TeleBot(os.environ.get("TELEGRAM_TOKEN"))
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    video_id = extract_video_id(url)
    
    if not video_id:
        bot.reply_to(message, "لطفاً لینک یوتیوب بفرست.")
        return
        
    bot.reply_to(message, "در حال پردازش...")
    
    try:
        # استفاده از متد مستقیم که کمتر دچار خطا می‌شود
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['fa', 'en', 'de', 'fr', 'es'])
        text = " ".join([t['text'] for t in transcript.fetch()])
        
        response = model.generate_content(f"بر اساس این متن، تایتل، دیسکریپشن و تگ‌های یوتیوب را به فارسی بنویس: {text[:10000]}")
        bot.reply_to(message, response.text)
        
    except Exception as e:
        bot.reply_to(message, f"خطا در دریافت زیرنویس. مطمئن شو ویدیو زیرنویس فعال دارد.")

bot.polling()

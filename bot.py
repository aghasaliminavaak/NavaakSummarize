import os
import telebot
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import threading
from flask import Flask

# دریافت رمزها از تنظیمات Railway
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ==========================================
# این بخش سرور فیک است تا Railway ارور ندهد
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive and running perfectly!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! من آماده‌ام. لینک ویدیوی یوتیوب رو بفرست تا سئوش کنم.")

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    try:
        url = message.text
        bot.reply_to(message, "در حال استخراج زیرنویس... لطفا منتظر بمانید ⏳")
        
        # ۱. استخراج آیدی ویدیو با yt-dlp (بدون دانلود ویدیو)
        ydl_opts = {'quiet': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info['id']
        
        # ۲. گرفتن متن زیرنویس
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['fa', 'en'])
        text = " ".join([t['text'] for t in transcript_list])
        
        bot.reply_to(message, "زیرنویس دریافت شد! در حال تحلیل با هوش مصنوعی... 🧠")

        # ۳. ارسال به جمینای برای تولید محتوای سئو شده
        prompt = f"""
        تو یک متخصص سئو و تولید محتوا برای یوتیوب هستی. بر اساس متن زیرنویس این ویدیو:
        ۱. سه تا تایتل جذاب و کلیک‌خور به فارسی پیشنهاد بده.
        ۲. یک دیسکریپشن حرفه‌ای و سئوشده بنویس.
        ۳. تگ‌ها و هشتگ‌های مناسب رو لیست کن.
        
        متن ویدیو:
        {text[:10000]}
        """
        response = model.generate_content(prompt)
        
        bot.reply_to(message, response.text)
        
    except Exception as e:
        bot.reply_to(message, f"❌ خطا در پردازش: {str(e)}\n\n(مطمئن شو ویدیو زیرنویس داره و پرایوت نیست)")

# اجرای همزمان وب‌سرور و ربات تلگرام
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.infinity_polling()

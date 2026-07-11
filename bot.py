import os
import telebot
import re
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import threading
from flask import Flask

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running perfectly!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def get_video_id(url):
    match = re.search(r"(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! من آماده‌ام. لینک ویدیوی یوتیوب رو بفرست تا سئوش کنم.")

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    try:
        url = message.text
        bot.reply_to(message, "در حال استخراج زیرنویس... لطفا منتظر بمانید ⏳")
        
        video_id = get_video_id(url)
        if not video_id:
            bot.reply_to(message, "❌ لینک یوتیوب نامعتبر است.")
            return
            
        # این همان بخشی است که به یوتیوب می‌گوید ما ربات نیستیم
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, 
            languages=['fa', 'en'],
            cookies='cookies.txt'
        )
        text = " ".join([t['text'] for t in transcript_list])
        
        bot.reply_to(message, "زیرنویس دریافت شد! در حال تحلیل با هوش مصنوعی... 🧠")

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
        bot.reply_to(message, f"❌ خطا در استخراج: {str(e)}\n\n(مطمئن شو ویدیو زیرنویس داره)")

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.infinity_polling()

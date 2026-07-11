import os
import telebot
import re
import requests
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
# سرور فیک برای روشن ماندن در Railway
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running perfectly!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
# ==========================================

def get_video_id(url):
    match = re.search(r"(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

# --- هسته جدید و ضدتحریم برای استخراج زیرنویس ---
def get_transcript_bypass(video_id):
    # لیست سرورهای واسطه اُپن‌سورس
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.syncpundit.io",
        "https://pipedapi.drgns.space"
    ]
    
    for api_url in instances:
        try:
            url = f"{api_url}/streams/{video_id}"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                subtitles = data.get("subtitles", [])
                if not subtitles:
                    continue # اگر زیرنویس نداشت، برو سرور بعدی
                
                # اولویت با زیرنویس فارسی یا انگلیسی
                sub_url = None
                for sub in subtitles:
                    if sub.get("code") in ["fa", "en"]:
                        sub_url = sub.get("url")
                        break
                
                if not sub_url:
                    sub_url = subtitles[0].get("url") # انتخاب اولین زیرنویس موجود
                    
                # دانلود متن زیرنویس
                vtt_res = requests.get(sub_url, timeout=10)
                vtt_text = vtt_res.text
                
                # پاکسازی زمان‌ها و تبدیل به متن خالص
                clean_text = []
                for line in vtt_text.split('\n'):
                    # نادیده گرفتن کدهای زمانی و اطلاعات اضافه
                    if '-->' in line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:') or not line.strip():
                        continue
                    # حذف تگ‌های HTML
                    clean_line = re.sub(r'<[^>]+>', '', line)
                    clean_text.append(clean_line.strip())
                
                final_text = " ".join(clean_text)
                if final_text:
                    return final_text
        except Exception:
            continue # اگر این سرور خراب بود، سرور بعدی را تست کن
            
    return None
# ----------------------------------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! من آماده‌ام. لینک ویدیوی یوتیوب رو بفرست تا سئوش کنم.")

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    try:
        url = message.text
        bot.reply_to(message, "در حال استخراج زیرنویس از طریق سرورهای واسطه... ⏳")
        
        video_id = get_video_id(url)
        if not video_id:
            bot.reply_to(message, "❌ لینک یوتیوب نامعتبر است.")
            return
            
        # استفاده از روش بای‌پس
        text = get_transcript_bypass(video_id)
        
        if not text:
            bot.reply_to(message, "❌ نتوانستم زیرنویس را استخراج کنم. یا ویدیو زیرنویس ندارد یا دسترسی مسدود است.")
            return
        
        bot.reply_to(message, "✅ زیرنویس با موفقیت و بدون درگیری با یوتیوب دریافت شد! در حال تحلیل با هوش مصنوعی... 🧠")

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
        bot.reply_to(message, f"❌ خطا در پردازش: {str(e)}")

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.infinity_polling()

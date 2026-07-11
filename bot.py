import os
import telebot
import re
import requests
import html
import google.generativeai as genai
import threading
from flask import Flask

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# مشکل دقیقاً همین خط بود که به gemini-pro تغییر کرد
model = genai.GenerativeModel("gemini-pro")

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

def get_transcript_bypass(video_id):
    try:
        url = f"https://youtubetranscript.com/?server_vid2={video_id}"
        res = requests.get(url, timeout=10)
        
        if res.status_code == 200 and "<text" in res.text:
            texts = re.findall(r'<text[^>]*>(.*?)</text>', res.text)
            clean_texts = [html.unescape(t) for t in texts]
            final_text = " ".join(clean_texts)
            
            if len(final_text) > 50:
                return final_text
    except Exception:
        pass

    backup_instances = [
        "https://pipedapi.tokhmi.xyz", 
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.syncpundit.io"
    ]
    
    for api_url in backup_instances:
        try:
            url = f"{api_url}/streams/{video_id}"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                subtitles = data.get("subtitles", [])
                if not subtitles:
                    continue
                
                sub_url = None
                for sub in subtitles:
                    if sub.get("code") in ["fa", "en"]:
                        sub_url = sub.get("url")
                        break
                if not sub_url:
                    sub_url = subtitles[0].get("url")
                    
                vtt_res = requests.get(sub_url, timeout=10)
                clean_text = []
                for line in vtt_res.text.split('\n'):
                    if '-->' in line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:') or not line.strip():
                        continue
                    clean_line = re.sub(r'<[^>]+>', '', line)
                    clean_text.append(clean_line.strip())
                
                final_text = " ".join(clean_text)
                if final_text:
                    return final_text
        except Exception:
            continue
            
    return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! من آماده‌ام. لینک ویدیوی یوتیوب رو بفرست تا سئوش کنم.")

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    try:
        url = message.text
        bot.reply_to(message, "در حال استخراج زیرنویس از طریق سرورهای مرجع... ⏳")
        
        video_id = get_video_id(url)
        if not video_id:
            bot.reply_to(message, "❌ لینک یوتیوب نامعتبر است.")
            return
            
        text = get_transcript_bypass(video_id)
        
        if not text:
            bot.reply_to(message, "❌ نتوانستم زیرنویس را استخراج کنم. (یا ویدیو اصلاً زیرنویس CC ندارد، یا دسترسی سرور مسدود است)")
            return
        
        bot.reply_to(message, "✅ زیرنویس با موفقیت استخراج شد! در حال تحلیل با هوش مصنوعی... 🧠")

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

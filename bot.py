import os
import telebot
import google.generativeai as genai
import re

bot = telebot.TeleBot(os.environ.get("TELEGRAM_TOKEN"))
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# پاک کردن زمان‌ها و کدهای اضافی از فایل SRT
def clean_srt(text):
    # حذف اعداد و تایم‌کدها (مثلاً 00:00:12,000 --> 00:00:15,000)
    text = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', text)
    return text

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        # دانلود فایل از تلگرام
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # تبدیل فایل به متن و تمیز کردن
        text = downloaded_file.decode('utf-8')
        clean_text = clean_srt(text)
        
        bot.reply_to(message, "فایل دریافت شد. در حال تحلیل هوشمند... 🤖")
        
        prompt = f"بر اساس این متن زیرنویس، یک تیتر جذاب، دیسکریپشن سئو شده، هشتگ‌ها و تگ‌های یوتیوب (کمتر از 500 کاراکتر) به فارسی بنویس:\n{clean_text[:10000]}"
        
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "خطا در خواندن فایل. مطمئن شو فایل با فرمت .srt است.")

bot.polling()import os
import telebot
import google.generativeai as genai
import re

bot = telebot.TeleBot(os.environ.get("TELEGRAM_TOKEN"))
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# پاک کردن زمان‌ها و کدهای اضافی از فایل SRT
def clean_srt(text):
    # حذف اعداد و تایم‌کدها (مثلاً 00:00:12,000 --> 00:00:15,000)
    text = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', text)
    return text

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        # دانلود فایل از تلگرام
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # تبدیل فایل به متن و تمیز کردن
        text = downloaded_file.decode('utf-8')
        clean_text = clean_srt(text)
        
        bot.reply_to(message, "فایل دریافت شد. در حال تحلیل هوشمند... 🤖")
        
        prompt = f"بر اساس این متن زیرنویس، یک تیتر جذاب، دیسکریپشن سئو شده، هشتگ‌ها و تگ‌های یوتیوب (کمتر از 500 کاراکتر) به فارسی بنویس:\n{clean_text[:10000]}"
        
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "خطا در خواندن فایل. مطمئن شو فایل با فرمت .srt است.")

bot.polling()

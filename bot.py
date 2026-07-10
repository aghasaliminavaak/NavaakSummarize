import os
import telebot
import google.generativeai as genai

bot = telebot.TeleBot(os.environ.get("TELEGRAM_TOKEN"))
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! متن زیرنویس را بفرست تا تحلیلش کنم. (اگر متن خیلی طولانی است، آن را به ۲ یا ۳ بخش تقسیم کن و بفرست).")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    if len(text) < 50:
        bot.reply_to(message, "متن خیلی کوتاه است. لطفاً متن کامل را بفرست.")
        return
        
    bot.reply_to(message, "در حال تحلیل... 🤖")
    
    try:
        # محدود کردن متن برای جلوگیری از کرش کردن سرور
        if len(text) > 10000:
            text = text[:10000]
            bot.reply_to(message, "متن طولانی بود، بخش اول آن را تحلیل می‌کنم...")
            
        prompt = f"""
        بر اساس متن زیر، این موارد را به فارسی بنویس:
        1. تیتر جذاب
        2. دیسکریپشن (توضیحات) کامل
        3. چند هشتگ مرتبط
        4. کلمات کلیدی (تگ‌ها) جدا شده با کاما (مجموعاً کمتر از 500 کاراکتر)
        
        متن:
        {text}
        """
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"خطا در پردازش. اگر متن خیلی طولانی است، آن را کوتاه‌تر کن.")

bot.polling()

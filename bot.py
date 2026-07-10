import os
import telebot
import google.generativeai as genai

bot = telebot.TeleBot(os.environ.get("TELEGRAM_TOKEN"))
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! متن زیرنویس ویدیو را برایم بفرست تا تایتل، دیسکریپشن و تگ‌ها را برایت بنویسم.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    if len(text) < 100:
        bot.reply_to(message, "متنی که فرستادی خیلی کوتاه است. لطفاً متن کامل زیرنویس را بفرست.")
        return
        
    bot.reply_to(message, "در حال تحلیل هوشمند متن... 🤖")
    
    try:
        prompt = f"""
        من متن یک ویدیو را به تو می‌دهم. لطفاً برای آن:
        1. یک تیتر جذاب (فارسی)
        2. یک دیسکریپشن (توضیحات) کامل و سئو شده (فارسی)
        3. چند هشتگ مرتبط
        4. کلمات کلیدی (تگ‌ها) جدا شده با کاما (مجموعاً کمتر از 500 کاراکتر)
        بنویس.
        
        متن ویدیو:
        {text}
        """
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "خطایی رخ داد. دوباره تلاش کن.")

bot.polling()

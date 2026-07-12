# NavaakSummarize

ربات تلگرام برای دریافت لینک یوتیوب، استخراج زیرنویس و تولید پیشنهادهای سئویی شامل عنوان، دیسکریپشن، تگ و هشتگ.

## نیازمندی‌ها

- Python 3.10 یا جدیدتر
- توکن ربات تلگرام
- کلید Gemini API

## متغیرهای محیطی

```bash
TELEGRAM_TOKEN=your-telegram-bot-token
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
PORT=8080
```

`GEMINI_MODEL` اختیاری است و در صورت تنظیم نشدن، مقدار `gemini-2.5-flash` استفاده می‌شود.

## اجرای محلی

```bash
pip install -r requirements.txt
python bot.py
```

## نکات امنیتی

- هیچ توکن، کلید API یا فایل کوکی را داخل پروژه commit نکنید.
- اگر قبلا `cookies.txt` شامل کوکی واقعی بوده، بهتر است آن نشست‌ها را باطل یا rotate کنید.

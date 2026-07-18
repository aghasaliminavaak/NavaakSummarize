import html
import logging
import os
import re
import threading
from urllib.parse import parse_qs, urlparse

import google.generativeai as genai
import requests
import telebot
from dotenv import load_dotenv
from flask import Flask


load_dotenv()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
TELEGRAM_MAX_MESSAGE_LENGTH = 4096


def get_env_int(name, default):
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError:
        logger.warning("Invalid %s=%r. Using default value: %s", name, raw_value, default)
        return default


REQUEST_TIMEOUT = get_env_int("REQUEST_TIMEOUT", 10)

missing_env = [
    name
    for name, value in {
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "GEMINI_API_KEY": GEMINI_API_KEY,
    }.items()
    if not value
]
if missing_env:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_env)}")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running."


def run_web():
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)


def get_video_id(url):
    if not url:
        return None

    url = url.strip()
    if re.match(r"^(?:www\.)?(?:youtube\.com|youtu\.be)/", url):
        url = f"https://{url}"

    parsed_url = urlparse(url)

    if parsed_url.netloc in {"youtu.be", "www.youtu.be"}:
        candidate = parsed_url.path.strip("/").split("/")[0]
        return candidate if re.fullmatch(r"[0-9A-Za-z_-]{11}", candidate or "") else None

    if parsed_url.netloc.endswith("youtube.com"):
        query_video_id = parse_qs(parsed_url.query).get("v", [None])[0]
        if query_video_id and re.fullmatch(r"[0-9A-Za-z_-]{11}", query_video_id):
            return query_video_id

        path_match = re.search(
            r"/(?:shorts|embed|live)/([0-9A-Za-z_-]{11})(?:\b|/)?",
            parsed_url.path,
        )
        if path_match:
            return path_match.group(1)

    return None


def fetch_url(url):
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response


def clean_vtt(vtt_text):
    clean_text = []
    for raw_line in vtt_text.splitlines():
        line = raw_line.strip()
        if (
            not line
            or "-->" in line
            or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE"))
            or re.fullmatch(r"\d+", line)
        ):
            continue

        line = re.sub(r"<[^>]+>", "", line)
        line = html.unescape(line).strip()
        if line:
            clean_text.append(line)

    return " ".join(clean_text)


def get_transcript_bypass(video_id):
    primary_url = f"https://youtubetranscript.com/?server_vid2={video_id}"
    try:
        response = fetch_url(primary_url)
        if "<text" in response.text:
            texts = re.findall(r"<text[^>]*>(.*?)</text>", response.text, re.DOTALL)
            final_text = " ".join(html.unescape(text).strip() for text in texts if text.strip())
            if len(final_text) > 50:
                return final_text
    except requests.RequestException:
        logger.warning("Primary transcript provider failed", exc_info=True)

    backup_instances = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.syncpundit.io",
    ]

    for api_url in backup_instances:
        try:
            response = fetch_url(f"{api_url}/streams/{video_id}")
            subtitles = response.json().get("subtitles", [])
            if not subtitles:
                continue

            subtitle = next(
                (item for item in subtitles if item.get("code") in {"fa", "en"}),
                subtitles[0],
            )
            sub_url = subtitle.get("url")
            if not sub_url:
                continue

            vtt_response = fetch_url(sub_url)
            final_text = clean_vtt(vtt_response.text)
            if len(final_text) > 50:
                return final_text
        except (requests.RequestException, ValueError, KeyError, TypeError):
            logger.warning("Backup transcript provider failed: %s", api_url, exc_info=True)

    return None


def build_prompt(text):
    return f"""
تو یک متخصص سئو و تولید محتوا برای یوتیوب هستی. بر اساس متن زیرنویس این ویدیو:
1. سه عنوان جذاب، دقیق و کلیک‌خور به فارسی پیشنهاد بده.
2. یک دیسکریپشن حرفه‌ای و سئوشده بنویس.
3. تگ‌ها و هشتگ‌های مناسب را لیست کن.

متن ویدیو:
{text[:10000]}
""".strip()


def send_long_message(chat_id, text):
    if not text:
        bot.send_message(chat_id, "پاسخی از مدل دریافت نشد.")
        return

    for start in range(0, len(text), TELEGRAM_MAX_MESSAGE_LENGTH):
        bot.send_message(chat_id, text[start : start + TELEGRAM_MAX_MESSAGE_LENGTH])


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(
        message,
        "سلام! لینک ویدیوی یوتیوب را بفرست تا از روی زیرنویس، عنوان، دیسکریپشن و تگ پیشنهاد بدهم.",
    )


@bot.message_handler(content_types=["text"])
def handle_link(message):
    url = (message.text or "").strip()
    video_id = get_video_id(url)

    if not video_id:
        bot.reply_to(message, "لینک یوتیوب معتبر نیست. لطفا لینک کامل ویدیو را بفرست.")
        return

    try:
        bot.reply_to(message, "در حال استخراج زیرنویس ویدیو...")
        text = get_transcript_bypass(video_id)

        if not text:
            bot.reply_to(
                message,
                "نتوانستم زیرنویس را استخراج کنم. ممکن است ویدیو زیرنویس عمومی نداشته باشد یا سرویس‌های زیرنویس در دسترس نباشند.",
            )
            return

        bot.reply_to(message, "زیرنویس استخراج شد. در حال تحلیل با هوش مصنوعی...")
        response = model.generate_content(build_prompt(text))
        send_long_message(message.chat.id, getattr(response, "text", ""))
    except Exception:
        logger.exception("Failed to process Telegram message")
        bot.reply_to(message, "خطا در پردازش درخواست. لطفا کمی بعد دوباره تلاش کن.")


if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.infinity_polling(skip_pending=True)

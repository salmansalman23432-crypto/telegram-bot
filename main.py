import os
import json
import threading
import telebot
from flask import Flask
from telebot import types

# =========================
# إعدادات
# =========================

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN:
    raise Exception("Missing TELEGRAM_TOKEN")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# =========================
# Flask (حل Render)
# =========================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# البيانات
# =========================

def load():
    try:
        with open("market.json", "r") as f:
            return json.load(f)
    except:
        return {
            "gold": {},
            "silver": {},
            "currency": {}
        }

def save(data):
    with open("market.json", "w") as f:
        json.dump(data, f, indent=2)

# =========================
# UI
# =========================

def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📊 السوق")
    kb.row("💱 العملات", "🪙 الذهب", "🥈 الفضة")
    return kb

# =========================
# رسالة البداية
# =========================

def start_message():
    try:
        bot.send_message(CHAT_ID, "🚀 V6.1 Bot Online")
    except:
        pass

# =========================
# /start
# =========================

@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, "👋 أهلاً بك", reply_markup=menu())

# =========================
# السوق
# =========================

@bot.message_handler(func=lambda m: m.text == "📊 السوق")
def market(msg):
    data = load()

    text = "📊 <b>السوق</b>\n\n"

    icons = {
        "gold": "🪙 الذهب",
        "silver": "🥈 الفضة",
        "currency": "💱 العملات"
    }

    for cat, values in data.items():
        text += f"{icons.get(cat, cat)}:\n"

        for k, v in values.items():
            text += f" - {k}: <b>{v}</b>\n"

        text += "\n"

    bot.send_message(msg.chat.id, text)

# =========================
# /set
# =========================

@bot.message_handler(commands=['set'])
def set_value(msg):
    try:
        parts = msg.text.split()

        if len(parts) != 4:
            bot.reply_to(msg, "❌ /set gold scrap 4700")
            return

        cat = parts[1].lower()
        key = parts[2].lower()
        value = float(parts[3])

        data = load()

        if cat not in data or key not in data[cat]:
            bot.reply_to(msg, "❌ غير موجود")
            return

        data[cat][key] = value
        save(data)

        bot.reply_to(msg, f"✅ {cat} → {key} = {value}")

    except Exception as e:
        print("SET ERROR:", e)
        bot.reply_to(msg, "❌ خطأ في الإدخال")

# =========================
# fallback
# =========================

@bot.message_handler(func=lambda m: m.content_type == 'text')
def fallback(msg):
    if not msg.text.startswith('/'):
        bot.reply_to(msg, "استخدم الأزرار")

# =========================
# تشغيل البوت (مصَحح)
# =========================

def run_bot():
    bot.remove_webhook()
    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )

# =========================
# التشغيل
# =========================

if __name__ == "__main__":
    start_message()

    threading.Thread(target=run_web).start()

    run_bot()
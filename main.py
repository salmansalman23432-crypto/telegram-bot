import os
import json
import threading
import telebot
from flask import Flask

# =========================
# Telegram Bot Setup
# =========================

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# =========================
# Flask Web Server (IMPORTANT for Render)
# =========================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# Data Storage
# =========================

def load():
    try:
        with open("market.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save(data):
    with open("market.json", "w") as f:
        json.dump(data, f, indent=2)

# =========================
# Start message
# =========================

def start_message():
    try:
        bot.send_message(CHAT_ID, "🚀 V5 Web Service Bot is LIVE")
    except:
        pass

# =========================
# Commands
# =========================

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "✅ Bot is running on Web Service")

@bot.message_handler(commands=['set'])
def set_price(msg):
    try:
        parts = msg.text.split()

        category = parts[1].lower()
        key = parts[2].lower()
        value = float(parts[3])

        data = load()

        if category not in data:
            bot.reply_to(msg, "❌ category not found")
            return

        if key not in data[category]:
            bot.reply_to(msg, "❌ key not found")
            return

        data[category][key] = value
        save(data)

        bot.reply_to(msg, f"✅ updated {category} → {key} = {value}")

    except:
        bot.reply_to(msg, "❌ usage: /set gold scrap 4700")

@bot.message_handler(commands=['market'])
def market(msg):
    data = load()

    text = "📊 <b>Market Status</b>\n\n"

    for cat, values in data.items():
        text += f"🔹 {cat.upper()}:\n"
        for k, v in values.items():
            text += f" - {k}: <b>{v}</b>\n"
        text += "\n"

    bot.reply_to(msg, text)

# =========================
# Safety fallback
# =========================

@bot.message_handler(func=lambda m: True)
def fallback(msg):
    bot.reply_to(msg, "Use /start /market /set")

# =========================
# Telegram polling loop (stable)
# =========================

def run_bot():
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print("Bot error:", e)

# =========================
# START ALL
# =========================

if __name__ == "__main__":
    start_message()

    # تشغيل السيرفر (هذا يحل مشكلة Render Port scan)
    threading.Thread(target=run_web, daemon=True).start()

    # تشغيل البوت
    run_bot()

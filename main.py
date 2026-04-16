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
# Flask (حل مشكلة Render Port)
# =========================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# Data
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
# UI (Buttons)
# =========================

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row("📊 السوق")
    kb.row("💱 العملات", "🪙 الذهب", "🥈 الفضة")

    return kb

# =========================
# Start message
# =========================

def start_message():
    try:
        bot.send_message(CHAT_ID, "🚀 V5.1 System Online")
    except:
        pass

# =========================
# Start
# =========================

@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(
        msg.chat.id,
        "👋 أهلاً بك في نظام السوق الليبي",
        reply_markup=main_menu()
    )

# =========================
# Market display
# =========================

@bot.message_handler(func=lambda m: m.text == "📊 السوق")
def show_market(msg):
    data = load()

    text = "📊 <b>السوق الليبي</b>\n\n"

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
# Menus (UI placeholders)
# =========================

@bot.message_handler(func=lambda m: m.text == "💱 العملات")
def currency_menu(msg):
    bot.send_message(msg.chat.id, "💱 اختر عملة للتحديث (لاحقًا تطوير تحويل ذكي)")

@bot.message_handler(func=lambda m: m.text == "🪙 الذهب")
def gold_menu(msg):
    bot.send_message(msg.chat.id, "🪙 اختر نوع الذهب (new / used / scrap / cast)")

@bot.message_handler(func=lambda m: m.text == "🥈 الفضة")
def silver_menu(msg):
    bot.send_message(msg.chat.id, "🥈 اختر نوع الفضة (new / used)")

# =========================
# Set command
# =========================

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

# =========================
# fallback
# =========================

@bot.message_handler(func=lambda m: True)
def fallback(msg):
    bot.reply_to(msg, "استخدم الأزرار أو /market")

# =========================
# Run bot safely
# =========================

def run_bot():
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print("Bot error:", e)

# =========================
# START EVERYTHING
# =========================

if __name__ == "__main__":
    start_message()

    threading.Thread(target=run_web, daemon=True).start()

    run_bot()

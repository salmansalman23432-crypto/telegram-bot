import os
import json
import threading
import telebot
from flask import Flask
from telebot import types

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# Data
# =========================

def load():
    try:
        with open("market.json") as f:
            return json.load(f)
    except:
        return {"gold": {}, "silver": {}, "currency": {}}

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
    kb.row("🧮 تحويل العملات")
    return kb

# =========================
# State
# =========================

user_state = {}

# =========================
# START
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
    text = "📊 السوق:\n\n"

    for cat, values in data.items():
        text += f"{cat}:\n"
        for k, v in values.items():
            text += f" - {k}: {v}\n"
        text += "\n"

    bot.send_message(msg.chat.id, text)

# =========================
# العملات
# =========================

@bot.message_handler(func=lambda m: m.text == "💱 العملات")
def currency_menu(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("usd", "eur")
    kb.row("try", "egp", "tnd")
    kb.row("🔙 رجوع")
    bot.send_message(msg.chat.id, "اختر العملة:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["usd","eur","try","egp","tnd"])
def currency_input(msg):
    user_state[msg.chat.id] = ("currency", msg.text)
    bot.send_message(msg.chat.id, f"أدخل سعر {msg.text}:")

# =========================
# الذهب
# =========================

@bot.message_handler(func=lambda m: m.text == "🪙 الذهب")
def gold_menu(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("new", "used")
    kb.row("scrap", "cast")
    kb.row("🔙 رجوع")
    bot.send_message(msg.chat.id, "اختر النوع:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["new","used","scrap","cast"])
def gold_input(msg):
    user_state[msg.chat.id] = ("gold", msg.text)
    bot.send_message(msg.chat.id, f"أدخل السعر:")

# =========================
# الفضة
# =========================

@bot.message_handler(func=lambda m: m.text == "🥈 الفضة")
def silver_menu(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("new", "used")
    kb.row("🔙 رجوع")
    bot.send_message(msg.chat.id, "اختر النوع:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["new","used"] and m.chat.id in user_state and user_state[m.chat.id][0] != "gold")
def silver_input(msg):
    user_state[msg.chat.id] = ("silver", msg.text)
    bot.send_message(msg.chat.id, "أدخل السعر:")

# =========================
# التحويل
# =========================

@bot.message_handler(func=lambda m: m.text == "🧮 تحويل العملات")
def convert_start(msg):
    user_state[msg.chat.id] = "convert_amount"
    bot.send_message(msg.chat.id, "أدخل المبلغ:")

@bot.message_handler(func=lambda m: m.chat.id in user_state and user_state[m.chat.id] == "convert_amount")
def convert_amount(msg):
    try:
        amount = float(msg.text)
        user_state[msg.chat.id] = ("convert_from", amount)

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("usd","eur","tnd","try","egp")

        bot.send_message(msg.chat.id, "من أي عملة؟", reply_markup=kb)

    except:
        bot.send_message(msg.chat.id, "❌ أدخل رقم صحيح")

@bot.message_handler(func=lambda m: m.chat.id in user_state and isinstance(user_state[m.chat.id], tuple) and user_state[m.chat.id][0] == "convert_from")
def convert_from(msg):
    amount = user_state[msg.chat.id][1]
    user_state[msg.chat.id] = ("convert_to", amount, msg.text.lower())

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("usd","eur","tnd","try","egp")

    bot.send_message(msg.chat.id, "إلى أي عملة؟", reply_markup=kb)

@bot.message_handler(func=lambda m: m.chat.id in user_state and isinstance(user_state[m.chat.id], tuple) and user_state[m.chat.id][0] == "convert_to")
def convert_to(msg):
    _, amount, from_currency = user_state[msg.chat.id]
    to_currency = msg.text.lower()

    data = load()

    try:
        from_rate = data["currency"][from_currency]
        to_rate = data["currency"][to_currency]

        result = (amount * to_rate) / from_rate

        bot.send_message(msg.chat.id,
            f"💱 {amount} {from_currency} = {round(result,2)} {to_currency}",
            reply_markup=menu()
        )

        del user_state[msg.chat.id]

    except:
        bot.send_message(msg.chat.id, "❌ تأكد من إدخال الأسعار")

# =========================
# حفظ القيم (مقيد)
# =========================

@bot.message_handler(func=lambda m: m.chat.id in user_state and isinstance(user_state[m.chat.id], tuple) and user_state[m.chat.id][0] in ["gold","silver","currency"])
def save_value(msg):
    try:
        cat, key = user_state[msg.chat.id]
        value = float(msg.text)

        data = load()
        data[cat][key] = value
        save(data)

        bot.send_message(msg.chat.id, f"✅ تم الحفظ", reply_markup=menu())
        del user_state[msg.chat.id]

    except:
        bot.send_message(msg.chat.id, "❌ أدخل رقم صحيح")

# =========================
# رجوع
# =========================

@bot.message_handler(func=lambda m: m.text == "🔙 رجوع")
def back(msg):
    bot.send_message(msg.chat.id, "رجوع", reply_markup=menu())

# =========================
# تشغيل
# =========================

def run_bot():
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    run_bot()
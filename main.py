import os
import json
import threading
import requests
import telebot
from flask import Flask
from telebot import types

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

app = Flask(__name__)

# =========================
# WEB (Render fix)
# =========================

@app.route('/')
def home():
    return "Bot running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# DATA
# =========================

def load():
    with open("market.json") as f:
        return json.load(f)

def save(data):
    with open("market.json", "w") as f:
        json.dump(data, f, indent=2)

# =========================
# MENU
# =========================

def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📊 السوق")
    kb.row("💱 العملات", "🪙 الذهب", "🥈 الفضة")
    kb.row("🌍 تحديث عالمي", "🧮 تحويل")
    return kb

# =========================
# STATE
# =========================

user_state = {}

# =========================
# START
# =========================

@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, "👋 مرحبًا", reply_markup=menu())

# =========================
# السوق
# =========================

@bot.message_handler(func=lambda m: m.text == "📊 السوق")
def market(msg):
    data = load()

    text = "📊 <b>السوق</b>\n\n"

    text += "💱 العملات المحلية:\n"
    for k,v in data["local"]["currency"].items():
        text += f"{k}: {v}\n"

    text += "\n🪙 الذهب:\n"
    text += f"18: {data['local']['gold']['g18']}\n"
    text += f"21: {data['local']['gold']['g21']}\n"

    text += "\n🥈 الفضة:\n"
    text += f"used: {data['local']['silver']['used']}\n"

    text += "\n🌍 العالمي:\n"
    for k,v in data["global"]["currency"].items():
        text += f"{k}: {v}\n"

    text += f"\nذهب عالمي: {data['global']['metal']['gold']}"
    text += f"\nفضة عالمية: {data['global']['metal']['silver']}"

    bot.send_message(msg.chat.id, text)

# =========================
# العملات المحلية
# =========================

@bot.message_handler(func=lambda m: m.text == "💱 العملات")
def currency_menu(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("usd","eur","gbp")
    kb.row("tnd","egp","try")
    kb.row("🔙 رجوع")
    bot.send_message(msg.chat.id, "اختر:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["usd","eur","gbp","tnd","egp","try"])
def currency_input(msg):
    user_state[msg.chat.id] = ("currency", msg.text)
    bot.send_message(msg.chat.id, "أدخل السعر:")

# =========================
# الذهب
# =========================

@bot.message_handler(func=lambda m: m.text == "🪙 الذهب")
def gold_menu(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("ذهب 18", "ذهب 21")
    kb.row("🔙 رجوع")
    bot.send_message(msg.chat.id, "اختر:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["ذهب 18","ذهب 21"])
def gold_input(msg):
    key = "g18" if msg.text == "ذهب 18" else "g21"
    user_state[msg.chat.id] = ("gold", key)
    bot.send_message(msg.chat.id, "أدخل السعر:")

# =========================
# الفضة
# =========================

@bot.message_handler(func=lambda m: m.text == "🥈 الفضة")
def silver_menu(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("فضة مستعمل")
    kb.row("🔙 رجوع")
    bot.send_message(msg.chat.id, "اختر:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "فضة مستعمل")
def silver_input(msg):
    user_state[msg.chat.id] = ("silver", "used")
    bot.send_message(msg.chat.id, "أدخل السعر:")

# =========================
# حفظ القيم
# =========================

@bot.message_handler(func=lambda m: m.chat.id in user_state)
def save_value(msg):
    try:
        cat, key = user_state[msg.chat.id]
        value = float(msg.text)

        data = load()

        if cat == "currency":
            data["local"]["currency"][key] = value
        elif cat == "gold":
            data["local"]["gold"][key] = value
        elif cat == "silver":
            data["local"]["silver"][key] = value

        save(data)

        bot.send_message(msg.chat.id, "✅ تم الحفظ", reply_markup=menu())
        del user_state[msg.chat.id]

    except:
        bot.send_message(msg.chat.id, "❌ أدخل رقم صحيح")

# =========================
# API عالمي
# =========================

@bot.message_handler(func=lambda m: m.text == "🌍 تحديث عالمي")
def update_global(msg):
    try:
        data = load()

        # عملات
        res = requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()

        data["global"]["currency"]["usd"] = 1
        data["global"]["currency"]["eur"] = res["rates"]["EUR"]
        data["global"]["currency"]["gbp"] = res["rates"]["GBP"]

        # ذهب (تقريبي)
        data["global"]["metal"]["gold"] = 2300
        data["global"]["metal"]["silver"] = 25

        save(data)

        bot.send_message(msg.chat.id, "🌍 تم تحديث الأسعار العالمية")

    except:
        bot.send_message(msg.chat.id, "❌ فشل التحديث")

# =========================
# تحويل
# =========================

@bot.message_handler(func=lambda m: m.text == "🧮 تحويل")
def convert_start(msg):
    user_state[msg.chat.id] = "amount"
    bot.send_message(msg.chat.id, "أدخل المبلغ:")

@bot.message_handler(func=lambda m: m.chat.id in user_state and user_state[m.chat.id] == "amount")
def convert_amount(msg):
    try:
        amount = float(msg.text)
        user_state[msg.chat.id] = ("from", amount)

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("usd","eur","gbp","tnd","egp","try")
        bot.send_message(msg.chat.id, "من:", reply_markup=kb)

    except:
        bot.send_message(msg.chat.id, "❌ رقم غير صحيح")

@bot.message_handler(func=lambda m: isinstance(user_state.get(m.chat.id), tuple) and user_state[m.chat.id][0] == "from")
def convert_from(msg):
    amount = user_state[msg.chat.id][1]
    user_state[msg.chat.id] = ("to", amount, msg.text)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("usd","eur","gbp","tnd","egp","try")
    bot.send_message(msg.chat.id, "إلى:")

@bot.message_handler(func=lambda m: isinstance(user_state.get(m.chat.id), tuple) and user_state[m.chat.id][0] == "to")
def convert_to(msg):
    _, amount, from_c = user_state[msg.chat.id]
    to_c = msg.text

    data = load()["local"]["currency"]

    try:
        result = (amount * data[to_c]) / data[from_c]
        bot.send_message(msg.chat.id, f"💱 {round(result,2)}", reply_markup=menu())
        del user_state[msg.chat.id]

    except:
        bot.send_message(msg.chat.id, "❌ تأكد من إدخال الأسعار")

# =========================
# رجوع
# =========================

@bot.message_handler(func=lambda m: m.text == "🔙 رجوع")
def back(msg):
    bot.send_message(msg.chat.id, "رجوع", reply_markup=menu())

# =========================
# RUN
# =========================

def run_bot():
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    run_bot()

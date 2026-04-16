import os
import json
import telebot
from telebot import types

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(TOKEN)

# =========================
# تحميل / حفظ
# =========================

def load():
    try:
        with open("market.json") as f:
            return json.load(f)
    except:
        return {}

def save(data):
    with open("market.json", "w") as f:
        json.dump(data, f, indent=2)

# =========================
# القائمة الرئيسية
# =========================

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("📊 السوق")
    kb.add("💱 العملات", "🪙 الذهب", "🥈 الفضة")

    return kb

# =========================
# بدء
# =========================

@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, "👋 أهلاً بك", reply_markup=main_menu())

# =========================
# عرض السوق
# =========================

@bot.message_handler(func=lambda m: m.text == "📊 السوق")
def show_market(msg):
    data = load()

    text = "📊 السوق:\n\n"

    for cat, values in data.items():
        text += f"{cat}:\n"
        for k, v in values.items():
            text += f" - {k}: {v}\n"
        text += "\n"

    bot.send_message(msg.chat.id, text)

# =========================
# اختيار العملات
# =========================

@bot.message_handler(func=lambda m: m.text == "💱 العملات")
def currency_menu(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("USD", "EUR")
    kb.add("TRY", "EGP", "TND")
    kb.add("🔙 رجوع")

    bot.send_message(msg.chat.id, "اختر العملة:", reply_markup=kb)

# =========================
# اختيار الذهب
# =========================

@bot.message_handler(func=lambda m: m.text == "🪙 الذهب")
def gold_menu(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("new", "used")
    kb.add("scrap", "cast")
    kb.add("🔙 رجوع")

    bot.send_message(msg.chat.id, "اختر النوع:", reply_markup=kb)

# =========================
# اختيار الفضة
# =========================

@bot.message_handler(func=lambda m: m.text == "🥈 الفضة")
def silver_menu(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("new", "used")
    kb.add("🔙 رجوع")

    bot.send_message(msg.chat.id, "اختر النوع:", reply_markup=kb)

# =========================
# رجوع
# =========================

@bot.message_handler(func=lambda m: m.text == "🔙 رجوع")
def back(msg):
    bot.send_message(msg.chat.id, "القائمة الرئيسية", reply_markup=main_menu())

# =========================
# إدخال السعر
# =========================

user_state = {}

@bot.message_handler(func=lambda m: m.text in ["USD","EUR","TRY","EGP","TND","new","used","scrap","cast"])
def ask_price(msg):
    user_state[msg.chat.id] = msg.text.lower()
    bot.send_message(msg.chat.id, f"أدخل السعر لـ {msg.text}:")

# =========================
# استقبال الرقم
# =========================

@bot.message_handler(func=lambda m: True)
def receive_value(msg):
    if msg.chat.id not in user_state:
        return

    key = user_state[msg.chat.id]

    try:
        value = float(msg.text)

        data = load()

        if key in ["usd","eur","try","egp","tnd"]:
            data["currency"][key] = value
        elif key in ["new","used","scrap","cast"]:
            data["gold"][key] = value
        else:
            data["silver"][key] = value

        save(data)

        bot.send_message(msg.chat.id, f"✅ تم حفظ {key} = {value}", reply_markup=main_menu())

        del user_state[msg.chat.id]

    except:
        bot.send_message(msg.chat.id, "❌ أدخل رقم صحيح")

# =========================
# تشغيل
# =========================

bot.remove_webhook()
bot.infinity_polling()
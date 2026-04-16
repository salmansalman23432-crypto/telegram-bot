import os
import json
import telebot

# =========================
# إعدادات
# =========================

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(TOKEN)

# =========================
# رموز السوق (Emojis)
# =========================

ICONS = {
    "gold": "🪙 الذهب",
    "silver": "🥈 الفضة",
    "usd": "💵 الدولار",
    "eur": "💶 اليورو",
    "try": "🇹🇷 الليرة التركية",
    "egp": "🇪🇬 الجنيه المصري",
    "tnd": "🇹🇳 الدينار التونسي"
}

# =========================
# تحميل / حفظ
# =========================

def load_market():
    try:
        with open("market.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_market(data):
    with open("market.json", "w") as f:
        json.dump(data, f)

# =========================
# تحديث يدوي
# =========================

@bot.message_handler(commands=['set'])
def set_price(msg):
    try:
        parts = msg.text.split()

        category = parts[1].lower()   # gold / silver / currency
        key = parts[2].lower()        # usd / new / scrap
        value = float(parts[3])

        data = load_market()

        if category not in data:
            data[category] = {}

        data[category][key] = value
        save_market(data)

        bot.reply_to(msg, f"✅ تم تحديث {category} - {key} = {value}")

    except:
        bot.reply_to(msg, "❌ الاستخدام:\n/set gold scrap 4700")

# =========================
# عرض السوق
# =========================

@bot.message_handler(commands=['market'])
def show_market(msg):
    data = load_market()

    text = "📊 السوق الليبي الحالي:\n\n"

    for category, values in data.items():
        text += f"{ICONS.get(category, category)}:\n"

        for k, v in values.items():
            text += f" - {k}: {v}\n"

        text += "\n"

    bot.reply_to(msg, text)

# =========================
# تحليل بسيط للذهب
# =========================

def analyze_gold(data):
    g = data.get("gold", {})

    new = g.get("new", 0)
    scrap = g.get("scrap", 0)
    cast = g.get("cast", 0)

    alerts = []

    if new and scrap:
        diff = ((new - scrap) / new) * 100
        if diff > 10:
            alerts.append("⚠️ فرق كبير بين الذهب الجديد والكسر")

    if new and cast:
        diff = ((new - cast) / new) * 100
        if diff < 1:
            alerts.append("📊 المسبوك قريب جدًا من الجديد")

    return alerts

# =========================
# فحص دوري
# =========================

def check_market():
    data = load_market()

    alerts = analyze_gold(data)

    if alerts:
        bot.send_message(CHAT_ID, "📢 تنبيه سوق:\n\n" + "\n".join(alerts))

# =========================
# تشغيل أولي
# =========================

def start_message():
    try:
        with open("started.flag", "r"):
            return
    except:
        bot.send_message(CHAT_ID, "🚀 V4 اليدوي الذكي بدأ العمل")
        open("started.flag", "w").write("ok")

# =========================
# تشغيل مستمر
# =========================

import time
import threading

def loop():
    while True:
        try:
            check_market()
            time.sleep(300)
        except:
            time.sleep(60)

start_message()
threading.Thread(target=loop).start()

bot.infinity_polling()
import os
import json
import telebot

# =========================
# إعدادات
# =========================

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# =========================
# رموز
# =========================

ICONS = {
    "gold": "🪙 الذهب",
    "silver": "🥈 الفضة",
    "currency": "💱 العملات",
    "usd": "💵 الدولار",
    "eur": "💶 اليورو",
    "try": "🇹🇷 الليرة التركية",
    "egp": "🇪🇬 الجنيه المصري",
    "tnd": "🇹🇳 الدينار التونسي"
}

# =========================
# تحميل / حفظ
# =========================

def load_data():
    try:
        with open("market.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open("market.json", "w") as f:
        json.dump(data, f, indent=2)

# =========================
# رسالة بدء (مرة واحدة)
# =========================

def send_start():
    try:
        with open("started.flag", "r"):
            return
    except:
        bot.send_message(CHAT_ID, "🚀 <b>V4 Market System يعمل الآن</b>")
        open("started.flag", "w").write("ok")

# =========================
# أمر /set
# =========================

@bot.message_handler(commands=['set'])
def set_price(msg):
    try:
        parts = msg.text.split()

        if len(parts) != 4:
            raise Exception()

        category = parts[1].lower()
        key = parts[2].lower()
        value = float(parts[3])

        data = load_data()

        if category not in data:
            bot.reply_to(msg, "❌ قسم غير موجود")
            return

        if key not in data[category]:
            bot.reply_to(msg, "❌ نوع غير موجود")
            return

        data[category][key] = value
        save_data(data)

        bot.reply_to(msg, f"✅ تم تحديث {category} → {key} = {value}")

    except:
        bot.reply_to(msg, "❌ الاستخدام:\n/set gold scrap 4700")

# =========================
# أمر /market
# =========================

@bot.message_handler(commands=['market'])
def show_market(msg):
    data = load_data()

    text = "📊 <b>السوق الليبي الآن:</b>\n\n"

    for category, values in data.items():
        text += f"{ICONS.get(category, category)}:\n"

        for k, v in values.items():
            icon = ICONS.get(k, "")
            text += f" - {icon} {k}: <b>{v}</b>\n"

        text += "\n"

    bot.reply_to(msg, text)

# =========================
# أمر /help
# =========================

@bot.message_handler(commands=['help'])
def help_cmd(msg):
    text = """
📌 الأوامر:

/set gold new 4850
/set gold scrap 4700
/set silver new 60
/set currency usd 5.2

/market → عرض السوق
"""
    bot.reply_to(msg, text)

# =========================
# أي رسالة أخرى
# =========================

@bot.message_handler(func=lambda m: True)
def fallback(msg):
    bot.reply_to(msg, "❌ استخدم /help لمعرفة الأوامر")

# =========================
# تشغيل
# =========================

send_start()

# أهم سطر (حل كل المشاكل)
bot.remove_webhook()

bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
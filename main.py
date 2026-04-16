import os
import json
import time
import requests
import telebot

# ===== إعدادات =====
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(TOKEN)

# ===== العملات والمعادن =====
ASSETS = {
    "gold": "XAU",
    "silver": "XAG",
    "usd": "USD",
    "eur": "EUR",
    "tnd": "TND",
    "egp": "EGP",
    "try": "TRY"
}

# ===== تحميل البيانات =====
def load_data():
    try:
        with open("prices.json", "r") as f:
            return json.load(f)
    except:
        return {"data": {}}

def save_data(data):
    with open("prices.json", "w") as f:
        json.dump(data, f)

# ===== جلب السعر العالمي =====
def get_price(symbol):
    try:
        if symbol in ["XAU", "XAG"]:
            url = f"https://api.gold-api.com/price/{symbol}"
            res = requests.get(url).json()
            return float(res["price"])
        else:
            # API صرف العملات
            url = f"https://open.er-api.com/v6/latest/USD"
            res = requests.get(url).json()
            rate = res["rates"].get(symbol, 0)
            return float(rate)
    except:
        return 0

# ===== تحليل التغير =====
def analyze(old, new):
    if old == 0:
        return "🆕 أول تسجيل"

    diff = abs(new - old)
    percent = (diff / old) * 100 if old else 0

    if percent > 1:
        return "⚠️ تغير قوي"
    elif percent > 0.3:
        return "📊 تغير متوسط"
    else:
        return "➖ استقرار"

# ===== تشغيل الفحص =====
def check_all():
    db = load_data()
    old_data = db.get("data", {})

    messages = []

    for name, symbol in ASSETS.items():
        new_price = get_price(symbol)
        old_price = old_data.get(name, 0)

        status = analyze(old_price, new_price)

        if old_price == 0:
            old_data[name] = new_price
            continue

        if abs(new_price - old_price) > 0:
            messages.append(f"{name.upper()}:\n{old_price} ➜ {new_price}\n{status}\n")

        old_data[name] = new_price

    if messages:
        bot.send_message(CHAT_ID, "📊 تحديث السوق:\n\n" + "\n".join(messages))

    db["data"] = old_data
    save_data(db)

# ===== تشغيل البوت =====
bot.send_message(CHAT_ID, "🚀 V2 ليبيا بدأ العمل (ذهب + عملات)")

while True:
    try:
        check_all()
        time.sleep(300)
    except Exception as e:
        print("Error:", e)
        time.sleep(60)
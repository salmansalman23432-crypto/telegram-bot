import os
import json
import re
import threading
import telebot
from flask import Flask
from telebot import types

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# =========================
# WEB
# =========================

@app.route('/')
def home():
    return "Running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# DATA
# =========================

def load():
    try:
        with open("market.json") as f:
            return json.load(f)
    except:
        return {
            "sources": {
                "usd": [0,0,0,0],
                "eur": [0,0,0,0],
                "gbp": [0,0,0,0],
                "tnd": [0,0,0,0],
                "egp": [0,0,0,0],
                "try": [0,0,0,0]
            },
            "metals": {
                "g18": 0,
                "g21": 0,
                "silver": 0
            }
        }

def save(data):
    with open("market.json","w") as f:
        json.dump(data,f,indent=2)

# =========================
# تحليل النص
# =========================

def extract(text):
    data = {}

    patterns = {
        "usd": r'الدولار.*?(\d+\.\d+)',
        "eur": r'اليورو.*?(\d+\.\d+)',
        "gbp": r'الباوند.*?(\d+\.\d+)',
        "tnd": r'صك.*?(\d+\.\d+)',
        "egp": r'جنيه.*?(\d+\.\d+)',
        "try": r'ليرة.*?(\d+\.\d+)',
        "g18": r'18.*?(\d+)',
        "g21": r'21.*?(\d+)',
        "silver": r'فضة.*?(\d+\.\d+)'
    }

    for k, p in patterns.items():
        match = re.findall(p, text)
        if match:
            data[k] = float(match[-1])

    return data

# =========================
# فلترة + متوسط
# =========================

def clean(vals):
    vals = [v for v in vals if v > 0]
    if not vals:
        return []
    avg = sum(vals)/len(vals)
    return [v for v in vals if abs(v-avg) < 0.3]

def avg(vals):
    vals = clean(vals)
    if not vals:
        return 0
    return round(sum(vals)/len(vals),3)

# =========================
# MENU
# =========================

def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📥 إدخال نص")
    kb.row("📊 السوق")
    kb.row("🪙 تحديث المعادن")
    return kb

state = {}

# =========================
# START
# =========================

@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id,"👋 أهلا",reply_markup=menu())

# =========================
# إدخال النص
# =========================

@bot.message_handler(func=lambda m: m.text == "📥 إدخال نص")
def ask_text(msg):
    state[msg.chat.id] = "waiting_text"
    bot.send_message(msg.chat.id,"📩 أرسل نص السوق:")

@bot.message_handler(func=lambda m: state.get(m.chat.id) == "waiting_text")
def process_text(msg):
    data = load()
    extracted = extract(msg.text)

    # اختيار مصدر
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("1","2","3","4")

    state[msg.chat.id] = ("choose_source", extracted)
    bot.send_message(msg.chat.id,f"📌 تم استخراج:\n{extracted}\nاختر المصدر:",reply_markup=kb)

@bot.message_handler(func=lambda m: isinstance(state.get(m.chat.id),tuple) and state[m.chat.id][0]=="choose_source")
def save_source(msg):
    idx = int(msg.text)-1
    extracted = state[msg.chat.id][1]

    data = load()

    for k,v in extracted.items():
        if k in data["sources"]:
            data["sources"][k][idx] = v
        else:
            data["metals"][k] = v

    save(data)

    bot.send_message(msg.chat.id,"✅ تم حفظ المصدر",reply_markup=menu())
    del state[msg.chat.id]

# =========================
# عرض السوق
# =========================

@bot.message_handler(func=lambda m: m.text == "📊 السوق")
def market(msg):
    data = load()

    text = "📊 السوق:\n\n"

    for k,v in data["sources"].items():
        text += f"{k}: {avg(v)}\n"

    text += "\n🪙 المعادن:\n"
    for k,v in data["metals"].items():
        text += f"{k}: {v}\n"

    bot.send_message(msg.chat.id,text)

# =========================
# المعادن يدوي
# =========================

@bot.message_handler(func=lambda m: m.text == "🪙 تحديث المعادن")
def metals(msg):
    state[msg.chat.id] = "metals"
    bot.send_message(msg.chat.id,"اكتب:\n18=900\n21=970\nsilver=18.5")

@bot.message_handler(func=lambda m: state.get(m.chat.id) == "metals")
def save_metals(msg):
    data = load()

    lines = msg.text.split("\n")

    for line in lines:
        if "=" in line:
            k,v = line.split("=")
            if "18" in k:
                data["metals"]["g18"]=float(v)
            elif "21" in k:
                data["metals"]["g21"]=float(v)
            elif "silver" in k:
                data["metals"]["silver"]=float(v)

    save(data)

    bot.send_message(msg.chat.id,"✅ تم تحديث المعادن",reply_markup=menu())
    del state[msg.chat.id]

# =========================
# RUN
# =========================

def run_bot():
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    run_bot()
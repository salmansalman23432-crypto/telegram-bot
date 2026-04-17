import os, json, re, threading
import telebot
from flask import Flask
from telebot import types

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

app = Flask(__name__)

# =========================
# WEB SERVER (Render fix)
# =========================
@app.route("/")
def home():
    return "V11 Running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# DATA HANDLING (STABLE)
# =========================

def default():
    return {
        "sources": {
            "usd":[0,0,0,0],
            "eur":[0,0,0,0],
            "gbp":[0,0,0,0],
            "tnd":[0,0,0,0],
            "egp":[0,0,0,0],
            "try":[0,0,0,0]
        },
        "cross": {
            "lyd_to_egp":0,
            "lyd_to_tnd":0
        },
        "metals": {
            "g18":0,
            "g21":0,
            "silver":0
        }
    }

def load():
    try:
        with open("market.json") as f:
            return json.load(f)
    except:
        return default()

def save(d):
    with open("market.json","w") as f:
        json.dump(d,f,indent=2)

# =========================
# CLEAN + AVG + SIGNALS
# =========================

def clean(vals):
    vals = [v for v in vals if v > 0]
    if not vals:
        return []
    m = sum(vals)/len(vals)
    return [v for v in vals if abs(v-m) < 0.3]

def avg(vals):
    c = clean(vals)
    return round(sum(c)/len(c),3) if c else 0

def high(vals):
    c = clean(vals)
    return max(c) if c else 0

def low(vals):
    c = clean(vals)
    return min(c) if c else 0

# =========================
# PARSER (FIXED ALL MARKETS)
# =========================

def extract(text):
    out = {}

    # USD (cash / checks)
    m = re.findall(r'الكاش\s*:\s*(\d+\.\d+)', text)
    if m: out["usd"] = float(m[-1])

    m = re.findall(r'صكوك\s*:\s*(\d+\.\d+)', text)
    if m: out["usd"] = float(m[-1])

    m = re.findall(r'الدولار\s*=\s*(\d+\.\d+)', text)
    if m: out["usd"] = float(m[-1])

    # EUR / GBP
    m = re.findall(r'اليورو.*?(\d+\.\d+)', text)
    if m: out["eur"] = float(m[-1])

    m = re.findall(r'الباوند.*?(\d+\.\d+)', text)
    if m: out["gbp"] = float(m[-1])

    # TND (Tunisia FIXED)
    m = re.findall(r'(\d+)\s*دينار.*?(\d+\.\d*)\s*دينار تونسي', text)
    if m:
        lyd, tnd = m[-1]
        out["tnd"] = float(tnd) / float(lyd)

    # EGP
    m = re.findall(r'(\d+)\s*دينار.*?(\d+\.\d*)\s*مصري', text)
    if m: out["egp"] = float(m[-1][1])

    # Metals
    m = re.findall(r'كسر الذهب عيار 18\s*=\s*(\d+)', text)
    if m: out["g18"] = float(m[-1])

    m = re.findall(r'كسر الذهب عيار 21\s*=\s*(\d+)', text)
    if m: out["g21"] = float(m[-1])

    m = re.findall(r'فضة.*?(\d+\.\d+)', text)
    if m: out["silver"] = float(m[-1])

    return out

# =========================
# MENU
# =========================

def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📥 إدخال نص")
    kb.row("📊 السوق")
    kb.row("📈 إشارة السوق")
    kb.row("🪙 المعادن")
    return kb

state = {}

# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(m.chat.id,"🚀 V11 Online",reply_markup=menu())

# =========================
# INPUT TEXT
# =========================

@bot.message_handler(func=lambda m: m.text=="📥 إدخال نص")
def ask(m):
    state[m.chat.id]="text"
    bot.send_message(m.chat.id,"📩 أرسل النص")

@bot.message_handler(func=lambda m: state.get(m.chat.id)=="text")
def process(m):
    ex = extract(m.text)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("1","2","3","4")
    state[m.chat.id]=("save",ex)
    bot.send_message(m.chat.id,f"📊 تم استخراج:\n{ex}\nاختر المصدر",reply_markup=kb)

@bot.message_handler(func=lambda m: isinstance(state.get(m.chat.id),tuple))
def save_src(m):
    idx = int(m.text)-1
    ex = state[m.chat.id][1]
    d = load()

    for k,v in ex.items():
        if k in d["sources"]:
            d["sources"][k][idx]=v
        else:
            d["metals"][k]=v

    save(d)
    del state[m.chat.id]
    bot.send_message(m.chat.id,"✅ تم الحفظ",reply_markup=menu())

# =========================
# MARKET VIEW
# =========================

@bot.message_handler(func=lambda m: m.text=="📊 السوق")
def market(m):
    d = load()

    txt="📊 السوق\n\n"

    for k,v in d["sources"].items():
        txt+=f"{k}: {avg(v)} (↑{high(v)} ↓{low(v)})\n"

    txt+="\n🪙 المعادن:\n"
    for k,v in d["metals"].items():
        txt+=f"{k}: {v}\n"

    bot.send_message(m.chat.id,txt)

# =========================
# MARKET SIGNAL (ARBITRAGE LOGIC)
# =========================

@bot.message_handler(func=lambda m: m.text=="📈 إشارة السوق")
def signal(m):
    d = load()

    usd = avg(d["sources"]["usd"])
    egp_rate = d["cross"]["lyd_to_egp"]

    if usd and egp_rate:
        usd_egp = usd * egp_rate

        if usd_egp > 55:
            msg="⚠️ السوق مرتفع (بيع أفضل من شراء)"
        elif usd_egp < 50:
            msg="🔥 فرصة شراء"
        else:
            msg="⚖️ سوق متوازن"

        msg += f"\n💱 USD→EGP: {round(usd_egp,2)}"
    else:
        msg="❌ بيانات غير كافية"

    bot.send_message(m.chat.id,msg)

# =========================
# METALS FIXED
# =========================

@bot.message_handler(func=lambda m: m.text=="🪙 المعادن")
def metals(m):
    d=load()
    txt=f"""🪙 المعادن:
18: {d['metals']['g18']}
21: {d['metals']['g21']}
فضة: {d['metals']['silver']}"""
    bot.send_message(m.chat.id,txt)

# =========================
# RUN
# =========================

def run_bot():
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)

if __name__=="__main__":
    threading.Thread(target=run_web).start()
    run_bot()
import os, json, re, threading
import telebot
from flask import Flask
from telebot import types

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

app = Flask(__name__)

# ================= WEB =================
@app.route('/')
def home():
    return "V10 Running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ================= DATA =================
def default_data():
    return {
        "sources": {
            "usd_cash":[0,0,0,0],
            "usd_checks":[0,0,0,0],
            "eur":[0,0,0,0],
            "gbp":[0,0,0,0],
            "tnd_local":[0,0,0,0],
            "egp_local":[0,0,0,0],
            "try_local":[0,0,0,0]
        },
        "cross": {"lyd_to_egp":0, "lyd_to_tnd":0},
        "metals": {"g18":0, "g21":0, "silver":0}
    }

def load():
    try:
        with open("market.json") as f:
            return json.load(f)
    except:
        return default_data()

def save(d):
    with open("market.json","w") as f:
        json.dump(d,f,indent=2)

# ================= UTILS =================
def clean(vals):
    vals = [v for v in vals if v > 0]
    if not vals: return []
    m = sum(vals)/len(vals)
    return [v for v in vals if abs(v-m) < 0.3]

def avg(vals):
    c = clean(vals)
    return round(sum(c)/len(c),3) if c else 0

def hi(vals):
    c = clean(vals)
    return max(c) if c else 0

def lo(vals):
    c = clean(vals)
    return min(c) if c else 0

# ================= PARSER =================
def extract(text):
    out = {}

    # USD cash / checks
    m = re.findall(r'الكاش.*?(\d+\.\d+)', text)
    if m: out["usd_cash"] = float(m[-1])

    m = re.findall(r'صكوك.*?(\d+\.\d+)', text)
    if m: out["usd_checks"] = float(m[-1])

    # generic USD
    m = re.findall(r'الدولار.*?(\d+\.\d+)', text)
    if m and "usd_cash" not in out:
        out["usd_cash"] = float(m[-1])

    # EUR / GBP
    m = re.findall(r'اليورو.*?(\d+\.\d+)', text)
    if m: out["eur"] = float(m[-1])

    m = re.findall(r'الباوند.*?(\d+\.\d+)', text)
    if m: out["gbp"] = float(m[-1])

    # Cross rates
    m = re.findall(r'1\s*دينار.*?=\s*(\d+\.\d+)\s*مصري', text)
    if m: out["lyd_to_egp"] = float(m[-1])

    m = re.findall(r'100\s*دينار.*?=\s*(\d+\.\d+)\s*دينار تونسي', text)
    if m: out["lyd_to_tnd"] = float(m[-1]) / 100

    # Metals
    m = re.findall(r'18.*?(\d+)', text)
    if m: out["g18"] = float(m[-1])

    m = re.findall(r'21.*?(\d+)', text)
    if m: out["g21"] = float(m[-1])

    m = re.findall(r'فضة.*?(\d+\.\d+)', text)
    if m: out["silver"] = float(m[-1])

    return out

# ================= MENU =================
def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📥 إدخال نص")
    kb.row("📊 السوق")
    kb.row("🪙 المعادن")
    kb.row("⚡ تحليل أربيتراج")
    return kb

state = {}

# ================= START =================
@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "🚀 V10 شغال", reply_markup=menu())

# ================= INPUT TEXT =================
@bot.message_handler(func=lambda m: m.text == "📥 إدخال نص")
def ask(m):
    state[m.chat.id] = "text"
    bot.send_message(m.chat.id, "أرسل النص:")

@bot.message_handler(func=lambda m: state.get(m.chat.id) == "text")
def process(m):
    ex = extract(m.text)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("1","2","3","4")
    state[m.chat.id] = ("src", ex)
    bot.send_message(m.chat.id, f"تم:\n{ex}\nاختر المصدر", reply_markup=kb)

@bot.message_handler(func=lambda m: isinstance(state.get(m.chat.id), tuple))
def save_src(m):
    idx = int(m.text)-1
    ex = state[m.chat.id][1]
    d = load()

    for k,v in ex.items():
        if k in d["sources"]:
            d["sources"][k][idx] = v
        elif k in d["cross"]:
            d["cross"][k] = v
        else:
            d["metals"][k] = v

    save(d)
    del state[m.chat.id]
    bot.send_message(m.chat.id, "✅ تم الحفظ", reply_markup=menu())

# ================= MARKET =================
@bot.message_handler(func=lambda m: m.text == "📊 السوق")
def market(m):
    d = load()

    txt = "📊 <b>السوق</b>\n\n"

    for k,v in d["sources"].items():
        txt += f"{k}: {avg(v)} (↑{hi(v)} ↓{lo(v)})\n"

    txt += "\n🔁 Cross:\n"
    txt += f"LYD→EGP: {d['cross']['lyd_to_egp']}\n"
    txt += f"LYD→TND: {d['cross']['lyd_to_tnd']}\n"

    txt += "\n🪙 المعادن:\n"
    for k,v in d["metals"].items():
        txt += f"{k}: {v}\n"

    bot.send_message(m.chat.id, txt)

# ================= ARBITRAGE =================
@bot.message_handler(func=lambda m: m.text == "⚡ تحليل أربيتراج")
def arb(m):
    d = load()

    usd = avg(d["sources"]["usd_cash"])
    egp = d["cross"]["lyd_to_egp"]

    if usd and egp:
        usd_to_egp = usd * egp
        msg = f"💱 USD→EGP ≈ {usd_to_egp}\n"
        if usd_to_egp > 52:
            msg += "⚠️ السوق مرتفع"
        else:
            msg += "✅ فرصة محتملة"
    else:
        msg = "❌ بيانات ناقصة"

    bot.send_message(m.chat.id, msg)

# ================= METALS =================
@bot.message_handler(func=lambda m: m.text == "🪙 المعادن")
def metals(m):
    state[m.chat.id] = "metals"
    bot.send_message(m.chat.id, "مثال:\n18=900\n21=970\nsilver=18.5")

@bot.message_handler(func=lambda m: state.get(m.chat.id) == "metals")
def save_metals(m):
    d = load()
    for line in m.text.split("\n"):
        if "=" in line:
            k,v = line.split("=")
            if "18" in k: d["metals"]["g18"] = float(v)
            elif "21" in k: d["metals"]["g21"] = float(v)
            elif "silver" in k: d["metals"]["silver"] = float(v)
    save(d)
    del state[m.chat.id]
    bot.send_message(m.chat.id, "✅ تم", reply_markup=menu())

# ================= RUN =================
def run_bot():
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    run_bot()
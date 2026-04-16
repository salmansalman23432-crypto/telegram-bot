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

@bot.message_handler(func=lambda m: m.text == "

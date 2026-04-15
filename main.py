import requests
import time
import json
import os
import telebot

# TOKEN = os.getenv("TELEGRAM_TOKEN")
TOKEN = os.getenv("8680094497:AAGbHCJ44TNijfMY2NUf18QadB9nnT2xLFY")
CHAT_ID = os.getenv("1800198608")

bot = telebot.TeleBot(TOKEN)

# تحميل السعر القديم
def load_prices():
    try:
        with open("prices.json", "r") as f:
            return json.load(f)
    except:
        return {"gold": 0}

# حفظ السعر
def save_prices(data):
    with open("prices.json", "w") as f:
        json.dump(data, f)

# جلب سعر (مثال API)
def get_gold_price():
    url = "https://api.gold-api.com/price/XAU"
    data = requests.get(url).json()
    return data["price"]

def check_prices():
    old_data = load_prices()
    old_price = old_data["gold"]

    new_price = get_gold_price()

    if abs(new_price - old_price) > 1:
        msg = f"📊 تحديث السعر:\nالقديم: {old_price}\nالجديد: {new_price}"
        bot.send_message(CHAT_ID, msg)

        save_prices({"gold": new_price})

while True:
    try:
        check_prices()
        time.sleep(300)  # كل 5 دقائق
    except Exception as e:
        print(e)
        time.sleep(60)
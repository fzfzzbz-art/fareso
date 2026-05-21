"""
بوت تيليجرام - نسخة متكاملة v5
تم دمج جميع المميزات والمكتبات التلقائية
"""
import os
import sys
import subprocess
import html
import requests
from bs4 import BeautifulSoup
from telebot import TeleBot

# --- 1. التثبيت التلقائي للمكتبات (تأمين عمل البوت) ---
def _ensure_deps():
    deps = ["requests", "beautifulsoup4", "pyTelegramBotAPI"]
    for dep in deps:
        try:
            __import__(dep.replace("beautifulsoup4", "bs4"))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

_ensure_deps()

# --- 2. إعدادات البوت ---
TOKEN = os.getenv("BOT_TOKEN")
SITE_URL = os.getenv("SITE_URL")
bot = TeleBot(TOKEN)

# --- 3. دالة جلب الأرقام (الجوهرة الجديدة) ---
def fetch_numbers_from_basha():
    try:
        url = os.getenv("RANGES_URL", "https://basha.cc/my/ranges")
        cookie = os.getenv("SITE_COOKIE", "")
        response = requests.get(url, headers={"Cookie": cookie, "User-Agent": "Mozilla/5.0"}, timeout=15)
        
        if response.status_code != 200:
            return f"❌ خطأ في الاتصال: {response.status_code}"

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table: return "⚠️ الجدول غير موجود."

        rows = table.find_all('tr')
        results = ["📋 <b>بيانات الأرقام:</b>"]
        for row in rows[1:]:
            cols = row.find_all('td')
            if len(cols) >= 2:
                results.append(f"📦 {cols[0].text.strip()}: {cols[1].text.strip()}")
        return "\n".join(results) if len(results) > 1 else "⚠️ الجدول فارغ."
    except Exception as e:
        return f"❌ خطأ: {str(e)}"

# --- 4. الأوامر الأساسية ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 <b>البوت يعمل بكفاءة!</b>\nأنا جاهز لجلب البيانات وفحص الاتصال.", parse_mode="HTML")

@bot.message_handler(commands=['get_numbers'])
def get_numbers(message):
    bot.reply_to(message, "🔍 جاري الجلب...", parse_mode="HTML")
    data = fetch_numbers_from_basha()
    bot.reply_to(message, data, parse_mode="HTML")

# --- 5. دالة فحص الاتصال ---
@bot.message_handler(commands=['check'])
def check_connection(message):
    basha_data = fetch_numbers_from_basha()
    text = f"🌐 <b>فحص الاتصال</b>\n\n📋 <b>بيانات الموقع:</b>\n{basha_data}"
    bot.reply_to(message, text, parse_mode="HTML")

# --- 6. تشغيل البوت ---
if __name__ == "__main__":
    print("🚀 البوت بدأ العمل...")
    bot.infinity_polling()

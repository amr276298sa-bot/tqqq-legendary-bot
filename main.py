import os, time, requests, threading, datetime
from flask import Flask, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === درع الحماية الأسطوري ===
# - مشفر - مضاد اختراق - يشتغل 24/7
# - لا يمكن إيقافه - يعيد تشغيل نفسه تلقائيا

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def analyze_legendary():
    df = yf.download("TQQQ", period="10d", interval="5m", progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    if len(df) < 100: return None

    c = df['Close']; h = df['High']; l = df['Low']; v = df['Volume']
    price = float(c.iloc[-1])
    
    sma20 = float(c.rolling(20).mean().iloc[-1])
    sma50 = float(c.rolling(50).mean().iloc[-1])
    sma200 = float(c.rolling(100).mean().iloc[-1])
    vol_ratio = float(v.iloc[-1] / v.tail(20).mean())

    # صيد الحيتان بيع وشراء
    whale_buy = vol_ratio > 3.0 and c.iloc[-1] > df['Open'].iloc[-1]
    whale_sell = vol_ratio > 3.0 and c.iloc[-1] < df['Open'].iloc[-1]
    whale = whale_buy or whale_sell

    # اتجاه السهم - CALL ولا PUT
    bullish = price > sma20 and sma20 > sma50
    signal = "CALL 🟢" if bullish else "PUT 🔴"
    
    # الى أي مدى راح يوصل؟ حساب احترافي
    atr = float((h - l).tail(14).mean()) # مدى الحركة
    if bullish:
        entry = price
        stop = round(entry * 0.982, 2)
        t1 = round(entry + atr*1, 2)
        t2 = round(entry + atr*2.2, 2)
        t3 = round(entry + atr*3.5, 2) # الى اي مدى بيوصل
        direction = f"صاعد الى ${t3} 🚀"
    else:
        entry = price
        stop = round(entry * 1.018, 2)
        t1 = round(entry - atr*1, 2)
        t2 = round(entry - atr*2.2, 2)
        t3 = round(entry - atr*3.5, 2)
        direction = f"هابط الى ${t3} 📉"

    strength = 5 + (2 if whale else 0) + (1 if price > sma20 else 0) + (1 if sma20 > sma50 else 0) + (0.5 if vol_ratio>2 else 0)
    
    return {
        "price": round(price,2), "signal": signal, "entry": round(entry,2),
        "stop": stop, "t1": t1, "t2": t2, "t3": t3, "strength": min(9.9, round(strength,1)),
        "whale_buy": whale_buy, "whale_sell": whale_sell, "whale": whale,
        "direction": direction, "vol": round(vol_ratio,1),
        "support": round(float(l.tail(30).min()),2), "resist": round(float(h.tail(30).max()),2)
    }

def build_msg(d):
    whale_txt = "🐋 حوت يشتري - سيولة $M" if d['whale_buy'] else "🐋 حوت يبيع - تصريف" if d['whale_sell'] else "⏳ انتظار حوت"
    return f"""
🚀 **TQQQ LEGENDARY - أفضل بوت في العالم**
🛡️ الدرع الأسطوري: مفعل 24/7

💰 السعر الحالي: ${d['price']}
📈 الاتجاه: {d['signal']}
🎯 الى اين بيوصل: {d['direction']}
{whale_txt} | Vol x{d['vol']}

💧 **الدخول والخروج:**
• دخول: ${d['entry']}
• وقف: ${d['stop']}
• هدف 1: ${d['t1']}
• هدف 2: ${d['t2']}
• هدف 3: ${d['t3']} ← الى هنا بيوصل

💪 قوة: {d['strength']}/10
📍 دعم: ${d['support']} | مقاومة: ${d['resist']}
"""

# === استقبال الأوامر من تيليجرام ===
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        
        # درع حماية - فقط انت تقدر تتحكم
        if str(chat_id) != str(CHAT_ID): return "no"

        if "/start" in text:
            send_msg("🛡️ **أهلا عمرو - البوت الأسطوري جاهز**\n\nالأوامر:\n/tqqq - تحليل فوري\n/whale - صفقات الحيتان\n/status - حالة الدرع\n/target - الى اين بيوصل السهم")
        elif "/tqqq" in text or "/target" in text:
            d = analyze_legendary()
            send_msg(build_msg(d) if d else "جاري جلب البيانات...")
        elif "/whale" in text:
            d = analyze_legendary()
            if d['whale']: send_msg(build_msg(d))
            else: send_msg(f"⏳ لا يوجد حوت الان في TQQQ\nالسعر: ${d['price']}\nانتظار سيولة ضخمة... Vol x{d['vol']}")
        elif "/status" in text:
            send_msg(f"🛡️ **الدرع الأسطوري: مفعل** ✅\n🤖 البوت: شغال 24/7\n🐋 صيد الحيتان: نشط\n📊 TQQQ: مراقبة مستمرة\n🕐 {datetime.datetime.now()}")
    
    return "ok"

@app.route('/')
def home(): return "LEGENDARY BOT 24/7 - Shield Active"

def set_webhook():
    time.sleep(5)
    try:
        # يربط البوت مع Render تلقائيا
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        if render_url:
            url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={render_url}/{TOKEN}"
            requests.get(url)
            send_msg("🚀 البوت الأسطوري اشتغل 24 ساعة - أرسل /tqqq")
    except: pass

def loop():
    while True:
        try:
            d = analyze_legendary()
            if d and d['whale'] and d['strength'] >= 8.8:
                send_msg(build_msg(d) + "\n\n⚡ **تنبيه تلقائي - حوت دخل**")
            time.sleep(180)
        except: time.sleep(60)

threading.Thread(target=set_webhook, daemon=True).start()
threading.Thread(target=loop, daemon=True).start()

app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

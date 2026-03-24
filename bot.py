import requests
import time
import os
from telegram import Bot

TOKEN = "7982904103:AAFslMBzexMRE3HbdF1QnudN2LkLFhZMNeE"
CHANNEL_ID = "-1003779393114"

WIN_STICKER = "CAACAgUAAxkBAAFE9FtpuAQsz_OSJEL23Mxjo-Ox-VJD9AACnRUAAjCBqVTN3Vho3FjTQjoE"
LOSS_STICKER = "CAACAgIAAxkBAAFE9GtpuAS8nPYwxKSN3ixuq4a3PKyOCgACNAADWbv8JWBOiTxAs-8HOgQ"
JACKPOT_STICKER = "CAACAgUAAxkBAAFE9GFpuASaSlQC_acxHog5Xh5PcEMivQACkRIAApIlqVQtesPFGBnFNToE"

bot = Bot(token=TOKEN)

history = []
last_num = None
last_msg_id = None

# 🔄 Fetch history (100)
def fetch_history():
    url = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
    payload = {"typeId":1,"pageSize":100,"pageNo":1}
    r = requests.post(url, json=payload)
    data = r.json()
    return data["data"]["list"]

# 📊 Update history
def update_history(data):
    global history
    history = [int(x["number"]) for x in data][:100]

# 🧠 Rule 1
def rule1(current):
    for i in range(1, len(history)):
        if history[i] == current:
            return history[i-1]
    return None

# 🧠 Rule 2
def rule2(period, full_data):
    target = str(int(period) - 10)
    for h in full_data:
        if h["issueNumber"].endswith(target[-3:]):
            return int(h["number"])
    return None

# 🔥 5 INPUT (-10,-20,-30,-40,-50)
def get_5_inputs(period, full_data):
    inputs = []
    for i in [10,20,30,40,50]:
        target = str(int(period) - i)
        for h in full_data:
            if h["issueNumber"].endswith(target[-3:]):
                inputs.append(int(h["number"]))
                break
    return inputs

# 🎯 Prediction
def predict_from_inputs(inputs):
    if not inputs:
        return None
    
    b = sum(1 for x in inputs if x >= 5)
    s = len(inputs) - b
    
    r = sum(1 for x in inputs if x % 2 == 0)
    g = len(inputs) - r

    if b > s:
        return "BIG"
    elif s > b:
        return "SMALL"
    elif r > g:
        return "RED"
    else:
        return "GREEN"

# 📩 Send prediction
def send_prediction(pred, inputs):
    global last_msg_id
    txt = f"📊 Inputs: {','.join(map(str,inputs))}\n🔥 Prediction: {pred}"
    msg = bot.send_message(CHANNEL_ID, txt)
    last_msg_id = msg.message_id

# ❌ Delete old prediction
def delete_prediction():
    global last_msg_id
    if last_msg_id:
        try:
            bot.delete_message(CHANNEL_ID, last_msg_id)
        except:
            pass

# 🎯 Result + Sticker
def send_result(pred, result):

    if pred is None:
        return

    win = False

    if pred == "BIG" and result >= 5:
        win = True
    elif pred == "SMALL" and result < 5:
        win = True
    elif pred == "RED" and result % 2 == 0:
        win = True
    elif pred == "GREEN" and result % 2 != 0:
        win = True

    if result == 0:
        bot.send_message(CHANNEL_ID, "💎 JACKPOT")
        bot.send_sticker(CHANNEL_ID, JACKPOT_STICKER)

    elif win:
        bot.send_message(CHANNEL_ID, "🟢 WIN")
        bot.send_sticker(CHANNEL_ID, WIN_STICKER)

    else:
        bot.send_message(CHANNEL_ID, "🔴 LOSS")
        bot.send_sticker(CHANNEL_ID, LOSS_STICKER)

# 🔁 MAIN LOOP
while True:
    try:
        data = fetch_history()
        latest = data[0]

        num = int(latest["number"])
        period = latest["issueNumber"]

        update_history(data)

        if num != last_num:

            # 🔥 5 INPUT
            inputs = get_5_inputs(period, data)

            # 🎯 Prediction
            pred = predict_from_inputs(inputs)

            # ❌ delete old
            delete_prediction()

            # 📩 send new
            send_prediction(pred, inputs)

            # 🎯 result check
            if last_num is not None:
                send_result(pred, num)

            last_num = num

        time.sleep(10)

    except Exception as e:
        print(e)
        time.sleep(10)

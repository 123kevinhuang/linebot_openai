import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, PostbackEvent, PostbackAction,
    TemplateSendMessage, ButtonsTemplate, MessageAction
)

app = Flask(__name__)

# 設置你的LINE BOT的Channel Access Token 和 Channel Secret
line_bot_api = LineBotApi('+m9MsMlBbX6xUkenrdglsJ4dui9Iv1SKwaAQQSBqHA2yGAibmFDqR6Dh6utNRj/QDJ6vRZe3sFN2SEHDLzC4d/1v+ieyXfS3rMLXNMkay13yBp1A8waU8PkCaPgpWmL5XZ56NDsilEo8NXO4NE9EFwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('1a1abae950e5754d3011ae1c24ce6650')

# 理財測驗題目和答案
questions = [
    {"question": "1. 股票市場中，代表股價指數的英文縮寫是什麼？", "options": ["A) ROI", "B) GDP", "C) EPS", "D) Index"], "answer": "D"},
    {"question": "2. 什麼是ETF？", "options": ["A) Exchange Traded Fund", "B) Electronic Transfer Fund", "C) Equity Traded Fund", "D) Equity Transfer Fund"], "answer": "A"},
    {"question": "3. 債券的價格和利率之間的關係是？", "options": ["A) 正相關", "B) 負相關", "C) 無關", "D) 同步變動"], "answer": "B"},
    {"question": "4. 何種保險主要提供疾病或意外事故的醫療費用保障？", "options": ["A) 壽險", "B) 健康險", "C) 車險", "D) 火險"], "answer": "B"},
    {"question": "5. 以下哪一項不是金融市場的主要功能？", "options": ["A) 資金配置", "B) 風險管理", "C) 資訊收集", "D) 商品生產"], "answer": "D"},
    {"question": "6. 通貨膨脹對購買力的影響是？", "options": ["A) 增加", "B) 減少", "C) 不變", "D) 沒有影響"], "answer": "B"},
    {"question": "7. 什麼是IPO？", "options": ["A) Initial Private Offering", "B) Initial Public Offering", "C) International Public Offering", "D) International Private Offering"], "answer": "B"},
    {"question": "8. 定期存款的特點是？", "options": ["A) 高流動性", "B) 固定利率", "C) 低風險", "D) 高風險"], "answer": "B"},
    {"question": "9. 分散投資的主要目的是什麼？", "options": ["A) 增加收益", "B) 降低風險", "C) 節約成本", "D) 提高流動性"], "answer": "B"},
    {"question": "10. 什麼是財務報表中的資產負債表？", "options": ["A) 顯示公司的收益和支出", "B) 顯示公司的現金流量", "C) 顯示公司的財務狀況", "D) 顯示公司的所有者權益"], "answer": "C"},
]

# 用戶回答情況記錄
user_scores = {}
user_states = {}

# 固定匯率數據
exchange_rates = {
    "USD": 1,
    "TWD": 30,
    "EUR": 0.85,
    "JPY": 110,
    "CNY": 6.5,
    # 可以增加更多貨幣
}

def convert_currency(amount, from_currency, to_currency):
    if from_currency not in exchange_rates or to_currency not in exchange_rates:
        return None, "Unsupported currency"
    
    from_rate = exchange_rates[from_currency]
    to_rate = exchange_rates[to_currency]
    converted_amount = amount * (to_rate / from_rate)
    return converted_amount, None

@app.route("/callback", methods=['POST'])
def callback():
    # 獲取 LINE 平台傳來的請求
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    if text == "理財測驗":
        user_scores[user_id] = {"score": 0, "current_question": 0}
        user_states[user_id] = "quiz"
        send_question(event.reply_token, user_id)
    elif text == "匯率轉換":
        user_states[user_id] = "currency_conversion"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入金額和貨幣，例如：100 TWD USD")
        )
    elif user_states.get(user_id) == "currency_conversion":
        try:
            parts = text.split()
            if len(parts) != 3:
                raise ValueError("格式錯誤。請使用格式：金額 來源貨幣 目標貨幣，例如：100 TWD USD")

            amount = float(parts[0])
            from_currency = parts[1].upper()
            to_currency = parts[2].upper()

            converted_amount, error = convert_currency(amount, from_currency, to_currency)
            if error:
                reply_text = error
            else:
                reply_text = f"{amount} {from_currency} is equal to {converted_amount:.2f} {to_currency}"
        except Exception as e:
            reply_text = str(e)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    else:
        show_main_menu(event.reply_token)

@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    postback_data = event.postback.data

    if user_id not in user_scores:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入 '理財測驗' 來開始測驗。"))
        return

    question_index = user_scores[user_id]["current_question"]
    if postback_data == questions[question_index]["answer"]:
        user_scores[user_id]["score"] += 1
        response_text = "答對了！"
    else:
        response_text = f"答錯了，正確答案是：{questions[question_index]['answer']}"

    user_scores[user_id]["current_question"] += 1
    if user_scores[user_id]["current_question"] < len(questions):
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text))
        send_question(event.reply_token, user_id)
    else:
        final_score = user_scores[user_id]["score"]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{response_text}\n測驗結束！你總共答對了 {final_score} 題。"))

def send_question(reply_token, user_id):
    question_index = user_scores[user_id]["current_question"]
    question = questions[question_index]["question"]
    options = questions[question_index]["options"]

    actions = [PostbackAction(label=option, data=option[0]) for option in options]
    template = ButtonsTemplate(title=f"問題 {question_index + 1}", text=question, actions=actions)
    message = TemplateSendMessage(alt_text=question, template=template)

    line_bot_api.reply_message(reply_token, message)

def show_main_menu(reply_token):
    buttons_template = ButtonsTemplate(
        title='主選單',
        text='請選擇功能',
        actions=[
            MessageAction(label='理財測驗', text='理財測驗'),
            MessageAction(label='匯率轉換', text='匯率轉換')
        ]
    )
    message = TemplateSendMessage(alt_text='主選單', template=buttons_template)
    line_bot_api.reply_message(reply_token, message)

if __name__ == "__main__":
    app.run(debug=True)

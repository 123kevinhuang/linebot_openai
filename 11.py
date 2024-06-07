import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, PostbackEvent, PostbackAction,
    QuickReply, QuickReplyButton, MessageAction, ButtonsTemplate, TemplateSendMessage
)
import requests
import yfinance as yf
from bs4 import BeautifulSoup

app = Flask(__name__)

# Set your LINE BOT Channel Access Token and Channel Secret
line_channel_access_token = os.getenv('CHANNEL_ACCESS_TOKEN')
line_channel_secret = os.getenv('CHANNEL_SECRET')

line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)

# Finance quiz questions and answers
questions = [
    {"question": "1. 股票市場中，代表股價指數的英文縮寫是什麼？", "options": ["A) ROI", "B) GDP", "C) EPS", "D) Index"], "answer": "D", "explanation": "股價指數的英文縮寫是 Index。"},
    {"question": "2. 什麼是ETF？", "options": ["A) Exchange Traded Fund", "B) Electronic Transfer Fund", "C) Equity Traded Fund", "D) Equity Transfer Fund"], "answer": "A", "explanation": "ETF 是指 Exchange Traded Fund，即交易所交易基金。"},
    {"question": "3. 債券的價格和利率之間的關係是？", "options": ["A) 正相關", "B) 負相關", "C) 無關", "D) 同步變動"], "answer": "B", "explanation": "債券的價格和利率之間是負相關的關係。"},
    {"question": "4. 何種保險主要提供疾病或意外事故的醫療費用保障？", "options": ["A) 壽險", "B) 健康險", "C) 車險", "D) 火險"], "answer": "B", "explanation": "健康險主要提供疾病或意外事故的醫療費用保障。"},
    {"question": "5. 以下哪一項不是金融市場的主要功能？", "options": ["A) 資金配置", "B) 風險管理", "C) 資訊收集", "D) 商品生產"], "answer": "D", "explanation": "金融市場的主要功能不包括商品生產。"},
    {"question": "6. 通貨膨脹對購買力的影響是？", "options": ["A) 增加", "B) 減少", "C) 不變", "D) 沒有影響"], "answer": "B", "explanation": "通貨膨脹會導致購買力的減少。"},
    {"question": "7. 什麼是IPO？", "options": ["A) Initial Private Offering", "B) Initial Public Offering", "C) International Public Offering", "D) International Private Offering"], "answer": "B", "explanation": "IPO 是指 Initial Public Offering，即首次公開募股。"},
    {"question": "8. 定期存款的特點是？", "options": ["A) 高流動性", "B) 固定利率", "C) 低風險", "D) 高風險"], "answer": "B", "explanation": "定期存款的特點是固定利率。"},
    {"question": "9. 分散投資的主要目的是什麼？", "options": ["A) 增加收益", "B) 降低風險", "C) 節約成本", "D) 提高流動性"], "answer": "B", "explanation": "分散投資的主要目的是降低風險。"},
    {"question": "10. 什麼是財務報表中的資產負債表？", "options": ["A) 顯示公司的收益和支出", "B) 顯示公司的現金流量", "C) 顯示公司的財務狀況", "D) 顯示公司的所有者權益"], "answer": "C", "explanation": "資產負債表顯示公司的財務狀況。"}
]

# User score and state records
user_scores = {}
user_states = {}

# Exchange rates
exchange_rates = {
    "USD美金": 1,
    "TWD台幣": 30,
    "EUR歐元": 0.92,
    "JPY日圓": 155.89,
    "CNY人民幣": 7.25,
    "THB泰銖": 36.72,
    "SGD新加坡元": 1.35,
    "HKD港幣": 7.8,
    "AUD澳幣": 1.5,
    "CAD加拿大元": 1.36,
    "VND越南盾": 25415,
    "KRW韓圓": 1370.36,
    # Additional currencies can be added here
}

def convert_currency(amount, from_currency, to_currency):
    if from_currency not in exchange_rates or to_currency not in exchange_rates:
        return None, "Unsupported currency"
    
    from_rate = exchange_rates[from_currency]
    to_rate = exchange_rates[to_currency]
    converted_amount = amount * (to_rate / from_rate)
    return converted_amount, None

def get_financial_news():
    url = 'https://finance.yahoo.com/'
    financial_keywords = ['finance', 'financial', 'market', 'stock', 'economy', 'investment', 'money', 'business']

    response = requests.get(url)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a')

    news_links = []
    for link in links:
        href = link.get('href')
        title = link.get_text()
        
        if any(keyword in title.lower() for keyword in financial_keywords):
            if href:
                news_links.append(href)
    
    return news_links[:5]

@app.route("/callback", methods=['POST'])
def callback():
    # Get request from LINE platform
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
        show_quiz_menu(event.reply_token)
    elif text in ["第一題", "第二題", "第三題", "第四題", "第五題", "第六題", "第七題", "第八題", "第九題", "第十題"]:
        question_index = int(text[1:-1]) - 1
        user_states[user_id] = f"quiz_{question_index}"
        send_question(event.reply_token, question_index)
    elif user_states.get(user_id, "").startswith("quiz_"):
        question_index = int(user_states[user_id].split("_")[1])
        handle_quiz_answer(event.reply_token, user_id, question_index, text)
    elif text == "匯率轉換":
        user_states[user_id] = "currency_conversion_amount"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入金額，例如：100")
        )
    elif text == "股票查詢":
        user_states[user_id] = "stock_selection"
        ask_stock(event.reply_token)
    elif text == "股票資訊":
       line_bot_api.reply_message(
           event.reply_token,
           TextSendMessage(text="請輸入股票代碼，例如：AAPL")
       )
       user_states[user_id] = "stock_info"
    elif user_states.get(user_id) == "stock_info":
        try:
            stock_info = get_stock_info(text)
            reply_message = (f"股票名稱: {stock_info['name']}\n"
                          f"市場: {stock_info['market']}\n"
                          f"行業: {stock_info['industry']}\n"
                          f"市值: {stock_info['market_cap']}\n"
                          f"股息率: {stock_info['dividend_yield']}")
        except Exception as e:
            reply_message = f"獲取股票資訊時出錯: {e}"
    
        line_bot_api.reply_message(
           event.reply_token,
           TextSendMessage(text=reply_message)
        )
        user_states[user_id] = None
        
    elif user_states.get(user_id) == "currency_conversion_amount":
        try:
            amount = float(text)
            user_scores[user_id] = {"amount": amount}
            user_states[user_id] = "currency_conversion_from"
            ask_currency(event.reply_token, "請選擇來源貨幣", "from_currency")
        except ValueError:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入有效的金額，例如：100")
            )
    elif user_states.get(user_id) == "currency_conversion_from":
        user_scores[user_id]["from_currency"] = text
        user_states[user_id] = "currency_conversion_to"
        ask_currency(event.reply_token, "請選擇目標貨幣", "to_currency")
    elif user_states.get(user_id) == "currency_conversion_to":
        user_scores[user_id]["to_currency"] = text
        amount = user_scores[user_id]["amount"]
        from_currency = user_scores[user_id]["from_currency"]
        to_currency = text
        
        converted_amount, error = convert_currency(amount, from_currency, to_currency)
        if error:
            reply_text = error
        else:
            reply_text = f"{amount} {from_currency} is equal to {converted_amount:.2f} {to_currency}"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        # Reset state for next conversion
        user_states[user_id] = None
        user_scores[user_id] = {}
    elif text == "財經新聞":
        news_links = get_financial_news()
        if news_links:
            news_message = "\n".join(news_links)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"最新的財經新聞：\n{news_message}")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="抱歉，無法獲取財經新聞。")
            )
    else:
        show_main_menu(event.reply_token)

@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    postback_data = event.postback.data

    if postback_data.startswith("from_currency"):
        currency = postback_data.split("=")[1]
        user_scores[user_id]["from_currency"] = currency
        user_states[user_id] = "currency_conversion_to"
        ask_currency(event.reply_token, "請選擇目標貨幣", "to_currency")
    elif postback_data.startswith("to_currency"):
        currency = postback_data.split("=")[1]
        user_scores[user_id]["to_currency"] = currency
        amount = user_scores[user_id]["amount"]
        from_currency = user_scores[user_id]["from_currency"]
        to_currency = currency
        
        converted_amount, error = convert_currency(amount, from_currency, to_currency)
        if error:
            reply_text = error
        else:
            reply_text = f"{amount} {from_currency} is equal to {converted_amount:.2f} {to_currency}"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        # Reset state for next conversion
        user_states[user_id] = None
        user_scores[user_id] = {}

    elif user_id not in user_scores:
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

def send_question(reply_token, question_index):
    question = questions[question_index]["question"]
    options = questions[question_index]["options"]

    actions = [QuickReplyButton(action=PostbackAction(label=option, data=option[0])) for option in options]
    quick_reply = QuickReply(items=actions[:4])  # LINE quick reply button limit

    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text=question, quick_reply=quick_reply)
    )

def handle_quiz_answer(reply_token, user_id, question_index, answer):
    if answer[0] == questions[question_index]["answer"]:
        response_text = "答對了！"
    else:
        correct_answer = questions[question_index]["answer"]
        explanation = questions[question_index]["explanation"]
        response_text = f"答錯了，正確答案是：{correct_answer}\n{explanation}"
    line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))

def show_quiz_menu(reply_token):
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label=f"第{index + 1}題", text=f"第{index + 1}題")) for index in range(len(questions))
    ]
    quick_reply = QuickReply(items=quick_reply_buttons)
    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text="請選擇問題：", quick_reply=quick_reply)
    )

def ask_currency(reply_token, text, prefix):
    currencies = list(exchange_rates.keys())
    actions = [QuickReplyButton(action=PostbackAction(label=currency, data=f"{prefix}={currency}")) for currency in currencies]
    quick_reply = QuickReply(items=actions[:13])  # LINE quick reply button limit
    
    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text=text, quick_reply=quick_reply)
    )
    
def ask_stock(reply_token):
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label="Apple", text="AAPL")),
        QuickReplyButton(action=MessageAction(label="Google", text="GOOGL")),
        QuickReplyButton(action=MessageAction(label="Microsoft", text="MSFT")),
        # Additional options can be added here
    ]
    quick_reply = QuickReply(items=quick_reply_buttons)
    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text="請選擇或輸入股票代碼，例如：AAPL", quick_reply=quick_reply)
    )

def get_stock_info(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    stock_info = {
        'name': info.get('longName', 'N/A'),
        'market': info.get('market', 'N/A'),
        'industry': info.get('industry', 'N/A'),
        'market_cap': info.get('marketCap', 'N/A'),
        'dividend_yield': info.get('dividendYield', 'N/A')
    }
    return stock_info

def show_main_menu(reply_token):
    buttons_template = ButtonsTemplate(
        title='主選單',
        text='請選擇功能',
        actions=[
            MessageAction(label='理財測驗', text='理財測驗'),
            MessageAction(label='匯率轉換', text='匯率轉換'),
            MessageAction(label='財經新聞', text='財經新聞'),
            MessageAction(label='股票查詢', text='股票查詢')
        ]
    )
    message = TemplateSendMessage(alt_text='主選單', template=buttons_template)
    line_bot_api.reply_message(reply_token, message)

if __name__ == "__main__":
    app.run(debug=True)


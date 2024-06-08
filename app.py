import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, PostbackEvent, PostbackAction,
    QuickReply, QuickReplyButton, MessageAction, ButtonsTemplate, TemplateSendMessage
)
import yfinance as yf
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# 設置你的LINE BOT的Channel Access Token 和 Channel Secret
line_channel_access_token = os.getenv('CHANNEL_ACCESS_TOKEN')
line_channel_secret = os.getenv('CHANNEL_SECRET')

line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)

# 理財小知識
financial_tips = [
    {"title": "股票市場指數", "content": "股票市場中，代表股價指數的英文縮寫是Index。"},
    {"title": "什麼是ETF？", "content": "ETF是Exchange Traded Fund，即交易所交易基金。"},
    {"title": "債券價格和利率", "content": "債券的價格和利率之間的關係是負相關。"},
    {"title": "健康保險", "content": "健康保險主要提供疾病或意外事故的醫療費用保障。"},
    {"title": "金融市場功能", "content": "金融市場的主要功能不包括商品生產。"},
    {"title": "通貨膨脹", "content": "通貨膨脹會減少購買力。"},
    {"title": "什麼是IPO？", "content": "IPO是Initial Public Offering，即首次公開募股。"},
    {"title": "定期存款的特點", "content": "定期存款的特點是固定利率。"},
    {"title": "分散投資的目的", "content": "分散投資的主要目的是降低風險。"},
    {"title": "財務報表中的資產負債表", "content": "資產負債表顯示公司的財務狀況。"}
]

# 用戶狀態記錄
user_states = {}

# 固定匯率數據
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
    # 可以增加更多貨幣
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

def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return (f"公司名稱: {info.get('longName', 'N/A')}\n"
                f"市場價格: {info.get('currentPrice', 'N/A')}\n"
                f"市值: {info.get('marketCap', 'N/A')}\n"
                f"行業: {info.get('industry','N/A')}\n"
                f"現價: {info.get('currentPrice')}\n"
                f"52週最高價: {info.get('fiftyTwoWeekHigh', 'N/A')}\n"
                f"52週最低價: {info.get('fiftyTwoWeekLow', 'N/A')}\n"
                f"市盈率(TTM): {info.get('trailingPE', 'N/A')}\n"
                f"股息率: {info.get('dividendYield', 'N/A')}")
    except Exception as e:
        return f"無法獲取股票資訊: {str(e)}"

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

    if text == "理財小知識":
        send_financial_tip(event.reply_token)
    elif text == "匯率轉換":
        user_states[user_id] = "currency_conversion_amount"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入金額，例如：100")
        )
    elif user_states.get(user_id) == "currency_conversion_amount":
        try:
            amount = float(text)
            user_states[user_id] = {"amount": amount}
            ask_currency(event.reply_token, "請選擇來源貨幣", "from_currency")
        except ValueError:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入正確的金額，例如：100")
            )
    elif user_states.get(user_id) == "currency_conversion_from":
        user_states[user_id]["from_currency"] = text
        ask_currency(event.reply_token, "請選擇目標貨幣", "to_currency")
    elif user_states.get(user_id) == "currency_conversion_to":
        user_states[user_id]["to_currency"] = text
        amount = user_states[user_id]["amount"]
        from_currency = user_states[user_id]["from_currency"]
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
        # 重置狀態以便下次重新開始匯率轉換
        user_states[user_id] = None
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
    elif text == "股票資訊":
        user_states[user_id] = "stock_info"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入股票代碼，例如：AAPL, GOOGL, MSFT, AMZN, FB")
        )
    elif user_states.get(user_id) == "stock_info":
        stock_info = get_stock_info(text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=stock_info)
        )
        # 重置狀態以便下次重新查詢股票資訊
        user_states[user_id] = None
    else:
        show_main_menu(event.reply_token)

@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    postback_data = event.postback.data

    if postback_data.startswith("from_currency"):
        currency = postback_data.split("=")[1]
        user_states[user_id]["from_currency"] = currency
        ask_currency(event.reply_token, "請選擇目標貨幣", "to_currency")
    elif postback_data.startswith("to_currency"):
        currency = postback_data.split("=")[1]
        user_states[user_id]["to_currency"] = currency

        if "amount" not in user_states[user_id]:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入金額"))
            return

        amount = user_states[user_id]["amount"]
        from_currency = user_states[user_id]["from_currency"]
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
        # 重置狀態以便下次重新開始匯率轉換
        user_states[user_id] = None

def send_financial_tip(reply_token):
    import random
    tip = random.choice(financial_tips)
    message = f"{tip['title']}\n{tip['content']}"
    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text=message)
    )

def ask_currency(reply_token, text, prefix):
    currencies = list(exchange_rates.keys())
    actions = [QuickReplyButton(action=PostbackAction(label=currency, data=f"{prefix}={currency}")) for currency in currencies]
    quick_reply = QuickReply(items=actions[:13])  # LINE quick reply 有 13 個按鈕限制
    
    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text=text, quick_reply=quick_reply)
    )

def show_main_menu(reply_token):
    buttons_template = ButtonsTemplate(
        title='主選單',
        text='請選擇功能',
        actions=[
            MessageAction(label='理財小知識', text='理財小知識'),
            MessageAction(label='匯率轉換', text='匯率轉換'),
            MessageAction(label='財經新聞', text='財經新聞'),
            MessageAction(label='股票資訊', text='股票資訊')
        ]
    )
    message = TemplateSendMessage(alt_text='主選單', template=buttons_template)
    line_bot_api.reply_message(reply_token, message)

if __name__ == "__main__":
    app.run(debug=True)

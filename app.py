pip install flask line-bot-sdk requests beautifulsoup4
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageAction

import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Line Bot 的 Channel Access Token 和 Channel Secret
LINE_CHANNEL_ACCESS_TOKEN = '+m9MsMlBbX6xUkenrdglsJ4dui9Iv1SKwaAQQSBqHA2yGAibmFDqR6Dh6utNRj/QDJ6vRZe3sFN2SEHDLzC4d/1v+ieyXfS3rMLXNMkay13yBp1A8waU8PkCaPgpWmL5XZ56NDsilEo8NXO4NE9EFwdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '1a1abae950e5754d3011ae1c24ce6650'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 爬取銀行匯率數據的函數
def get_bank_a_exchange_rate():
    url = "https://www.banka.com/exchange-rates"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    rates = {
        "USD": float(soup.find(id="usd-rate").text),
        "EUR": float(soup.find(id="eur-rate").text),
        "GBP": float(soup.find(id="gbp-rate").text)
    }
    return rates

def get_bank_b_exchange_rate():
    url = "https://www.bankb.com/exchange-rates"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    rates = {
        "USD": float(soup.find(id="usd-rate").text),
        "EUR": float(soup.find(id="eur-rate").text),
        "GBP": float(soup.find(id="gbp-rate").text)
    }
    return rates

def get_bank_c_exchange_rate():
    url = "https://www.bankc.com/exchange-rates"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    rates = {
        "USD": float(soup.find(id="usd-rate").text),
        "EUR": float(soup.find(id="eur-rate").text),
        "GBP": float(soup.find(id="gbp-rate").text)
    }
    return rates

@app.route("/", methods=['POST'])
def callback():
    # 獲取 X-Line-Signature header 值
    signature = request.headers['X-Line-Signature']

    # 獲取請求的 body
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 處理 webhook 主體
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == "查看匯率":
        buttons_template = ButtonsTemplate(
            title='選擇銀行', text='請選擇您要查看的銀行匯率', actions=[
                MessageAction(label='銀行 A', text='銀行 A 匯率'),
                MessageAction(label='銀行 B', text='銀行 B 匯率'),
                MessageAction(label='銀行 C', text='銀行 C 匯率')
            ])
        template_message = TemplateSendMessage(
            alt_text='Buttons template', template=buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif event.message.text == "銀行 A 匯率":
        rates = get_bank_a_exchange_rate()
        response = f"銀行 A 匯率:\nUSD: {rates['USD']}\nEUR: {rates['EUR']}\nGBP: {rates['GBP']}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
    elif event.message.text == "銀行 B 匯率":
        rates = get_bank_b_exchange_rate()
        response = f"銀行 B 匯率:\nUSD: {rates['USD']}\nEUR: {rates['EUR']}\nGBP: {rates['GBP']}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
    elif event.message.text == "銀行 C 匯率":
        rates = get_bank_c_exchange_rate()
        response = f"銀行 C 匯率:\nUSD: {rates['USD']}\nEUR: {rates['EUR']}\nGBP: {rates['GBP']}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入 '查看匯率' 來查看匯率資訊"))

if __name__ == "__main__":
    app.run()


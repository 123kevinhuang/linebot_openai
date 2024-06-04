from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import tempfile, os
import datetime
import traceback

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

def GPT_response(text):
    # Dummy response function
    answer = "這是預設的回答，因為OpenAI已被移除。"
    return answer

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    try:
        GPT_answer = GPT_response(msg)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        app.logger.error(traceback.format_exc())
        line_bot_api.reply_message(event.reply_token, TextSendMessage('發生錯誤，請稍後再試。'))

@handler.add(PostbackEvent)
def handle_postback(event):
    app.logger.info(f"Postback data: {event.postback.data}")

@handler.add(MemberJoinedEvent)
def welcome(event):
    try:
        uid = event.joined.members[0].user_id
        gid = event.source.group_id
        profile = line_bot_api.get_group_member_profile(gid, uid)
        name = profile.display_name
        message = TextSendMessage(text=f'{name}歡迎加入')
        line_bot_api.reply_message(event.reply_token, message)
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        app.logger.error(traceback.format_exc())

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

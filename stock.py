elif text == "股票查詢":
    user_states[user_id] = "stock_selection"
    ask_stock(event.reply_token)
def ask_stock(reply_token):
    # 提供一組預定義的股票代碼
    stock_codes = ["AAPL", "GOOGL", "MSFT", "AMZN", "FB"]
    actions = [MessageAction(label=code, text=code) for code in stock_codes]
    quick_reply = QuickReply(items=actions)

    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text="請選擇要查詢的股票代碼或直接輸入股票代碼。", quick_reply=quick_reply)
    )
elif user_states.get(user_id) == "stock_selection":
    # 用戶發送了股票代碼
    stock_code = text.upper()  # 將股票代碼轉換為大寫
    stock_info = get_stock_info(stock_code)
    if stock_info:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=stock_info)
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"抱歉，無法獲取股票代碼 {stock_code} 的資訊。")
        )
    # 清除用戶的狀態
    user_states[user_id] = None

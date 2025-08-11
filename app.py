# -*- coding: utf-8 -*-

# 載入我們需要的工具
import os
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 初始化 Flask App
app = Flask(__name__)

@app.get("/health")
def health():
    return ("OK", 200)

# 從「環境變數」中取得金鑰 (這是安全的作法)
CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', None)
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', None)

# 檢查金鑰是否存在，這一步對於除錯非常重要
if CHANNEL_SECRET is None:
    print('錯誤: 找不到 LINE_CHANNEL_SECRET 環境變數')
if CHANNEL_ACCESS_TOKEN is None:
    print('錯誤: 找不到 LINE_CHANNEL_ACCESS_TOKEN 環境變數')

# 初始化 LINE Bot API 和 Webhook Handler
# 確保在金鑰存在時才進行初始化
if CHANNEL_SECRET and CHANNEL_ACCESS_TOKEN:
    line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(CHANNEL_SECRET)
else:
    # 如果金鑰不存在，程式無法啟動，直接退出
    print("錯誤: 金鑰不完整，程式無法啟動。")
    exit()


# 設定 Webhook 的進入點，這就是我們要給 LINE 的網址路徑
@app.route("/callback", methods=['POST'])
def callback():
    # 取得 X-Line-Signature HTTP 標頭的值
    signature = request.headers['X-Line-Signature']

    # 以文字形式取得請求的內容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 處理 Webhook 事件
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("簽名錯誤，請檢查你的 channel secret 是否正確。")
        abort(400)
    except Exception as e:
        print(f"處理訊息時發生錯誤: {e}")
        abort(400)

    return 'OK', 200


# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 將收到的訊息原封不動地回傳
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )


# 主程式進入點
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



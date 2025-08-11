# -*- coding: utf-8 -*-

# 載入我們需要的工具
import os
from flask import Flask, request, abort

# 【重要】我們使用的是新版的 line-bot-sdk，這是正確的匯入路徑
from linebot import LineBotApi, WebhookHandler
from line_bot_sdk.exceptions import (
    InvalidSignatureError
)
from line_bot_sdk.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

# 初始化 Flask App
app = Flask(__name__)

# 從「環境變數」中取得金鑰
CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', None)
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', None)

# 檢查金鑰是否存在，這一步對於除錯非常重要
if not CHANNEL_SECRET or not CHANNEL_ACCESS_TOKEN:
    print("錯誤：LINE_CHANNEL_SECRET 或 LINE_CHANNEL_ACCESS_TOKEN 環境變數未設定。")
    # 在實際部署時，如果金鑰不完整，程式可能會無法正常處理 LINE 的請求
    # 但我們讓它繼續運行，以便 /health 路由可以作用

# 只有在金鑰完整時，才初始化 LINE 的處理工具
try:
    line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(CHANNEL_SECRET)
except Exception as e:
    print(f"初始化 LINE SDK 時發生錯誤: {e}")
    # 即使初始化失敗，也讓程式繼續跑，以便 /health 路由可以作用
    line_bot_api = None
    handler = None

# 【新增】健康檢查路由 (Health Check Endpoint)
# 這是雲端服務的最佳實踐，讓平台可以檢查我們的程式是否還活著
@app.route("/health", methods=['GET'])
def health_check():
    return 'OK', 200

# 設定 Webhook 的進入點
@app.route("/callback", methods=['POST'])
def callback():
    # 檢查 LINE 的處理工具是否已成功初始化
    if not handler:
        print("錯誤: LINE handler 未初始化，無法處理請求。")
        abort(500) # 500 代表伺服器內部錯誤

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

    return 'OK'


# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 確保 line_bot_api 也已成功初始化
    if not line_bot_api:
        print("錯誤: line_bot_api 未初始化，無法回覆訊息。")
        return

    # 將收到的訊息原封不動地回傳
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )


# 主程式進入點
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


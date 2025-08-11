# -*- coding: utf-8 -*-

# 載入我們需要的工具
import os
import sys
from flask import Flask, request, abort

# 根據官方文件，我們安裝的是 line-bot-sdk，但匯入時要用 linebot
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

# 初始化 Flask App
app = Flask(__name__)

# 從「環境變數」中取得金鑰
CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

# 嚴格的金鑰檢查
if not CHANNEL_SECRET or not CHANNEL_ACCESS_TOKEN:
    print("錯誤：LINE_CHANNEL_SECRET 或 LINE_CHANNEL_ACCESS_TOKEN 環境變數未設定。")
    sys.exit(1) # 結束程式，並回報錯誤狀態

# 初始化 LINE SDK
try:
    line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(CHANNEL_SECRET)
except Exception as e:
    print(f"初始化 LINE SDK 時發生錯誤: {e}")
    sys.exit(1) # 結束程式，並回報錯誤狀態

# 健康檢查路由，方便我們確認服務是否活著
@app.route("/health", methods=['GET'])
def health_check():
    return 'OK', 200

# Webhook 的主要入口
@app.route("/callback", methods=['POST'])
def callback():
    # 取得 X-Line-Signature HTTP 標頭的值
    signature = request.headers.get('X-Line-Signature')
    if signature is None:
        app.logger.warning("請求缺少 X-Line-Signature 標頭")
        abort(400)

    # 以文字形式取得請求的內容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 處理 Webhook 事件
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.exception("簽名驗證錯誤：請檢查您的 CHANNEL_SECRET 是否正確。")
        abort(400)
    except LineBotApiError as e:
        app.logger.exception(f"LINE API 錯誤: {e}")
        abort(500)
    except Exception as e:
        app.logger.exception(f"處理訊息時發生未知錯誤: {e}")
        abort(500)

    return 'OK', 200

# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        # 將收到的訊息原封不動地回傳
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text)
        )
    except LineBotApiError as e:
        # 回覆訊息失敗時 (例如 token 過期)，記錄詳細錯誤
        app.logger.error(f"回覆訊息時發生 LINE API 錯誤: {e}")

# 主程式進入點
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    # 在 Railway 上，這段不會被執行，它會直接使用 gunicorn
    app.run(host='0.0.0.0', port=port)

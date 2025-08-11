# -*- coding: utf-8 -*-
import os
from flask import Flask, request

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 讀環境變數，但「先不退出」
CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

line_bot_api = None
handler = None
if CHANNEL_SECRET and CHANNEL_ACCESS_TOKEN:
    try:
        line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
        handler = WebhookHandler(CHANNEL_SECRET)
        app.logger.info("LINE SDK initialized.")
    except Exception as e:
        app.logger.exception(f"初始化 LINE SDK 失敗: {e}")
else:
    app.logger.warning("LINE 金鑰未設定，/callback 暫不可用。")

@app.route("/", methods=['GET'])
def index():
    return "I'm alive.", 200

@app.route("/health", methods=['GET'])
def health_check():
    status = "OK (LINE ready)" if handler else "OK (LINE keys missing)"
    return status, 200

@app.route("/callback", methods=['POST'])
def callback():
    if handler is None:
        # 服務活著，但尚未設定；回 503 讓你知道需要設變數
        return 'Service not configured (missing LINE keys)', 503

    signature = request.headers.get('X-Line-Signature')
    if signature is None:
        app.logger.warning("缺少 X-Line-Signature")
        return 'Bad Request', 400

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.exception("簽名驗證錯誤：請檢查 CHANNEL_SECRET")
        return 'Invalid signature', 400
    except LineBotApiError as e:
        app.logger.exception(f"LINE API 錯誤: {e}")
        return 'OK', 200  # 避免 LINE 重試風暴
    except Exception as e:
        app.logger.exception(f"處理訊息未知錯誤: {e}")
        return 'OK', 200

    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text)
        )
    except LineBotApiError as e:
        app.logger.exception(f"回覆訊息時發生 LINE API 錯誤: {e}")
    except Exception as e:
        app.logger.exception(f"未知錯誤: {e}")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

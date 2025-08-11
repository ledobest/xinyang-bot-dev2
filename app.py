# -*- coding: utf-8 -*-

import os
import sys
from flask import Flask, request

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

if not CHANNEL_SECRET or not CHANNEL_ACCESS_TOKEN:
    print("錯誤：LINE_CHANNEL_SECRET 或 LINE_CHANNEL_ACCESS_TOKEN 環境變數未設定。")
    sys.exit(1)

try:
    line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(CHANNEL_SECRET)
except Exception as e:
    print(f"初始化 LINE SDK 時發生錯誤: {e}")
    sys.exit(1)

@app.route("/", methods=['GET'])
def index():
    return "I'm alive.", 200

@app.route("/health", methods=['GET'])
def health_check():
    return 'OK', 200

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    if signature is None:
        app.logger.warning("缺少 X-Line-Signature 標頭")
        return 'Bad Request', 400

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.exception("簽名驗證錯誤：請檢查 CHANNEL_SECRET")
        # 非法請求才回 400，避免 LINE 一直重試
        return 'Invalid signature', 400
    except LineBotApiError as e:
        # 盡量把可用資訊都打出來
        app.logger.exception(f"LINE API 錯誤: {e}")
        return 'OK', 200  # 回 200 以避免重試風暴
    except Exception as e:
        app.logger.exception(f"處理訊息時發生未知錯誤: {e}")
        return 'OK', 200  # 同上

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

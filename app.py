# -*- coding: utf-8 -*-
import os, hmac, hashlib, base64, threading
from flask import Flask, request, abort

from line_bot_sdk import LineBotApi, WebhookHandler
from line_bot_sdk.exceptions import InvalidSignatureError
from line_bot_sdk.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 讀環境變數
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
if not CHANNEL_SECRET:
    print("錯誤: 找不到 LINE_CHANNEL_SECRET 環境變數")
if not CHANNEL_ACCESS_TOKEN:
    print("錯誤: 找不到 LINE_CHANNEL_ACCESS_TOKEN 環境變數")
if not CHANNEL_SECRET or not CHANNEL_ACCESS_TOKEN:
    raise SystemExit("錯誤: 金鑰不完整，程式無法啟動。")

# LINE SDK
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 健康檢查
@app.get("/health")
def health():
    return ("OK", 200)

# Webhook 入口：先驗簽 -> 立刻回 200 -> 背景處理
@app.post("/callback")
def callback():
    # 原始 bytes 與 header
    body_bytes = request.get_data()           # bytes
    body_text  = body_bytes.decode("utf-8")   # str（給 handler 用）
    signature  = request.headers.get("X-Line-Signature", "")

    # 輕量簽章驗證（使用原始 bytes）
    digest = hmac.new(CHANNEL_SECRET.encode("utf-8"), body_bytes, hashlib.sha256).digest()
    signature_calc = base64.b64encode(digest).decode("utf-8")
    if signature != signature_calc:
        # 簽章不符：不要回 200，讓 Verify 知道失敗
        return ("", 403)

    # 驗簽通過：立刻回 200，避免 Verify 超時
    threading.Thread(target=_handle_async, args=(body_text, signature), daemon=True).start()
    return ("", 200)

def _handle_async(body_text: str, signature: str):
    try:
        handler.handle(body_text, signature)
    except InvalidSignatureError:
        # 理論上不會進來（已先驗過），保險起見
        print("[ERROR] InvalidSignatureError (async)")
    except Exception as e:
        print(f"[ERROR] handle exception: {e}")

# 文字回覆（echo 範例）
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text)
        )
    except Exception as e:
        print(f"[ERROR] reply_message exception: {e}")

if __name__ == "__main__":
    # Railway 需監聽 0.0.0.0:$PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

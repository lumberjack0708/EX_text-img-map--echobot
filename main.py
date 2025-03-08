from flask import Flask, request, abort, send_from_directory
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    ImageMessage, ImageSendMessage, LocationMessage
)
import dotenv
import os

# 初始化 Flask 與 dotenv
app = Flask(__name__)
dotenv.load_dotenv()

# 從環境變數讀取設定值
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
Ngrok = os.getenv("Ngrok_url")
print("Ngrok URL:", Ngrok)

# 建立 LINE Bot API 與 WebhookHandler (v2)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    # 取得 LINE 傳來的簽章與 request body
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@app.route('/image/<path:filename>')
def serve_image(filename):
    # 提供 image 資料夾內的檔案
    return send_from_directory('image', filename)

# 處理文字訊息：回覆「收到」
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    print("收到文字訊息:", event.message.text)
    reply_message = TextSendMessage(text="收到")
    line_bot_api.reply_message(event.reply_token, reply_message)

# 處理地址訊息：回覆「地址資訊」
@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    reply_message = TextSendMessage(text="地址資訊")
    line_bot_api.reply_message(event.reply_token, reply_message)

# 處理圖片訊息：下載圖片後回覆本地圖片連結
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    # 確保 image 資料夾存在
    if not os.path.exists("image"):
        os.mkdir("image")
    
    # 取得圖片內容
    message_content = line_bot_api.get_message_content(event.message.id)
    file_path = "image/test.jpg"
    print("儲存圖片至:", file_path)
    
    with open(file_path, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)
    
    # 產生公開可存取的圖片 URL，必須為 HTTPS
    image_url = f"{Ngrok}/image/test.jpg"
    print("圖片 URL:", image_url)
    
    reply_message = ImageSendMessage(
        original_content_url=image_url,
        preview_image_url=image_url
    )
    line_bot_api.reply_message(event.reply_token, reply_message)

if __name__ == '__main__':
    app.run(debug=True)
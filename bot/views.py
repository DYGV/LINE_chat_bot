# -*- encoding: utf-8 -*-
import json
import sys
import requests
from django.http import HttpResponse
import qrcode
from datetime import datetime
sys.path.append('LINE_bot/modules')
from modules import fragments, API_call, Config_Load

load_ = Config_Load.C_Config().load(2)
REPLY_ENDPOINT = load_['reply_endpoint']
ACCESS_TOKEN = load_['access_token']

HEADER = {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + ACCESS_TOKEN
}


def index(request):
    now = datetime.now()
    html = "<html><body>This is bot api.\n\n now %s.</body></html>" % now
    return HttpResponse(html)


def qr(reply_token, text):
    """textからQRコードを生成"""
    img = qrcode.make(text)  # "text"からQRコード生成
    api = API_call.APIs(1)
    up = api.upload(img)

    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "image",
                "originalContentUrl": up,
                "previewImageUrl": up
            }
        ]
    }
    requests.post(REPLY_ENDPOINT, headers=HEADER,
                  data=json.dumps(payload))
    return qr


def reply_text(reply_token, text, info):
    """docomo APIを使って返信"""
    profile_url = "https://api.line.me/v2/bot/profile/" + info
    profile = requests.get(profile_url, headers=HEADER)

    reply_class = API_call.APIs(0)
    reply = reply_class.reply(text, info, profile)
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": reply
            }
        ]
    }
    requests.post(REPLY_ENDPOINT, headers=HEADER,
                  data=json.dumps(payload))
    return reply_text


def sticker(reply_token):
    """スタンプを返す"""
    pkg, stk = fragments.sticker_id()
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "sticker",
                "packageId": pkg,
                "stickerId": stk,
            }
        ]
    }

    requests.post(REPLY_ENDPOINT, headers=HEADER,
                  data=json.dumps(payload))
    return sticker


def image(reply_token, content_id):
    """画像認識"""
    uri = "https://api.line.me/v2/bot/message/" + content_id + "/content"
    r = requests.get(uri, headers=HEADER)

    reply_class = API_call.APIs(4)
    image_bin = r.content
    res_image, caption = reply_class.image_recognition(image_bin)

    if "https://" in res_image:

        payload_image = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "image",
                    "originalContentUrl": res_image,
                    "previewImageUrl": res_image
                },
                {
                    "type": "text",
                    "text": caption,
                }
            ]
        }
        requests.post(REPLY_ENDPOINT, headers=HEADER,
                      data=json.dumps(payload_image))
    else:

        payload_describe = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "text",
                    "text": caption,
                }
            ]
        }
        requests.post(REPLY_ENDPOINT, headers=HEADER,
                      data=json.dumps(payload_describe))
    return image


def callback(request):
    request_json = json.loads(request.body.decode("utf-8"))  # requestの情報を取得
    for e in request_json["events"]:
        reply_token = e["replyToken"]  # get token
        message_type = e["message"]["type"]  # メッセージタイプ取得
        info = e["source"]["userId"]

        if message_type == "text":
            text = e["message"]["text"]  # メッセージ取得

            if "http://" in text or "www" in text and ".com" in text or ".jp" in text or ".net" in text \
                                                                       or ".info" in text or ".org" in text or ".co" in text:
                qr(reply_token, text)
                return HttpResponse(text)

            else:
                reply_text(reply_token, text, info)
                return HttpResponse(text)

        if message_type == "sticker":
            sticker_id = e["message"]["stickerId"]
            sticker(reply_token)
            return HttpResponse(sticker_id)

        elif message_type == "image":
            content_id = e["message"]["id"]  # メッセージIDの取得
            image(reply_token, content_id)
            return HttpResponse(content_id)

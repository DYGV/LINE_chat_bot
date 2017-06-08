# -*- encoding: utf-8 -*-
from boto.s3 import connection, key
from firebase import firebase
from PIL import Image, ImageDraw
import struct
from . import Config_Load
from . import fragments
import json
import requests


class APIs:
    def __init__(self, number):     # configの場所を呼び出されるときに指定しておく
        load_ = Config_Load.C_Config()
        self.CONFIG = load_.load(number)

    def firebase_login(self):

        authentication = firebase.FirebaseAuthentication(self.CONFIG["api_key"], self.CONFIG["e-mail"])
        firebase.authentication = authentication
        firebases = firebase.FirebaseApplication(self.CONFIG["app_url"], authentication)
        return firebases

    def reply(self, text, info, profile):
        """docomo チャット API
        """
        url = self.CONFIG['endpoint'] + "dialogue/v1/dialogue?APIKEY=" + self.CONFIG['api_key']

        auth = APIs(3)
        get_context = auth.firebase_login().get("/users/" + profile.json()["displayName"], None)

        if get_context is None:
            payload = {
                "utt": text,
                "t": 30,
            }

            post = requests.session().post(url, data=json.dumps(payload))
            res_json = json.loads(post.text)
            context = res_json["context"]
            data = {
                "user_identifier": info,
                "talk_context_id": context,
                "profile_img_url": profile.json()["pictureUrl"]
            }
            get_context.login().put("/users/", profile.json()["displayName"], data)
            return res_json["utt"]

        else:
            payload = {
                "utt": text,
                "context": get_context["talk_context_id"]
            }
            post = requests.session().post(url, data=json.dumps(payload))
            res_json = json.loads(post.text)

            return res_json["utt"]

    def face_recognition(self, image_bin):
        """Microsoft Face API
        """
        headers = {
            "Content-Type": "application/octet-stream",
            "Ocp-Apim-Subscription-Key": self.CONFIG['face_api'],
        }

        aa = requests.post(
            "https://westus.api.cognitive.microsoft.com/face/v1.0/detect?returnFaceId=true&returnFaceLandmarks=false",
            image_bin
            , headers=headers)
        bb = json.loads(aa.text)

        with open("img.jpg", "wb") as fout:
            for x in image_bin:
                fout.write(struct.pack("B", x))  # バイナリファイルの生成
        img = Image.open("./img.jpg")
        for face in bb:
            f_rec = face['faceRectangle']
            width = f_rec['width']
            height = f_rec['height']
            left = f_rec['left']
            top = f_rec['top']

            draw = ImageDraw.Draw(img)
            loc = (left, top, left + width, top + height)
            line = (loc[0], loc[1], loc[0], loc[3])
            draw.line(line, fill="red", width=3)
            line = (loc[0], loc[1], loc[2], loc[1])
            draw.line(line, fill="red", width=3)
            line = (loc[0], loc[3], loc[2], loc[3])
            draw.line(line, fill="red", width=3)
            line = (loc[2], loc[1], loc[2], loc[3])
            draw.line(line, fill="red", width=3)
            draw.ellipse((left, top, left + width, top + height), outline="red")

        img_name = 'test.png'
        img.save(img_name, 'PNG')
        aa = APIs(1)
        up = aa.upload(img)
        return up

    def image_recognition(self, image_bin):
        """Microsoft Computer Vision API
        """

        headers = {
            "Content-Type": "application/octet-stream",
            "Ocp-Apim-Subscription-Key": self.CONFIG['api_key'],
        }
        aa = requests.post("https://westus.api.cognitive.microsoft.com/vision/v1.0/analyze?visualFeatures=Description",
                           image_bin
                           , headers=headers)
        bb = json.loads(aa.text)

        tags = bb["description"]["tags"]

        for i in tags:
            if "person" in i or "people" in i:
                return APIs.face_recognition(self, image_bin), bb["description"]["captions"][0]["text"]
            else:
                return "", str(bb["description"]["captions"][0]["text"])

        return str(bb["description"]["captions"][0]["text"])

    def upload(self, img):
        """ S3に画像up
        """
        conn = connection.S3Connection(self.CONFIG['access_id'], self.CONFIG['secret_key'])
        bucket = conn.get_bucket(self.CONFIG['bucket_name'])
        file_name = fragments.gen_rand_str()
        k = key.Key(bucket, file_name)
        k.set_contents_from_string(fragments.process(img), headers={"Content-Type": "image/png"})

        expire_second = 600  # URL 有効時間(秒)
        return conn.generate_url(expire_second, method="GET",
                                 bucket=self.CONFIG['bucket_name'], key=file_name)

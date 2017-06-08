# -*- encoding: utf-8 -*-
from boto.s3 import connection, key
from firebase import firebase
from PIL import Image, ImageDraw
import struct
import requests
import json
from . import Config_Load
from . import fragments
import json
from modules import conversion
from goolabs import GoolabsAPI
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

        auth = APIs(4)
        get_context = auth.firebase_login()
        get_context.get("/users/" + profile.json()["displayName"], None)
        url = self.CONFIG['endpoint'] + "dialogue/v1/dialogue?APIKEY=" + self.CONFIG['api_key']

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
        aa = APIs(2)
        up = aa.upload(img)
        return up

    def image_recognition(self, image_bin):
        """Microsoft Computer Vision API
        """
        load = self.CONFIG(6)['api_key']

        headers = {
            "Content-Type": "application/octet-stream",
            "Ocp-Apim-Subscription-Key": load,
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

    def loc_to_hiragana(self, text):

        """地名判別とローマ字化
        """
        api_key = self.CONFIG["api_key"]
        api = GoolabsAPI(api_key)

        refinements = ["市", "町", "村", "区"]

        for elem in refinements:
            if elem in text:

                url ="gooLanguageAnalysisCorp/v1/entity?APIKEY=" + api_key

                payload = {
                    "sentence": text,
                    "class_filter": "LOC"
                }
                headers = {"content-type": "application/json"}
                post = requests.post(url, data=json.dumps(payload), headers=headers)
                res_json = json.loads(post.text)["ne_list"]

                for i in res_json:
                    if (i, "LOC" in i) is True:
                        pass
                else:
                    idx = i[0].rfind(str(refinements))  # iからrefinementsを探す
                    n_set = set(i[0])  # 重複しないn
                    refine_set = set(refinements)
                    matched = "".join(n_set & refine_set)
                    result = i[0][:idx] + "-" + matched

                    api.hiragana(
                        request_id="hiragana-req001",
                        sentence=result,
                        output_type="hiragana"  # "hiragana" or "katakana"
                    )
                    convert = api.response.json()["converted"]  # 変換

                i[0], conversion.kana2romaji(convert)
                load_ = Config_Load.C_Config().load(1)
                OPEN_WEATHER_APP_ID = load_["api_key"]
                OPEN_WEATHER_URL = load_["endpoint"]

                payload = {"q": conversion.kana2romaji(convert), "mode": "json", "units": "metric",
                           "APPID": OPEN_WEATHER_APP_ID
                           }
                response = requests.get(OPEN_WEATHER_URL, params=payload)
                if response.json()["cod"] == 200:

                    weather = response.json()["main"]
                    temp = weather["temp"]
                    pressure = weather["pressure"]
                    humidity = weather["humidity"]
                    wet = response.json()["weather"][0]["main"]
                    wind_speed = response.json()["wind"]["speed"]
                    id = response.json()["id"]

                    Photo_ENDPOINT = "https://static.pexels.com/photos/"

                    switch = {
                        "Rain": {"Weather": "雨", "url": Photo_ENDPOINT + "110874/pexels-photo-110874.jpeg"},
                        "Clouds": {"Weather": "曇り", "url": Photo_ENDPOINT + "216596/pexels-photo-216596.jpeg"},
                        "Sun": {"Weather": "晴れ", "url": Photo_ENDPOINT + "3768/sky-sunny-clouds-cloudy.jpg"},
                        "Fog": {"Weather": "霧", "url": Photo_ENDPOINT + "17579/pexels-photo.jpg"},
                        "Extreme": {"Weather": "異常気象", "url": Photo_ENDPOINT + "153971/pexels-photo-153971.jpeg"},
                        "Clear": {"Weather": "快晴", "url": Photo_ENDPOINT + "205335/pexels-photo-205335.jpeg"}
                    }

                    get_weather = switch.get(wet)
                    return i[0], get_weather["url"], "https://openweathermap.org/city/" + str(id), get_weather[
                        "Weather"] \
                           + "気温:{0}℃    湿度:{1}%\n風速:{2}m/s    気圧:{3}hPaです".format(temp, humidity, wind_speed,
                                                                                   pressure)

                else:
                    # とりあえず...ね
                    url = "https://cdn.pixabay.com/photo/2016/10/04/13/52/fail-1714367_960_720.jpg"
                    error = "https://kotobank.jp/word/%E5%A4%B1%E6%95%97-521649"
                    return i[0], url, error, "取得できませんでした。"

        else:
            url = "https://cdn.pixabay.com/photo/2016/10/04/13/52/fail-1714367_960_720.jpg"
            error = "https://kotobank.jp/word/%E5%A4%B1%E6%95%97-521649"
            return None, url, error, "行政区分の名前と一緒に入力してください\n 例　(気温 水戸市)"


    def upload(self,img):
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

# -*- coding: utf-8 -*-
import random
from io import BytesIO
from PIL import Image


def process(img):
    img.thumbnail((400, 600), Image.ANTIALIAS)
    out = BytesIO()
    img.save(out, "PNG")

    return out.getvalue()


def gen_rand_str(length=random.randint(30, 70), chars='_0123456789abcdefghijklmnopqrstuvwxyz'):
    import string
    if chars is None:
        chars = string.digits + string.letters
    return ''.join([random.choice(chars) for i in range(length)])


def sticker_id():
    package_id = random.randint(1, 4)

    if package_id == 1:
        sticker_id = open("bot/Stickers_id/Moon-James.txt").read().split("\n")

    elif package_id == 2:
        sticker_id = open("bot/Stickers_id/Brown-Cony.txt").read().split("\n")

    elif package_id == 3:
        sticker_id = open("bot/Stickers_id/Cherry-Coco.txt").read().split("\n")

    elif package_id == 4:
        sticker_id = open("bot/Stickers_id/Daily-Life.txt").read().split("\n")
    
    return package_id, random.choice(sticker_id)

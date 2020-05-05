import pathlib
import os
import json
import time
import traceback
import copy
import pprint

from bs4 import BeautifulSoup
from datetime import datetime
import requests

import env

# TODO:jsonの元ファイルを手作業で準備してるのでそれを不要にする


SLACK_CHANNEL_ID = env.SLACK_CHANNEL_ID
SLACK_URL = env.SLACK_URL
TOKEN = env.TOKEN

# チャンネルの投稿を全て取得
def fetch_text():
    """ umameshiチャンネルの投稿を取得してjsonに変換

    Returns:
        str: チャンネル投稿のデータjson
    """

    payload = {
        "channel": SLACK_CHANNEL_ID,
        "token": TOKEN
    }
    response = requests.get(SLACK_URL, params=payload)
    json_data = response.json()
    return json_data


def get_last_update_ts():
    """ ファイルの最終更新日時の取得

    Returns:
        float: unixtimeの更新日時
    """
    # ファイルの最終更新時刻
    p = pathlib.Path('./text_write_str.json')
    st = p.stat()
    last_updae_ts = float(st.st_mtime)
    return last_updae_ts

def get_message_last_post_ts(msg):
    """ チャンネル投稿の最終投稿日時の取得

    Args:
        msg (str): チャンネル投稿内容のmessage key配下のjson

    Returns:
        float: unixtimeの最終投稿日時
    """
    # 最終投稿時間の取得
    msg_ts = sorted([ts["ts"] for ts in msg])
    last_post_ts = float(msg_ts[len(msg_ts)-1])
    return last_post_ts


def main():
    # チャンネルの投稿を取得
    json_data = fetch_text()
    # print("チャンネル投稿", json_data)
    msg = json_data["messages"]

    # 保存されてるファイルの最終更新日と取得したメッセージの最終投稿日を取得
    last_updae_ts = get_last_update_ts()
    last_post_ts = get_message_last_post_ts(msg)
    print("最終更新", last_updae_ts, type(last_updae_ts))
    print("最終投稿", last_post_ts, type(last_post_ts))

    msg2 = []
    if last_post_ts > last_updae_ts:
        for index, conents in enumerate(msg):
            # print(conents["ts"])
            if float(conents["ts"]) > last_updae_ts:
                print("通ったindex", index)
                # pprint.pprint(conents)
                msg2.append(conents)

    if msg2:
        restaurant_data = get_url(msg2)
        # pprint.pprint(restaurant_data)
        return_data = get_restaurant_info(restaurant_data)

        result = json.dumps(return_data, ensure_ascii=False)

        # 書き込む
        # ファイルが既に存在していた場合は、ファイルの中身を空にして開く
        with open("text_write_str.json", 'wt') as f:
            f.write(result)
        print("json.dumpsルート")
        return result
    else:
        # 読み込む
        with open("./text_write_str.json", "r") as d:
            str_data = d.read()
            # str_data = json.load(d)
        print("特に更新もないルート")
        return json.dumps(str_data, ensure_ascii=False)

    # pprint.pprint(msg2)
    return msg2


# tabelogURLのリスト
def get_url(msg):
    # tabelog_list = []
    restaurant_data = {}

    for contents in msg:
        try:
            msg_id = contents["client_msg_id"]
            contents_link = contents["attachments"][0]["title_link"]
            if "tabelog" in contents_link:
                print("true")
                restaurant_data[msg_id] = contents_link

        except KeyError:
            continue
    
    return restaurant_data
    


# スクレイピングでデータ取得

def set_format(msg_id, title, address, genre, og_img):
    data = {"msg_id": msg_id, "title": title,
            "address": address, "genre": genre, "og_img": og_img}
    return data

def get_restaurant_info(restaurant_data):
    """ tabelogから必要な情報を取得する

    Args:
        restaurant_data (dict): {"msg_id":"tabelog url"}

    Returns:
        list: [{"msg_id": msg_id, "title": title,
            "address": address, "genre": genre, "og_img": og_img}] 
    """
    # 読み込む
    with open("./text_write_str.json", "r") as d:
        str_data = d.read()
    return_data = (json.loads(str_data))
    # return_data = []

    for k, v in restaurant_data.items():
        try:
            print("url",v)
            time.sleep(3)
            response = requests.get(v).text
            soup = BeautifulSoup(response, "html.parser")

            title = soup.select_one(
                "#rstdtl-head > div.rstdtl-header > section > div.rdheader-title-data > div.rdheader-rstname-wrap > div > h2 > span").text.strip()
            address = soup.select_one(
                "#contents-rstdata > div.rstinfo-table > table:nth-child(2) > tbody > tr:nth-child(5) > td > p").text
            genre = soup.select_one(
                "#contents-rstdata > div.rstinfo-table > table:nth-child(2) > tbody > tr:nth-child(2) > td > span").text

            og_img = soup.find('meta', attrs={'property': 'og:image', 'content': True})[
                "content"]
            print("og_img", og_img)

            return_data.append(set_format(k, title, address, genre, og_img))
             
            return return_data
        except:
            traceback.print_exc()
            continue


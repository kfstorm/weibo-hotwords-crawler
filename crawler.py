import requests
import json
import re
import datetime
import sys
import os

DO_COMPRESS = False

currnt_time = datetime.datetime.now()

body = None
hotwords = None
error = None

try:
    url = 'https://m.weibo.cn/api/container/getIndex?containerid=106003type%3D25%26t%3D3%26filter_type%3Drealtimehot'
    response = requests.get(url)
    assert response
    body = response.content.decode("utf-8")

    body_obj = json.loads(body)
    assert body_obj["ok"]

    lists = [_ for _ in body_obj["data"]["cards"] if _.get("itemid") == "hotword"]
    assert len(lists) == 1
    hotwords = lists[0]["card_group"]

    def extract_hotword(hotword):
        desc_extr = hotword.get("desc_extr")
        if not desc_extr:
            return None
        if isinstance(desc_extr, int):
            hot_value = desc_extr
            tags = []
        else:
            assert isinstance(desc_extr, str)
            parts = desc_extr.split(" ")
            numbers = [_ for _ in parts if _.isdigit()]
            assert len(numbers) == 1
            hot_value = int(numbers[0])
            tags = list(set(parts) - set(numbers))
        m = re.match(r".*img_search_(\d+).*", hotword["pic"])
        if not m:
            return None
        rank = int(m.group(1))
        value = {
            "word": hotword["desc"],
            "rank": rank,
            "hot_value": hot_value,
        }
        if tags:
            value["tags"] = tags
        return value

    hotwords = [extract_hotword(_) for _ in hotwords]
    hotwords = [_ for _ in hotwords if _]

    assert len(hotwords) == 50
except Exception as e:
    error = str(e)

output = {
    "fetch_time": currnt_time.astimezone().isoformat(),
}
if error:
    output["error"] = error
    output["http_body"] = body
else:
    output["hotwords"] = hotwords

output = json.dumps(output, ensure_ascii=False)
output = output.encode("utf-8")
if DO_COMPRESS:
    import zlib
    output = zlib.compress(output)

if len(sys.argv) > 1:
    output_folder = sys.argv[1]
else:
    output_folder = "."
os.makedirs(output_folder, exist_ok=True)

output_filename = os.path.abspath(os.path.join(output_folder, f"output_{currnt_time:%Y-%m-%d_%H-%M-%S}.json"))
with open(output_filename, 'wb') as f:
    f.write(output)

print(f"Fetched hotwords at {currnt_time} and wrote results to {output_filename}. Success: {not error}.")

import requests
import json
import os
import shutil

with open("items_with_links.json", "r") as f:
    item_list = json.load(f)

for row in item_list:
    file_name = "items_with_id/" + str(item_list[row]["id"]) + ".png"
    if not os.path.exists(file_name) or os.path.getsize(file_name) <= 1000:
        url = "https://steamcdn-a.akamaihd.net/" + item_list[row]["img"]
        response = requests.get(url, stream=True)
        print(item_list[row]["id"])
        with open(file_name, "wb") as f:
            shutil.copyfileobj(response.raw, f)

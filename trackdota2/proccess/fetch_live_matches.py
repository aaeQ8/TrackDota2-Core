import json
import requests
import os
import time

# add ?api_key= before the key
api_key = ""
url = "https://api.opendota.com/api/live" + api_key
directory = "database_files/live_matches"

if not os.path.exists(directory):
    os.mkdir(directory)

try:
    r = requests.get(url)
    data = r.json()
    filename = os.path.join(directory, "{}.json".format(time.time()))
    with open(filename + ".part", "w") as f:
        json.dump(data, f)
    os.rename(filename + ".part", filename)
    print("Wrote:", filename)
except Exception as e:
    print(e)

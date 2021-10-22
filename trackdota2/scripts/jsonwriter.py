import json
from collections import defaultdict

dic = defaultdict(dict)
for names in os.listdir(path):
    for filename in os.listdir(path + "/" + names):
        dic[filename.split(" ")[0].strip()]["players"] = [names]
        dic[filename.split(" ")[0].strip()]["extracted_heroes"] = False
        dic[filename.split(" ")[0].strip()]["primary_player"] = names
        if "frame_names" not in dic[filename.split(" ")[0].strip()]:
            dic[filename.split(" ")[0].strip()]["frame_names"] = [filename]
        else:
            dic[filename.split(" ")[0].strip()]["frame_names"].append(filename)

        dic[filename.split(" ")[0].strip()]["heroes"] = []
        if "count" not in dic[filename.split(" ")[0].strip()]:
            dic[filename.split(" ")[0].strip()]["count"] = 0
        else:
            dic[filename.split(" ")[0].strip()]["count"] += 1
with open("test_json.json", "w") as f:
    f.write(json.dumps(dic))

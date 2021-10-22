from trackdota2.frames import FramesDB
import numpy as np
import sqlite3
import os
import boto3
import json


con = sqlite3.connect("database_files/framesdb.sqlite3")
framesDB = FramesDB(con)

folder_path = "database_files/live_matches"
for json_file in os.listdir(folder_path):
    if json_file.endswith(".part") is False:
        with open(os.path.join(folder_path, json_file), "r") as f:
            json_data = json.load(f)
        framesDB.insert_live_games(json_data)
        framesDB.commit()

framesDB.update_is_deleted()
framesDB.add_names_from_matches()
framesDB.update_activate_time_id()
framesDB.extract_titles(ignore_extracted=False)

framesDB.close()

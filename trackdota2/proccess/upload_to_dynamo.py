from frames import FramesDB
from fetchers import FetchMatchDetails
import numpy as np
import sqlite3
import os
import boto3
import time

con = sqlite3.connect("database_files/framesdb.sqlite3")
framesDB = FramesDB(con)

BREAK_POINT = 100
PLAYERS_BREAK_POINT = 300

fetch_match_info = FetchMatchDetails()
framesDB.cursor.execute(
    """
    SELECT m.match_id FROM matches m 
    WHERE m.complete IS NULL AND exists (select mh.is_pro from matches_heroes mh WHERE mh.is_pro = True 
    AND mh.match_id=m.match_id) ORDER BY activate_time DESC;"""
)
match_ids = [x[0] for x in framesDB.cursor.fetchall()]

print("Fetching matches details")
index = 0
for match_id in match_ids:
    if index == BREAK_POINT:
        break
    try:
        details = fetch_match_info.fetch_match_details(match_id)
    except ValueError as e:
        print(e)
    if details is not None:
        index += 1
        framesDB.update_match_details(match_id, details)
    # time.sleep(1)


# Upload to dynamoDB

dynamodb = boto3.resource("dynamodb", region_name="ca-central-1")
matches_table = dynamodb.Table("matches")

print("Uploading matches")
for match_entry in framesDB.get_matches_to_upload():
    try:
        if match_entry is None:
            continue
        matches_table.put_item(Item=match_entry)
    except Exception as e:
        print(e)
    else:
        framesDB.cursor.execute(
            """
            UPDATE matches 
            SET uploaded = True 
            WHERE match_id == ?;""",
            (match_entry["matchid"],),
        )
        framesDB.commit()

players_table = dynamodb.Table("players")
framesDB.cursor.execute(
    """
    SELECT m.match_id, mh.num, m.activate_time_id, mh.player_name, mh.player_id
    FROM matches_heroes mh JOIN matches m on (m.match_id = mh.match_id) 
    WHERE player_name != 'None' AND mh.uploaded IS NULL 
    ORDER BY activate_time_id DESC LIMIT ?;""",
    (PLAYERS_BREAK_POINT,),
)

print("Uploading player matches")
for player_entry in framesDB.cursor.fetchall():
    entry_to_upload = {
        "player_id": player_entry[4],
        "player_name": player_entry[3],
        "activate_time_id": player_entry[2],
    }
    try:
        players_table.put_item(Item=entry_to_upload)
    except Exception as e:
        print(e)
    else:
        framesDB.cursor.execute(
            """
            UPDATE matches_heroes 
            SET uploaded = True
            WHERE match_id == ? AND num == ?;""",
            (player_entry[0], player_entry[1]),
        )
        framesDB.commit()


framesDB.close()

from trackdota2.frames import FramesDB
import sqlite3
import os
import boto3

con = sqlite3.connect("database_files/framesdb.sqlite3")
framesDB = FramesDB(con)

print("Linking matches")
framesDB.link_matches()

dynamodb = boto3.resource("dynamodb", region_name="ca-central-1")
matches_table = dynamodb.Table("matches")
yt_links_table = dynamodb.Table("yt_links")

framesDB.cursor.execute(
    """
	SELECT ml.match_id, ml.yt_id, m.activate_time_id 
	FROM matches_links ml JOIN matches m ON ml.match_id=m.match_id 
        WHERE ml.uploaded != True or ml.uploaded is null;"""
)
links = framesDB.cursor.fetchall()

for link in links:
    print("test", link)

    if link[2] is None:
        continue
    framesDB.cursor.execute(
        "SELECT yt_id from matches_links where match_id=?", (link[0],)
    )
    match_links = [x[0] for x in framesDB.cursor.fetchall()]
    print(link)
    matches_table.update_item(
        Key={"date": link[2].split("T")[0], "activate_time_id": link[2]},
        UpdateExpression="set yt_links=:links",
        ExpressionAttributeValues={":links": match_links},
    )
    print("Updated")
    yt_links_table.put_item(Item={"index": 0, "activate_time_id": link[2]})
    framesDB.cursor.execute(
        "UPDATE matches_links SET uploaded = True WHERE match_id=?", (link[0],)
    )
    framesDB.commit()
    print("Commited")


framesDB.close()

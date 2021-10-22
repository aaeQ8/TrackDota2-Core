from trackdota2.frames import FramesDB
import sqlite3
import os

database_dir = 'database_files'
if not os.path.exists(database_dir):
    os.mkdir(database_dir)

con = sqlite3.connect("database_files/framesdb.sqlite3")
framesDB = FramesDB(con)
framesDB.create_tables()
framesDB.insert_heroes("../../resources/heroes_ids.json")
framesDB.close()


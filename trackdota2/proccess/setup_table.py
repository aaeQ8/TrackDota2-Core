from trackdota2.frames import FramesDB
import sqlite3


con = sqlite3.connect("database_files/framesdb.sqlite3")
framesDB = FramesDB(con)
framesDB.create_tables()
framesDB.insert_heroes("../../resources/heroes_ids.json")
framesDB.close()


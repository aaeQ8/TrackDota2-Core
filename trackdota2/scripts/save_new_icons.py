from frames_classes import FramesDB
import sqlite3
import os
from heroes_classifer import HeroesExtractor
import json
from PIL import Image
import numpy as np

con = sqlite3.connect("asdasd")
framesDB = FramesDB(con)
new_images_folder = "new_images_1"
if not os.path.isdir(new_images_folder):
    os.mkdir(new_images_folder)

with open("heroes_ids.json") as f:
    heroes_ids = json.load(f)

heroes_ids_dic = {}

for hero in heroes_ids:
    heroes_ids_dic[int(hero["id"])] = hero["localized_name"].lower()

frame_files = framesDB.get_images(True, False)
framesDB.cursor.execute("SELECT yt_id, match_id from matches_links;")
matches_links = framesDB.cursor.fetchall()
heroes_extractor = HeroesExtractor()
for link in matches_links:
    print(link[0], link[1])
    framesDB.cursor.execute(
        """
        SELECT f.yt_id, f.file_name, f.full_path 
        FROM yt_frame_files f
        WHERE f.is_valid = True AND f.yt_id=?;""",
        (link[0],),
    )

    file_to_extract = framesDB.cursor.fetchone()
    path_to_save_in = os.path.join(new_images_folder, file_to_extract[1][:-4])
    if os.path.exists(file_to_extract[2]):
        img = Image.open(file_to_extract[2])
        extracted_heroes = heroes_extractor.extract_heroes(np.array(img))
        framesDB.cursor.execute(
            "SELECT hero_id from matches_heroes WHERE match_id=? ORDER BY num ASC;",
            (link[1],),
        )
        names = framesDB.cursor.fetchall()
        print(names)
        if names == []:
            continue
        hero_names = [x[0] for x in names]
        if not os.path.isdir(path_to_save_in):
            os.mkdir(path_to_save_in)
        for index, hero_img in enumerate(extracted_heroes):
            if hero_names[index] == "0":
                continue
            file_name = (
                os.path.join(path_to_save_in, heroes_ids_dic[int(hero_names[index])])
                + ".png"
            )
            if not os.path.exists(file_name):
                print(file_name)
                heroes_extractor.save_extracted_hero(hero_img, file_name)

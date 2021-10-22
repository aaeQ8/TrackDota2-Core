from trackdota2.fetchers import YtFramesFetcher
from trackdota2.frames import FramesDB
from trackdota2.heroes_classifer import HeroesExtractor, HeroesClassifer
import numpy as np
import sqlite3
import os
from PIL import Image
from sklearn.model_selection import train_test_split
import json


def load_labeled_data(image_loc, height, width):

    filename = image_loc.split("/")[-1]
    translation_table = dict.fromkeys(map(ord, "()~1234567890"), None)
    hero_name = filename.split(".")[0].strip()
    hero_name = (
        hero_name.translate(translation_table).strip().lower()
    )  # label class extracted from filename
    hero_image = Image.open(image_loc).convert("RGB").resize((height, width))

    return np.array(hero_image), hero_name


h, w = 50, 20
training_data = []
training_data_path = "../../resources/training_data"
for icon_name in os.listdir(training_data_path):
    training_data.append(
        load_labeled_data(os.path.join(training_data_path, icon_name), h, w)
    )

training_data = np.asarray(training_data, dtype=object)

X_train = np.array([im.flatten() for im in training_data[:, 0]])
y_train = training_data[:, 1]

heroes_clf = HeroesClassifer(X_train, y_train)

con = sqlite3.connect("database_files/framesdb.sqlite3", timeout=30000)
framesDB = FramesDB(con, "database_files/frames_images")

heroes_extractor = HeroesExtractor()

ydl_opts = {
    "playliststart": 1,
    "skip_download": False,
    "playlistend": 6,
    "sleep_interval": 1,
}

yt_frames_fetcher = YtFramesFetcher(
    initial_frame_num=900,
    num_of_frames=2,
    ydl_opts=ydl_opts,
    skip_frame=180,
    skip_valid=True,
)

framesDB.cursor.execute("SELECT hero_id, hero_name from heroes;")
ids = {}
for hero in framesDB.cursor.fetchall():
    ids[hero[1].lower()] = hero[0]

fetched_frames = yt_frames_fetcher.fetch_frames(framesDB.cursor)
for frame_data in fetched_frames:
    try:
        framesDB.cursor.execute(
            """INSERT INTO yt_vids 
            (yt_id, is_highlight, title, duration, upload_date)
            VALUES (?, 'UNKNOWN', ?, ?, ?)""",
            [
                frame_data.vid_entry["id"],
                frame_data.vid_entry["title"],
                frame_data.vid_entry["duration"],
                frame_data.vid_entry["upload_date"],
            ],
        )

        framesDB.commit()

    except sqlite3.IntegrityError:
        print(frame_data.vid_entry["id"], "already in yt_vids")

    finally:
        extracted_heroes = heroes_extractor.extract_heroes(frame_data.frame_image)
        extracted_heroes = heroes_extractor.convert_images_for_model(extracted_heroes)
        predicted_heroes = heroes_clf.predict(extracted_heroes)
        if len(set(predicted_heroes)) <= 7:
            is_valid_frame = False
        else:
            for index in range(len(predicted_heroes)):
                try:
                    framesDB.cursor.execute(
                        """
                        INSERT INTO yt_extracted_heroes (yt_id, num, hero_id)
                        VALUES (?,?,?);""",
                        (
                            frame_data.vid_entry["id"],
                            index,
                            ids[predicted_heroes[index].lower()],
                        ),
                    )
                except sqlite3.IntegrityError:
                    pass
            is_valid_frame = True

        print("inserting file", frame_data.vid_entry["id"])
        framesDB.insert_frame_file(
            frame_data.frame_image,
            frame_data.vid_entry["id"],
            frame_num=frame_data.frame_num,
            is_valid=is_valid_frame,
        )
        framesDB.commit()


framesDB.close()

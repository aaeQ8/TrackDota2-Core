from datetime import datetime
from collections import defaultdict
import os
import json
import sqlite3
import uuid
import cv2
import numpy as np
import time
import string


class _FrameFiles:
    def __init__(self, frame_files_dir):

        self.frame_files_dir = frame_files_dir

    def write_frame(self, frame_img, file_name):

        path = os.path.join(self.frame_files_dir, file_name)
        if not os.path.exists(path):
            cv2.imwrite(path, frame_img)
            # frame_img.save(path, 'png')

    def delete_frame(self, frame_name):

        path = os.path.join(self.frame_files_dir, frame_name)
        if os.path.exists(path):
            os.remove(path)


class FramesDB:
    def __init__(self, DB_connection, frames_dir="dota_frames_dir"):

        self._connection = DB_connection
        self.frames_dir = frames_dir
        self._cursor = DB_connection.cursor()
        if not os.path.exists(frames_dir):
            os.mkdir(frames_dir)
        self.frame_files = _FrameFiles(self.frames_dir)

    def commit(self):
        self._connection.commit()

    def execute(self, query, parms=[]):
        if parms == []:
            self._cursor.execute(query)
        else:
            self._cursor.execute(query, parms)

    @property
    def cursor(self):
        return self._cursor

    def close(self):
        self._connection.close()

    def insert_frame_file(
        self,
        frame_image,
        yt_id,
        frame_num=-1,
        is_valid="UNKNOWN",
        file_ext=".png",
        is_deleted="False",
    ):

        frame_name = str(uuid.uuid4()) + file_ext
        print(frame_name)
        full_path = os.path.abspath(os.path.join(self.frames_dir, frame_name))

        self._cursor.execute(
            """
          INSERT INTO yt_frame_files (file_name, yt_id, frame_num, full_path, is_valid, is_deleted)
          VALUES (?,?,?,?,?,?)""",
            (frame_name, yt_id, frame_num, full_path, is_valid, is_deleted),
        )

        self.frame_files.write_frame(frame_image, frame_name)

    def create_tables(self):

        self._cursor.execute(
            """
            CREATE TABLE if not exists yt_vids
               ( yt_id text UNIQUE NOT NULL PRIMARY KEY 
               , primary_player text
               , is_highlight text
               , title text
               , duration Integer
               , upload_date text
               )"""
        )

        self._cursor.execute(
            """
            CREATE TABLE if not exists yt_frame_files
               ( file_name text UNIQUE NOT NULL PRIMARY KEY
               , yt_id text
               , frame_num INTEGER
               , full_path text
               , is_valid text
               , is_deleted text
               , FOREIGN KEY(yt_id) REFERENCES yt_vids(yt_id))"""
        )

        self._cursor.execute(
            """
            CREATE TABLE if not exists yt_extracted_heroes
               (yt_id text
               , num INTEGER CHECK(num <10 AND num >= 0)
               , hero_id INTEGER
               , PRIMARY KEY(yt_id, num)
               , FOREIGN KEY(yt_id) REFERENCES yt_frame_files(yt_id)
               , FOREIGN KEY(hero_id) REFERENCES heroes(hero_id));"""
        )

        self._cursor.execute(
            """
            CREATE TABLE if not exists yt_players
               (yt_id TEXT, player_name TEXT
               , PRIMARY KEY(yt_id, player_name)
               , FOREIGN KEY(yt_id) REFERENCES yt_frame_files(yt_id));"""
        )

        self._cursor.execute(
            """
            CREATE TABLE if not exists matches
               (match_id TEXT PRIMARY KEY UNIQUE NOT NULL
               , average_mmr INTEGER
               , activate_time_id TEXT UNIQUE
               , activate_time TEXT
               , rad_score TEXT
               , dire_score TEXT
               , spectators_count INTEGER
               , uploaded TEXT
               , winner TEXT
               , duration INTEGER
               , complete TEXT)"""
        )

        self._cursor.execute(
            """
            CREATE TABLE if not exists matches_heroes
               (match_id TEXT
               , num INTEGER CHECK(num < 10 AND num >= 0)
               , hero_id INTEGER
               , player_name TEXT
               , player_id INTEGER
               , is_pro TEXT
               , kills INTEGER
               , deaths INTEGER
               , assists INTEGER
               , PRIMARY KEY(match_id, num)
               , FOREIGN KEY(match_id) REFERENCES matches(match_id)
               , FOREIGN KEY(hero_id) REFERENCES heroes(hero_id));"""
        )

        self._cursor.execute(
            """
            CREATE TABLE if not exists matches_items
               (match_id TEXT
               , num INTEGER CHECK(num < 10 AND num >= 0)
               , hero_id INTEGER
               , item INTEGER
               , PRIMARY KEY(match_id, num, hero_id)
               , FOREIGN KEY(match_id) REFERENCES matches(match_id))"""
        )

        self._cursor.execute(
            """
            CREATE TABLE if not exists matches_links
            (match_id TEXT
            , yt_id TEXT
            , is_valid TEXT
            , uploaded TEXT
            , PRIMARY KEY(match_id, yt_id)
            , FOREIGN KEY(match_id) REFERENCES matches(match_id)
            , FOREIGN KEY(yt_id) REFERENCES yt_vids(yt_id));"""
        )

        self._cursor.execute(
            """
            CREATE TABLE if not exists players
            (player_id INTEGER
            , player_name TEXT UNIQUE
            , team TEXT
            , is_primary_name TEXT
            , PRIMARY KEY(player_id, player_name));"""
        )
        
        self._cursor.execute("""
            CREATE TABLE if not exists heroes
            (hero_id INTEGER
            , hero_name TEXT
            , PRIMARY KEY(hero_id));""")

    def insert_heroes(self, json_file):
        with open(json_file, 'r') as f:
            heroes = json.load(f)

        for hero in heroes:
            try:
                self._cursor.execute("""INSERT INTO heroes(hero_id, hero_name) VALUES (?,?);"""
                    , (hero['id'], hero['localized_name']))
                self.commit()
            except sqlite3.IntegrityError:
                pass

    def extract_titles(self, ignore_extracted):
        if ignore_extracted:
            self._cursor.execute(
                """
                SELECT yt.yt_id, yt.title 
                FROM yt_vids yt
                WHERE NOT EXISTS (SELECT 1 from yt_players yp WHERE yp.yt_id == yt.yt_id);"""
            )
        elif ignore_extracted is False:
            self._cursor.execute(
                """
                SELECT yt.yt_id, yt.title 
                FROM yt_vids yt;"""
            )
        titles = self._cursor.fetchall()
        self._cursor.execute("SELECT p.player_id, p.player_name FROM players p;")
        players = self._cursor.fetchall()
        for yt_title_row in titles:
            player_found = "__UNIDENTIFIED__"
            for p_entry in players:
                if find_substring(
                    p_entry[1].lower(), yt_title_row[1].replace(".", " ").lower()
                ):
                    player_found = p_entry[1]
                    try:
                        self._cursor.execute(
                            """
                            INSERT INTO yt_players(yt_id, player_name) 
                            VALUES (?,?); """,
                            (yt_title_row[0], player_found),
                        )
                    except sqlite3.IntegrityError:
                        pass
            self.commit()
            if player_found == "__UNIDENTIFIED__":
                pass

    def update_is_deleted(self):

        self._cursor.execute(
            """SELECT file_name, full_path 
                FROM yt_frame_files 
                WHERE is_deleted = False;"""
        )
        for row in self._cursor.fetchall():
            if os.path.exists(row[1]) is False:
                self._cursor.execute(
                    """
                    UPDATE yt_frame_files 
                    SET is_deleted = True 
                    WHERE file_name = ?;""",
                    (row[0],),
                )
                self.commit()

    def update_activate_time_id(self):
        self._cursor.execute(
            """
            SELECT match_id, activate_time, activate_time_id 
            FROM matches WHERE activate_time_id is NULL;"""
        )
        all_matches = self._cursor.fetchall()
        for match in all_matches:
            if match[2] is None:
                self._cursor.execute(
                    """
                    SELECT match_id, activate_time, activate_time_id 
                    FROM matches 
                    WHERE activate_time == ?;""",
                    (match[1],),
                )
                matches = self._cursor.fetchall()
                index = 0
                for match_to_update in matches:
                    activate_time_id = datetime.utcfromtimestamp(
                        int(match_to_update[1])
                    ).strftime("%Y-%m-%dT%H:%M:%S:") + str(index).zfill(3)
                    print(activate_time_id)
                    self._cursor.execute(
                        """
                        UPDATE matches 
                        SET activate_time_id = ? 
                        WHERE match_id == ?;""",
                        (activate_time_id, match_to_update[0]),
                    )
                    index += 1
        self.commit()

    def insert_live_games(self, json_data):

        for entry in json_data:
            try:
                self.cursor.execute(
                    """INSERT INTO matches
                    (match_id, average_mmr, activate_time) VALUES (?,?,?);""",
                    (entry["match_id"], entry["average_mmr"], entry["activate_time"]),
                )
            except sqlite3.IntegrityError:
                pass
            try:
                for num, player in enumerate(entry["players"]):
                    self.cursor.execute(
                        """INSERT INTO matches_heroes 
                        (match_id, num, hero_id, player_name, player_id, is_pro) 
                        VALUES (?,?,?,?,?,?);""",
                        (
                            entry["match_id"],
                            num,
                            player["hero_id"],
                            player.get("name", "None"),
                            player["account_id"],
                            player.get("is_pro", "False"),
                        ),
                    )

            except sqlite3.IntegrityError:
                pass

    def get_images(self, is_valid, ignore_extracted):

        if ignore_extracted is False:
            self._cursor.execute(
                """
                SELECT file_name, full_path, is_valid, is_deleted, yt_id 
                FROM yt_frame_files
                WHERE is_valid == ? AND is_deleted != True""",
                (is_valid,),
            )
        elif ignore_extracted is True:
            self._cursor.execute(
                """
                SELECT yt_f.file_name, yt_f.full_path, yt_f.is_valid, yt_f.is_deleted, yt_f.yt_id
                FROM yt_frame_files yt_f
                WHERE yt_f.is_valid == ? AND yt_f.is_deleted != True 
                AND NOT EXISTS (SELECT 1 FROM yt_extracted_heroes yt_h WHERE yt_h.yt_id == yt_f.yt_id);""",
                (is_valid,),
            )

        frame_files = self._cursor.fetchall()
        return frame_files

    def link_matches(self):

        self._cursor.execute(
            """
            SELECT player_id
            FROM players 
            GROUP BY player_id;"""
        )
        players_ids_query = self._cursor.fetchall()
        players_ids = set(x[0] for x in players_ids_query)
        for player_id in players_ids:
            self._cursor.execute(
                """
                SELECT player_name
                FROM players
                WHERE player_id = ?;""",
                (player_id,),
            )
            player_names_query = self._cursor.fetchall()
            player_names = set(x[0] for x in player_names_query)
            yt_frames_to_check = set()
            for name in player_names:
                self._cursor.execute(
                    """
                    SELECT yt_id FROM yt_players
                    WHERE player_name == ? COLLATE NOCASE
                    GROUP BY yt_id;""",
                    (name,),
                )
                for row in self._cursor.fetchall():
                    yt_frames_to_check.add(row[0])
            self._cursor.execute(
                """
                SELECT match_id 
                FROM matches_heroes 
                WHERE player_id == ?;""",
                (player_id,),
            )
            matches_to_check = set(row[0] for row in self._cursor.fetchall())
            for match_id in matches_to_check:
                self._cursor.execute(
                    """
                    SELECT match_id, num, hero_id, player_name, player_id
                    FROM matches_heroes 
                    WHERE match_id == ?
                    ORDER BY num ASC;""",
                    (match_id,),
                )
                match_entry = self._cursor.fetchall()
                match_heroes = [int(x[2]) for x in match_entry]
                for yt_id in yt_frames_to_check:
                    self._cursor.execute(
                        """
                        SELECT yh.yt_id, h.hero_name, yh.num, yh.hero_id
                        FROM yt_extracted_heroes yh 
                        JOIN heroes h on (yh.hero_id=h.hero_id)
                        WHERE yh.yt_id == ?
                        ORDER BY num ASC""",
                        (yt_id,),
                    )
                    extracted_heroes = [
                        int(x[3]) for x in self._cursor.fetchall()
                    ]
                    try:
                        if distance(match_heroes, extracted_heroes) >= 5:
                            try:
                                self._cursor.execute(
                                    """
                                    INSERT INTO matches_links (match_id, yt_id)
                                    VALUES (?,?);""",
                                    (match_id, yt_id),
                                )
                                self.commit()
                            except sqlite3.IntegrityError:
                                pass
                    except IndexError as e:
                        pass
                    # print(e)

    def add_names_from_matches(self):
        self._cursor.execute(
            """
            SELECT player_id, player_name 
            FROM matches_heroes 
            WHERE is_pro == True 
            GROUP BY player_id, player_name;"""
        )
        players = self._cursor.fetchall()
        for row in players:
            try:
                self._cursor.execute(
                    "INSERT INTO players(player_id, player_name) VALUES (?,?)",
                    (row[0], row[1]),
                )
                self.commit()
            except sqlite3.IntegrityError as e:
                pass

    def update_match_details(self, match_id, new_details):
        self._cursor.execute(
            """
            UPDATE matches SET duration = ?, winner = ?, rad_score = ?, dire_score = ?
            WHERE match_id = ?;""",
            (
                new_details.duration,
                new_details.winner,
                new_details.radiant_score,
                new_details.dire_score,
                match_id,
            ),
        )
        self._insert_player_details(match_id, new_details.player_details)
        self.cursor.execute(
            """
            UPDATE matches 
            SET complete = True 
            WHERE match_id = ?;""",
            (match_id,),
        )
        self.commit()

    def _insert_player_details(self, match_id, player_details):

        for dic in player_details:
            self.cursor.execute(
                """
                UPDATE matches_heroes 
                SET kills = ?, deaths = ?, assists = ?
                WHERE match_id = ? AND hero_id = ?""",
                (dic["kills"], dic["deaths"], dic["assists"], match_id, dic["hero_id"]),
            )
            for num, item in enumerate(dic["items"]):
                try:
                    self._cursor.execute(
                        """
                        INSERT INTO matches_items (match_id, num, hero_id, item)
                        VALUES (?,?,?, ?);""",
                        (match_id, num, dic["hero_id"], item),
                    )
                except sqlite3.IntegrityError:
                    pass

    def get_matches_to_upload(self):
        self._cursor.execute(
            """
            SELECT match_id, average_mmr, activate_time, rad_score, dire_score
                , activate_time_id, duration, winner
            FROM matches
            WHERE uploaded IS NULL AND complete IS NOT NULL
            ORDER BY activate_time DESC;
            """
        )
        matches_to_upload = self._cursor.fetchall()
        for match_entry in matches_to_upload:
            players_list = []
            self._cursor.execute(
                """
                SELECT mh.player_id, mh.player_name, mh.hero_id, mh.num, mh.is_pro, h.hero_name
                FROM matches_heroes mh JOIN heroes h ON (h.hero_id=mh.hero_id)
                WHERE mh.match_id == ?
                ORDER BY num ASC""",
                (match_entry[0],),
            )
            players_query = self._cursor.fetchall()
            if len(players_query) != 10:
                continue
            players_list = []
            for row in players_query:
                self._cursor.execute(
                    """
                    SELECT t.item
                    FROM matches_items t JOIN matches_heroes h ON h.hero_id = t.hero_id 
                    WHERE t.match_id = ? AND h.match_id = t.match_id AND h.player_id = ? 
                    ORDER BY t.hero_id;""",
                    (match_entry[0], row[0]),
                )
                player_items = [x[0] for x in self._cursor.fetchall()]
                self._cursor.execute(
                    """
                    SELECT kills, deaths, assists
                    FROM matches_heroes 
                    WHERE match_id = ? AND hero_id = ?;""",
                    (match_entry[0], row[2]),
                )
                stats_query = self._cursor.fetchone()
                stats_dic = {
                    "kills": stats_query[0],
                    "deaths": stats_query[1],
                    "assists": stats_query[2],
                }
                if int(row[2]) == 0:
                    continue
                player_name_dic = {
                    "player_id": row[0],
                    "player_name": row[1],
                    "hero_id": row[2],
                    "hero_name": row[5],
                    "is_pro": row[4],
                }
                players_list.append(
                    {
                        "stats": stats_dic,
                        "items": player_items,
                        "player_details": player_name_dic,
                    }
                )
            date = datetime.utcfromtimestamp(int(match_entry[2])).strftime("%Y-%m-%d")
            temp_entry = {
                "date": date,
                "activate_time_id": match_entry[5],
                "activate_time": int(match_entry[2]),
                "matchid": match_entry[0],
                "average_mmr": match_entry[1],
                "rad_score": match_entry[3],
                "dire_score": match_entry[4],
                "duration": match_entry[6],
                "winner": match_entry[7],
                "players": players_list,
            }
            yield temp_entry


def filter_name(name):
    replacements = {
        "-": "",
        "0": "o",
        "!": "",
        "^": "",
        "_": " ",
        "1": "l",
        "`": "",
        "♥": "",
        "！": "",
    }
    for letter in replacements:
        name = name.replace(letter, replacements[letter])

    return name.lower()


def find_substring(needle, haystack):
    index = haystack.find(needle)
    if index == -1:
        return False
    if index != 0 and haystack[index - 1] not in string.whitespace:
        return False
    L = index + len(needle)
    if L < len(haystack) and haystack[L] not in string.whitespace:
        return False
    return True


def distance(labels1, labels2):
    similarity = 0
    for index in range(10):
        if labels1[index] == labels2[index]:
            similarity += 1
    return similarity

from collections import defaultdict
import cv2
import youtube_dl
from collections import namedtuple
import requests
import json


class FetchMatchDetails:
    def __init__(self, api_key=None):
        self.api_link = "https://api.opendota.com/api/matches"
        if api_key:
            self.api_key = "?api_key=" + api_key
        else:
            self.api_key = ""

    def fetch_match_details(self, match_id):
        r = requests.get(self.api_link + "/" + str(match_id) + self.api_key)
        data = r.json()
        try:
            duration = data["duration"]
            if data["radiant_win"]:
                winner = "radiant"
            else:
                winner = "dire"
            dire_score = data["dire_score"]
            radiant_score = data["radiant_score"]
            player_details = []
            for player in data["players"]:
                player_items = []
                for i in range(6):
                    player_items.append(player["item_{}".format(i)])
                for i in range(3):
                    player_items.append(player["backpack_{}".format(i)])
                player_items.append(player["item_neutral"])
                player_dic = {
                    "items": player_items,
                    "hero_id": player["hero_id"],
                    "kills": player["kills"],
                    "deaths": player["deaths"],
                    "assists": player["assists"],
                }
                player_details.append(player_dic)
            match_details = namedtuple(
                "match_details",
                ["duration", "winner", "radiant_score", "dire_score", "player_details"],
            )
            return match_details(
                duration, winner, radiant_score, dire_score, player_details
            )
        except KeyError:
            return None


class YtFramesFetcher:
    def __init__(
        self,
        channels=[
            "https://www.youtube.com/c/TopDotaTV/videos",
            "https://www.youtube.com/c/Dota2Pro/videos",
            "https://www.youtube.com/c/DotaPub/videos",
            "https://www.youtube.com/c/DotaPersona/videos",
            "https://www.youtube.com/c/Dota2HighSchool/videos",
            "https://www.youtube.com/c/JustWanPlayAGameBro/videos",
            "https://www.youtube.com/c/dotatvru/videos",
            "https://www.youtube.com/c/beckkkj/videos",
            "https://www.youtube.com/channel/UCiR9IHCurqVHpC821NVcW6g/videos",
            "https://www.youtube.com/c/SpotnetDota2/videos",
            "https://www.youtube.com/c/Dota2DivineRapier/videos",
        ],
        initial_frame_num=3000,
        skip_frame=3000,
        num_of_frames=3,
        skip_valid=False,
        vid_format="1080p60",
        ydl_opts={"playliststart": 1, "skip_download": True, "playlistend": 1},
    ):

        self.channels = channels
        self.initial_frame_num = initial_frame_num
        self.skip_frame = skip_frame
        self.num_of_frames = num_of_frames
        self.skip_valid = skip_valid
        self.vid_format = vid_format
        self.ydl_opts = ydl_opts

    def fetch_frames(self, cursor=None):

        ydl = youtube_dl.YoutubeDL(self.ydl_opts)
        for channel in self.channels:
            try:
                info_dict = ydl.extract_info(channel, download=False)
            except youtube_dl.utils.DownloadError:
                continue
            for vid_entry in info_dict.get("entries"):
                print("in loop:", vid_entry["id"])
                if vid_entry["is_live"]:
                    print(vid_entry["is_live"], vid_entry["id"])
                    continue
                if cursor is not None and self.skip_valid:
                    if has_valid_frame(vid_entry["id"], cursor):
                        print("skipping frame cuz valid found", vid_entry["id"])
                        continue
                for format_ in vid_entry.get("formats", None):
                    if format_.get("format_note", None) == self.vid_format:
                        next_frame = self._get_next_frame(vid_entry["id"], cursor)
                        entry_url = format_.get("url", None)
                        for _ in range(self.num_of_frames):
                            print("capturing frames", next_frame)
                            frame_image = capture_frame(entry_url, next_frame)
                            if frame_image is None:
                                continue
                            if len(frame_image) >= 1:
                                frame_entry = namedtuple(
                                    "frame_entry",
                                    ["vid_entry", "frame_image", "frame_num"],
                                )
                                yield frame_entry(vid_entry, frame_image, next_frame)
                                next_frame += self.skip_frame
                        break

    def _get_next_frame(self, fetched_id, cursor=None):

        if cursor:
            cursor.execute(
                """SELECT MAX(frame_num) from yt_frame_files 
                                WHERE yt_id == ? GROUP BY yt_id AND frame_num != -1;""",
                (fetched_id,),
            )
            max_frame_query = cursor.fetchone()

            if max_frame_query:
                next_frame = max_frame_query[0] + self.skip_frame
                print("next_frame", next_frame)
                return next_frame

        return self.initial_frame_num


def has_valid_frame(fetched_id, cursor):
    cursor.execute(
        """SELECT is_valid from yt_frame_files
                        WHERE yt_id == ?;""",
        (fetched_id,),
    )
    all_found = [bool(int(row[0])) for row in cursor.fetchall()]
    print(all_found)
    if True in all_found:
        return True
    else:
        return False


def capture_frame(vid_url, frame_to_capture=8000):
    try:
        print("frame to cap:", frame_to_capture)
        cap = cv2.VideoCapture(vid_url)
        cap.set(1, frame_to_capture)
        ret, frame = cap.read()
        if not ret:
            return None
        if cv2.waitKey(30) & 0xFF == ord("q"):
            return None
        cap.release()
        return frame

    except cv2.error as e:
        print("error", e)
        cap.release()
        return []

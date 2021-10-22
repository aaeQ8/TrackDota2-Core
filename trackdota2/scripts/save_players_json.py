from frames_classes import FramesDB
import numpy as np
import sqlite3
import os
import boto3
import json
from bs4 import BeautifulSoup
import requests


player_info = {}


def add_player_info(soup):
    links = soup.find_all("td", {"class": "plainlinks"})
    for link in links:
        twitch_link = "none"
        player_id = "none"
        for a_element in link.find_all("a"):
            url = a_element["href"]
            if "dotabuff" in url:
                player_id = int(url[url.rfind("/") + 1 :])
            if "twitch" in url:
                twitch_link = url
        if player_id != "none":
            player_info[player_id] = twitch_link


con = sqlite3.connect("asdasd")
framesDB = FramesDB(con)

framesDB.cursor.execute(
    """SELECT player_id, player_name 
	from matches_heroes 
	where is_pro = True 
	group by player_id;"""
)

players = framesDB.cursor.fetchall()
links_to_scrap = [
    "https://liquipedia.net/dota2/Portal:Players/Europe",
    "https://liquipedia.net/dota2/Portal:Players/China",
    "https://liquipedia.net/dota2/Portal:Players/Americas",
    "https://liquipedia.net/dota2/Portal:Players/Southeast_Asia",
]

for link in links_to_scrap:
    r = requests.get(link)
    soup = BeautifulSoup(r.content, "html.parser")
    add_player_info(soup)

# print(player_info)


lst = []


for player in players:
    print(player)
    framesDB.cursor.execute(
        """
		SELECT hero_id, count(hero_id) 
		FROM matches_heroes 
		WHERE player_id = ? 
		GROUP BY hero_id 
		ORDER BY count(hero_id) DESC;""",
        (player[0],),
    )

    popular_heroes = [x[0] for x in framesDB.cursor.fetchall()]
    if len(popular_heroes) >= 5:
        sig_heroes = popular_heroes[:5]
    else:
        sig_heroes = popular_heroes[:]

    if player[0] in player_info:
        twitch_link = player_info[player[0]]
    else:
        twitch_link = "none"

    dic = {
        "player_id": player[0],
        "player_name": player[1],
        "sig_heroes": sig_heroes,
        "region": "unknown",
        "twitch_link": twitch_link,
    }
    lst.append(dic)

with open("players_list.json", "w") as f:
    json.dump(lst, f)

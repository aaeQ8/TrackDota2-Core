import requests
import json
from bs4 import BeautifulSoup


r = requests.get(
    "https://dota2.fandom.com/wiki/Category:Item_icons?filefrom=Vanguard+icon.png#mw-category-media"
)
soup = BeautifulSoup(r.text)


for element in soup.find_all("li", {"class": "gallerybox"}):
    name = element.find("div", {"class": "gallerytext"})
    name = str(name.a["title"].split(":")[1].split(".")[0])
    img_link = element.a["href"]
    img_data = requests.get(img_link).content
    with open("items_icons/" + name, "wb") as f:
        f.write(img_data)

from bs4 import BeautifulSoup
import requests

r = requests.get("https://dota2.fandom.com/wiki/Category:Hero_icons")

soup = BeautifulSoup(r.text)


for element in soup.find_all("li", {"class": "gallerybox"}):
    name = element.img["alt"].split("icon")[0].strip()
    img_link = element.a.img["src"]

    print(name, img_link)

    img_data = requests.get(img_link).content
    with open("labeled_icons/" + name, "wb") as f:
        f.write(img_data)

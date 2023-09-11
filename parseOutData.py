import json

path = "out/scrape/https:@@www.poewiki.net/data.json"

# make python dict that has same root keys as json file
dct = {
    "stored_requests": {},
    "stored_soups": {},
    "stored_jsons": {},
    "stored_texts": {},
}

with open(path, "r") as file:
    data: dct = json.load(file)

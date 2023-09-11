import mp_gui2
import multiprocessing
import multiprocessing.queues
import time
import requests
import re
import os
import json
import random
from bs4 import BeautifulSoup


if __name__ == "__main__":

    def worker(name: str):
        global gui
        msgs = gui.get_message_queue(name)
        msgs.put("Alive")
        while not gui.is_stopping():
            msgs.put("Looking for work")
            try:
                url = url_work_queue.get(timeout=0.2)
            except multiprocessing.queues.Empty:  # type: ignore
                msgs.put("No work, sleeping")
                time.sleep(1)
                continue

            search_url = f"https://gbf.wiki{url}"

            msgs.put(search_url)
            response1 = requests.get(search_url)
            soup1 = BeautifulSoup(response1.text, features="lxml")

            wikitable = soup1.find("div", {"title": "Stats"})
            if not wikitable:
                print("NO WIKITABLE", url)
                time.sleep(1)
                msgs.put(f"Error {url} -> wikitable missing")
                continue

            msgs.put(f"{url} -> re")
            tags = ""
            for a in wikitable.find_all("a"):  # type: ignore
                try:
                    match = re.match(r"/weapon_lists/\w{1,20}/(\w+)", a["href"].lower())
                except KeyError as e:
                    print("KEY ERROR", e)
                    time.sleep(2)
                    msgs.put(f"Error {url} -> re -> keyerror")
                    continue
                if match:
                    tag = match.group(1)
                    tags += "_" + tag

            msgs.put(f"{url} -> re -> img")
            response3 = requests.get(f"https://gbf.wiki/File:{url[1:]}.png")
            soup3 = BeautifulSoup(response3.text, features="lxml")

            imgs1 = soup3.find_all("img", {"width": 640})

            if not imgs1:
                msgs.put(f"Error {url} -> re -> img -> missing")
                print("IMAGE MISSING", url)
                time.sleep(2)
                continue
            if len(imgs1) > 1:
                msgs.put(f"Error {url} -> re -> img -> too many")
                print("TOO MANY IMAGES", url)
                time.sleep(2)
                continue

            img1_src = imgs1[0]["src"]

            second_look_url = base_url + img1_src

            response2 = requests.get(second_look_url)
            response2.raise_for_status()

            msgs.put(f"{search_url} -> re -> img -> save")
            single_quote = "'"
            local_path = f"{img_out}{url[1:].replace('%27', single_quote)}{tags}.png"
            with open(local_path, "wb") as file:
                file.write(response2.content)

            with lock:
                counter.value += 1

    with multiprocessing.Manager() as manager:
        gui = mp_gui2.GUI(manager, "Example Worker GUI")
        url_work_queue = manager.Queue()
        queue_show = manager.Value("s", "")
        gui.easy_track(queue_show)
        lock = manager.Lock()
        counter = manager.Value("i", 0)
        counter_show = manager.Value("s", "")
        gui.easy_track(counter_show)

        filepath = "out/scrape/gbf_weapons.json"
        base_url = "https://gbf.wiki"
        img_out = "out/scrape/gbf_img2/"

        with open(filepath, "r") as file:
            urls = json.load(file)
            for url in urls:
                url_work_queue.put(url)
            del urls

        for i in range(40):
            gui.add_process(f"P{i}", target=worker, args=())

        gui.title_top_text.value = "^-^\n~xx"
        gui.footer_bottom_text.value = ""
        gui.start()
        while gui.is_running():
            queue_show.value = f"Q:{url_work_queue.qsize():0.0f}"
            counter_show.value = (
                f"C:{counter.value:0.0f}({counter.value/gui.get_runtime():0.1f}/s)"
            )
            time.sleep(1 / 30)

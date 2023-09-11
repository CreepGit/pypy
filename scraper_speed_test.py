import json
import re
import threading
import time
import random
import requests
import multiprocessing
from typing import Any
import tkinter as tk
from bs4 import BeautifulSoup
from urllib import parse

scraper_data_path_read_only = r"out/scrape/https:@@www.poewiki.net/data.json"

with open(scraper_data_path_read_only, "r") as file:
    data = json.load(file)


def point_score(link: str):
    # Large number = First
    score = 10_000
    score -= len(link) * 100
    if re.fullmatch(r"[\w\/\.\-]+", link):
        # Only normal stuff in link
        score *= 2
    if link.count("%") > 1:
        score *= 0.333

    for bad_word in (
        "edit",
        "info",
        "history",
        ".",
        ":",
        "#",
    ):
        if bad_word in link:
            score *= 0.333
    return int(score)


links = list(
    filter(lambda x: point_score(x.split(".net")[-1]) > 15000, data["stored_requests"])
)


_start_time = time.time()


def get_run_time():
    return time.time() - _start_time


# def worker(i: int, shared_num):
#     print("Starting",i)
#     try:
#         while state.running:
#             link = random.choice(links)
#             resp = requests.get(link)
#             shared_num.value += 1
#             with open(f"out/scrape/random/file{shared_num.value}.html", "w") as file:
#                 file.write(resp.text)
#     except KeyboardInterrupt:
#         pass
#     print(f"Stopping thread {i}")

# # mp_state = multiprocessing.Value("I", state)
# mp_num: Any = multiprocessing.Value("I", 0)
# for i in range(200):
#     # threading.Thread(target=worker, args=(i, )).start()
#     multiprocessing.Process(target=worker, args=(i, mp_num)).start()


# try:
#     while True:
#         time.sleep(0.1)
#         print(mp_num.value, f"{mp_num.value/get_run_time():4.1f}", f"{get_run_time():4.0f}")
# except KeyboardInterrupt:
#     print("Interrupted")
#     state.running = False

window = tk.Tk()
window.geometry("350x400")

label = tk.Label(text="Text", anchor="w", width=42)
label.grid(row=0, column=0, columnspan=2)

# ParseResult(scheme='https', netloc='www.poewiki.net', path='/wiki/Link_skill', params='', query='', fragment='')


class state:
    running = multiprocessing.Value("b", True)


def work(n: int, running):
    print("Spawned", n)

    def scour_link(link):
        nonlocal my_links
        parsed_link = parse.urlparse(link)
        try:
            resp = requests.get(link, timeout=3)
        except Exception:
            return
        soup = BeautifulSoup(resp.text, features="lxml")
        a_tags = soup.find_all("a")
        for a in a_tags:
            if src := a.get("href"):
                parsed_src = parse.urlparse(src)
                if parsed_src.scheme not in ("http", "https"):
                    continue
                my_links.add(
                    f"{parsed_src.scheme or parsed_link.scheme}://{parsed_src.netloc or parsed_link.netloc}{parsed_src.path}"
                )
        messages[n] = f"{link} {len(a_tags)}"
        val.value += 1

    my_links = set()
    try:
        while running.value:
            if my_links:
                pick = random.choice(list(my_links))
                my_links.remove(pick)
                scour_link(pick)
            else:
                scour_link(random.choice(links))
    except Exception as e:
        messages[n] = f"DIED {e}"
        raise e
    print("Killing", n)


labels = {}
message_labels = {}
process_count = 40
for i in range(process_count):
    labels[i] = tk.Label(text=f"P{i}")
    labels[i].grid(row=10 + i)
    message_labels[i] = tk.Label(text="msg", anchor="w", width=40)
    message_labels[i].grid(row=10 + i, column=1)


def draw_loop():
    label.configure(text=f"Text {val.value:4d} {val.value/get_run_time():4.1f}/s {get_run_time():0.0f}s {state.running.value}")  # type: ignore
    for i, m in messages.items():
        message_labels[i].configure(text=m)
    window.after(100, draw_loop)


def gui_process():
    print("Starting gui process")
    window.after(100, draw_loop)
    window.mainloop()
    print("Gui closed")
    state.running.value = False  # type: ignore


with multiprocessing.Manager() as manager:
    messages = manager.dict({i: "" for i in range(process_count)})
    val = manager.Value("i", 0)

    gui = multiprocessing.Process(target=gui_process, args=())
    gui.start()

    workers = []
    for i in range(process_count):
        worker = multiprocessing.Process(
            target=work,
            args=(i, state.running),
        )
        worker.start()
        workers.append(worker)

    gui.join()
    for worker in workers:
        worker.join()

print("App closed")

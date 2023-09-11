from bs4 import BeautifulSoup, element
import requests
import json
import time
import re
import base64
import shutil
import threading
import os, psutil

# CONFIG

starting_url = "https://www.poewiki.net/wiki/List_of_unique_body_armours"
base_url = "https://www.poewiki.net"


def main():
    global stored_requests, links, image_links, visited
    load()  # Never remove, warning: data loss
    # format_html_page_with_all_images()
    count_stored_requests_as_visited()
    mega_crawl(starting_url, skip_errors=True)
    print("DONE")


# CODE

stored_requests_path = "out/scrape/stored_requests/"
stored_requests_file = "out/scrape/stored_requests.json"


def save():
    global stored_requests, links, image_links, errored_on_link
    save_obj = {}
    save_obj["stored_requests"] = list(stored_requests)
    save_obj["image_links"] = list(image_links)
    save_obj["links"] = list(links)
    save_obj["errored_on_link"] = list(set(errored_on_link))
    with open(stored_requests_file, "w") as file:
        json.dump(save_obj, file, indent=2)


def load():
    global stored_requests, links, image_links, errored_on_link
    try:
        with open(stored_requests_file) as file:
            save_obj = json.load(file)
        links = set(save_obj["links"])
        image_links = set(save_obj["image_links"])
        stored_requests = set(save_obj["stored_requests"])
        errored_on_link = save_obj.get("errored_on_link", [])
    except FileNotFoundError:
        stored_requests = set()
        links = set()
        image_links = set()
        errored_on_link = []


def stored_request(url: str) -> str:
    url_as_filename = url.replace("/", "@") + ".html"

    if url not in stored_requests:
        print(f"INTERNET: {url}")
        res = requests.get(url)
        try:
            res.raise_for_status()
        except requests.HTTPError as e:
            return ""
        except Exception as e:
            print(e)
            input(">")
        stored_requests.add(url)
        with open(stored_requests_path + url_as_filename, "w") as file:
            file.write(res.text)
        return res.text
    else:
        try:
            with open(stored_requests_path + url_as_filename) as file:
                res = file.read()
        except FileNotFoundError:
            stored_requests.remove(url)
            print("Removed", url)
            return stored_request(url)
        return res


process = psutil.Process()


def get_memory_size():
    """In bytes"""
    return process.memory_info().rss


_start_time = time.time()


def get_runtime():
    now_time = time.time()
    delta = now_time - _start_time
    mins = delta // 60
    secs = delta % 60
    return f"{int(mins):1}:{int(secs):02}"


visited = set()


def crawl(url: str):
    global visited, stored_requests, links, image_links
    if url in visited:
        return
    res = stored_request(url)
    if res == "":
        errored_on_link.append(url)
        return  # Skip this one
    soup = BeautifulSoup(res, features="lxml")

    for a in soup.find_all("a"):
        a: element.Tag
        if a.has_attr("href"):
            href: str = a.get("href")  # type: ignore
            if not href.startswith("/"):
                continue
            links.add(a.get("href"))

    for img in soup.find_all("img"):
        img: element.Tag
        if img.has_attr("src"):
            src: str = img.get("src")  # type: ignore
            image_links.add(src)

    visited.add(url)
    # save()


def count_stored_requests_as_visited():
    global visited, stored_requests
    visited = set(stored_requests)


def mega_crawl_link_point_score(link: str):
    # Large number = First
    score = 10_000
    score -= len(link) * 100
    if re.fullmatch(r"[\w\/\.]+", link):
        # Only normal stuff in link
        score *= 2
    if link.count("%") > 1:
        score *= 0.333
    
    for bad_word in ("edit", "info", "history", ".", ":", ):
        if bad_word in link:
            score *= 0.333
    return -score


def mega_crawl(starting_url: str, *, skip_errors=False):
    global visited, stored_requests, links, image_links
    crawl(starting_url)
    try:
        while True:
            print("Counting scores for links")
            links_ordered_filtered = sorted(
                (link for link in links if link not in visited),
                key=lambda e: mega_crawl_link_point_score(e),  # type: ignore
            )
            if skip_errors:
                links_ordered_filtered = [link for link in links_ordered_filtered if link not in errored_on_link]
            if len(links_ordered_filtered) == 0:
                break
            for i, link in enumerate(links_ordered_filtered):
                print(f"Crawling Score:{-mega_crawl_link_point_score(link):6} {link}")
                print(
                    f"{i%1000:3} Mem:{get_memory_size()/1024/1024:5.2f}M vis:{len(visited)} time:{get_runtime()} imgs:{f'{len(image_links)//1000}K' if len(image_links) > 2000 else len(image_links)}"
                )
                crawl(base_url + link)
                if i % 50 == 0:
                    save()
            save()
            print("")
            print("Reshuffling links")
            print("Reshuffling links")
            print("Reshuffling links")
            print("")
            time.sleep(3)
    except KeyboardInterrupt:
        print()
        print("INTERRUPTING, saving")
        save()
    format_html_page_with_all_images()
    print("DONE MEGA CRAWLING")


def format_html_page_with_all_images():
    body = ""

    for src in image_links:
        body += f"<img src='{base_url + src}' loading='lazy'></img>\n<br><span>Source: {base_url + src}</span>\n<br>\n"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
</head>
<body>
    {body}
</body>
</html>"""
    with open("out/scrape/previewhtml.html", "w") as file:
        file.write(html)

    print("HTML FILE GENERATED")


main()

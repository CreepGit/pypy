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

thread_count = 8


def main():
    global stored_requests, links, image_links, visited
    load()  # Never remove, warning: data loss
    # format_html_page_with_all_images()
    count_stored_requests_as_visited()
    # mega_crawl(starting_url, skip_errors=True)
    thread_manager()
    print("DONE")


# CODE

assert not base_url.endswith("/")
base_url_folder = base_url.replace("/", "@")

if not os.path.exists(f"out/scrape/{base_url_folder}"):
    os.mkdir(f"out/scrape/{base_url_folder}")
if not os.path.exists(f"out/scrape/{base_url_folder}/html/"):
    os.mkdir(f"out/scrape/{base_url_folder}/html/")

stored_requests_path = f"out/scrape/{base_url_folder}/html/"
stored_requests_file = f"out/scrape/{base_url_folder}/data.json"


queues = {i: list() for i in range(thread_count)}
thread_infos = {i: dict() for i in range(thread_count)}
reserved = set()
threads_run = True
warnings = []


def thread_loop(number: int, my_list: list, info: dict):
    global threads_run
    done = 0

    try:
        while threads_run:
            if len(my_list) < 1:
                warnings.append(f"Thread {number} needs work!")
                info["message"] = f"L:{len(my_list):2} curr:-/-"
                time.sleep(0.05)
                continue
            url = my_list.pop(0)
            info[
                "message"
            ] = f"L:{len(my_list):2} done:{done:2} curr: {mega_crawl_link_point_score(url):5} {url}"
            crawl(base_url + url)
            done += 1
    except Exception as e:
        threads_run = False
        info["message"] = str(e)
        raise e
    info["message"] = "off"
    print(f"Thread {number} shut down")


def thread_manager():
    global threads_run, reserved, links, visited, internet_search, local_search
    try:
        threads = []
        for i in range(thread_count):
            t = threading.Thread(
                target=thread_loop, args=(i, queues[i], thread_infos[i])
            )
            threads.append(t)
            t.start()
            time.sleep(0.05)

        crawl(starting_url)
        save()
        last_text = ""

        while True:
            links_ordered_filtered = sorted(
                (link for link in set(links) if base_url + link not in visited),
                reverse=True,
                key=lambda e: mega_crawl_link_point_score(e),  # type: ignore
            )
            # Remove errored ons
            links_ordered_filtered = [
                link for link in links_ordered_filtered if link not in errored_on_link
            ]
            # Remove reserved
            links_ordered_filtered = [
                link for link in links_ordered_filtered if link not in reserved
            ]
            if len(links_ordered_filtered) == 0:
                print("This should not happen")
                break

            text = "\n" * 30
            for i in range(thread_count):
                info = thread_infos.get(i, {})
                message = info.get("message", "-")
                text += f"T{i}: {message}\n"

            for i in range(thread_count):
                que: list = queues.get(i)  # type: ignore
                if len(que) <= 30:
                    if len(links_ordered_filtered) > 5:
                        new_items = [links_ordered_filtered.pop(0) for _ in range(5)]
                        for link in new_items:
                            reserved.add(link)
                        que += new_items

            total_count = 0
            for k, v in queues.items():
                total_count += len(v)
            if total_count == 0:
                print("No thread is working")
                break

            open_good = sum(
                (
                    mega_crawl_link_point_score(link) > 10_000
                    for link in links_ordered_filtered
                )
            )
            text += f"Open: {len(links_ordered_filtered)} (10k+:{open_good}) Time:{get_runtime()}\nInternet/Local:{internet_search}/{local_search} {(internet_search+local_search)/(time.time()-_start_time):3.1f}/s MEM:{get_memory_size()/1024/1024:4.2f}M\n"

            if text != last_text:
                print(text)
                last_text = text

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Keyboard Interrupt")
    threads_run = False
    print("Waiting before saving to avoid overlapping..")
    for _ in range(thread_count * 2):
        print(".")
        time.sleep(0.5)
        ok_exit = True
        for t, info in thread_infos.items():
            if info.get("message") != "off":
                ok_exit = False
        if ok_exit:
            print("All threads off")
            break
    else:
        print("TIMED OUT, might be unsafe")
    save()
    print("SAVED")
    format_html_page_with_all_images()


def save():
    global stored_requests, links, image_links, errored_on_link, image_data
    save_obj = {}
    save_obj["stored_requests"] = list(stored_requests)
    save_obj["image_links"] = list(image_links)
    save_obj["links"] = list(links)
    save_obj["errored_on_link"] = list(set(errored_on_link))
    save_obj["image_data"] = image_data
    with open(stored_requests_file, "w") as file:
        json.dump(save_obj, file, indent=2)


def load():
    global stored_requests, links, image_links, errored_on_link, image_data
    try:
        with open(stored_requests_file) as file:
            save_obj = json.load(file)
        links = set(save_obj["links"])
        image_links = set(save_obj["image_links"])
        stored_requests = set(save_obj["stored_requests"])
        errored_on_link = save_obj.get("errored_on_link", [])
        image_data = save_obj.get("image_data", {})
    except FileNotFoundError:
        stored_requests = set()
        links = set()
        image_links = set()
        errored_on_link = []
        image_data = {}


internet_search = 0
local_search = 0


def stored_request(url: str) -> str:
    global internet_search, local_search
    url_as_filename = url.replace("/", "@") + ".html"

    if url not in stored_requests:
        internet_search += 1
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
        local_search += 1
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

            data = image_data.get(src)
            if not data:
                image_data[src] = {"found_in": [url]}
            else:
                # TODO change to set
                if url not in data.get("found_in"):
                    data.get("found_in").append(url)


def count_stored_requests_as_visited():
    global visited, stored_requests
    visited = set(stored_requests)


def mega_crawl_link_point_score(link: str):
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


def format_html_page_with_all_images():
    body = ""
    body += f"<p>Count image links={len(image_links)}</p>"

    body += "<input type='text' id='search' placeholder='filter'>"
    body += "<input type='button' value='go' onclick='sortFunction()'><br><br><br>"

    def sort_by_found_in_count(e):
        return len(image_data.get(e, {}).get("found_in", []))

    for src in sorted(image_links, reverse=True, key=sort_by_found_in_count):
        found_in = len(image_data.get(src, {}).get("found_in", []))
        body += f"<div class='img'><img src='{base_url + src}' loading='lazy'></img>\n<br><span>Source (Found In: {found_in}): {base_url + src}</span><br></div>\n\n"

    javascript = """
    
function sortFunction() {
    console.log("Starting search")
    const filter_text = document.getElementById("search").value.toLowerCase()
    console.log("Filtering with '" + filter_text + "'")
    const loop_count = document.body.childElementCount
    for (let i = 1; i < loop_count; i++) {
        try {
            const element = document.body.children[i]
            const src = element.children[0].getAttribute("src").toLowerCase()
            if (i % 1000 == 0) {
                setTimeout(()=>{
                    console.log(i + ' of ' + loop_count)                
                }, 100)
            }
            if (!src.includes(filter_text)) {
                element.style.display = "none"
            } else {
                element.style.display = null
            }
        } catch {
            
        }
    }
    console.log("Search finished")
}
    
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Superscraper Output</title>
</head>
<body>
    {body}
    <script>
    {javascript}
    </script>
</body>
</html>"""
    with open("out/scrape/previewhtml.html", "w") as file:
        file.write(html)

    print("HTML FILE GENERATED: out/scrape/previewhtml.html")


main()

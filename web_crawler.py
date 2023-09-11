import mp_gui2
import multiprocessing
import time
import requests
import re
import os
import json
from bs4 import BeautifulSoup
import urllib.parse
import heapq

#
# Worker:
#  1. Get url from queue
#  2. request
#  3. parse
#  4. worker's new links to queue
#


def worker(name: int):
    print("Starting", name)
    msgs = gui._sub_processes[name].message_queue
    msgs.put("Started")
    while not gui.stop_event.is_set():
        if queue.empty():
            msgs.put("Waiting for work")
            time.sleep(0.1)
            continue
        
        url = queue.get()
        if not url:
            msgs.put("No URL")
            time.sleep(2)
            continue
        msgs.put(f"Fetching {url}")
        
        try:
            resp = requests.get(url, timeout=10)
        except requests.exceptions.Timeout:
            print("TIMEOUT", url)
            errored_queue.put(url)
            continue
        except requests.exceptions.ConnectionError:
            errored_queue.put(url)
            continue
        
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError:
            msgs.put(f"Error {resp.status_code} {url}")
            errored_queue.put(url)
            print("Error", resp.status_code, url)
            continue
        
        # SAVING
        if False:
            msgs.put(f"  Saving {url}")
            parsed = urllib.parse.urlparse(url)
            netname = parsed.netloc.replace(".", "_")
            netpath = parsed.path.replace("/", "_")
            
            dirpath = f"out/scrape/multi/{netname}"
            filepath = f"out/scrape/multi/{netname}/{netpath}.html"
            
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            with open(filepath, "w") as file:
                file.write(resp.text)
            
        msgs.put(f" Parsing {url}")
        soup = BeautifulSoup(resp.text, "html.parser")
        
        hrefs_gen = (a.get("href") for a in soup.find_all("a", href=True) if a.get("href"))
        for href in hrefs_gen:
            href: str
            if href.startswith("/"):
                href = base_url + href
            link = unparse(urllib.parse.urlparse(href))
            dirty_queue.put(link)
            discovered_queue.put(link)
        
        with lock:
            total_done.value += 1
        done_queue.put(url)
        msgs.put(f"    Done {url}")
        
    msgs.put("Stopped")
    print("End", name)


#
# Queue Worker:
#  1. Get url from dirty queue
#  2. Check if already visited
#  3. Keep queue short
#  4. Add to queue
#

def queue_worker(name: str):
    def scoring_function(parsed: urllib.parse.ParseResult) -> float:
        """Negative numbers are rejected, highest score goes first"""
        # scheme='https'
        # netloc='www.poewiki.net'
        # path='/wiki/Path_of_Exile_Wiki'
        # params=''
        # query=''
        # fragment=''
        score = 10_000
        
        if parsed.netloc != "www.poewiki.net":
            return -1
        
        if parsed.scheme != "https":
            return -1
        
        if not parsed.path.startswith("/wiki/"):
            return -1
        
        for kill in ("edit", "history", "watch", "info"):
            if parsed.path.endswith(kill):
                return -1

        for bad, badness in (("Special:", 0.6),("Talk:", 0.2),):
            if bad in parsed.path:
                score *= badness
        
        if re.fullmatch(r"[\w\/]+", parsed.path):
            score *= 2
        
        score -= len(parsed.path) * 10
        
        return score
    
    queued = set()
    done_set = set()
    discovered_set = set()
    errored_set = set()
    url_heap: list[tuple[int, str]] = []
    
    msgs = gui._sub_processes[name].message_queue
    # load json
    msgs.put("Loading previous run")
    try:
        with open("out/scrape/multi/data.json", "r") as file:
            data = json.load(file)
            discovered_set = set(data.get("discovered", []))
            errored_set = set(data.get("errored", []))
            done_set = set(data.get("done", []))
            for url in discovered_set:
                dirty_queue.put(url)
            del data
    except FileNotFoundError:
        dirty_queue.put(start_url)
    
    while not gui.stop_event.is_set():
        
        # Done phase
        added_to_queues_at_once = 0
        msgs.put("Done phase")
        while not done_queue.empty() and added_to_queues_at_once < 1000:
            added_to_queues_at_once += 1
            done_url = done_queue.get_nowait()
            done_set.add(done_url)
        while not discovered_queue.empty() and added_to_queues_at_once < 1000:
            added_to_queues_at_once += 1
            discovered_url = discovered_queue.get_nowait()
            discovered_set.add(discovered_url)
        while not errored_queue.empty() and added_to_queues_at_once < 1000:
            added_to_queues_at_once += 1
            errored_url = errored_queue.get_nowait()
            errored_set.add(errored_url)
            
        # In phase
        msgs.put("In phase")
        in_queue_size = dirty_queue.qsize()
        out_queue_size = queue.qsize()
        
        for _ in range(min(10_000, in_queue_size)):
            url: str = dirty_queue.get_nowait()

            if url in queued:
                continue
            if url in done_set:
                continue
            if url in errored_set:
                continue
            queued.add(url)
            
            # SCORING
            parsed = urllib.parse.urlparse(url)
            score = scoring_function(parsed)
            
            heap_obj = (-score, url)
            heapq.heappush(url_heap, heap_obj) # type: ignore
            
        # Out phase
        msgs.put("Out phase")
        target_out_queue_size = 40
        if out_queue_size < target_out_queue_size and len(url_heap) > 0:
            for _ in range(target_out_queue_size - out_queue_size):
                score, url = heapq.heappop(url_heap) # type: ignore
                queue.put(url)
        
        msgs.put("Crafting title")
        gui.title_top_text.value = f"{in_queue_size:4}->{len(url_heap):4}->{out_queue_size:4} done: {total_done.value:6} ({total_done.value/gui.get_runtime():0.1f}/s)"

        if out_queue_size >= 30 and in_queue_size == 0:
            msgs.put("Resting")
            time.sleep(0.05)


    print("Finishing up pre-save")
    pre_save_counter = 0
    while not done_queue.empty():
        done_url = done_queue.get_nowait()
        done_set.add(done_url)
        pre_save_counter += 1
        if pre_save_counter % 10_000 == 0:
            msgs.put(f"Still finishing up done-queue {pre_save_counter}")
    while not discovered_queue.empty():
        discovered_url = discovered_queue.get_nowait()
        discovered_set.add(discovered_url)
        pre_save_counter += 1
        if pre_save_counter % 10_000 == 0:
            msgs.put(f"Still finishing up discovered-queue {pre_save_counter}")
    while not errored_queue.empty():
        errored_url = errored_queue.get_nowait()
        errored_set.add(errored_url)
        pre_save_counter += 1
        if pre_save_counter % 10_000 == 0:
            msgs.put(f"Still finishing up error-queue {pre_save_counter}")
    print("Saving DONE and DISCOVERED")
    outpath = "out/scrape/multi/data.json"
    with open(outpath, "w") as file:
        json.dump({
            "done": list(done_set), 
            "discovered": list(discovered_set),
            "errored": list(errored_set),
        }, file, indent=2)
    print("End Queue Worker")


def unparse(parsed: urllib.parse.ParseResult):
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))


with multiprocessing.Manager() as manager:
    process_count = 15
    dirty_queue = manager.Queue()
    done_queue = manager.Queue()
    discovered_queue = manager.Queue()
    errored_queue = manager.Queue()
    total_done = manager.Value("i", 0)
    lock = manager.Lock()
    queue = manager.Queue()
    stop_event = manager.Event()
    
    # add path of exile wiki to dirty queue
    start_url = "https://www.poewiki.net/wiki/Path_of_Exile_Wiki"
    base_url = "https://www.poewiki.net"

    gui = mp_gui2.GUI(manager, "poewiki.net crawler")
    
    for i in range(process_count):
        gui.add_process(f"{f'P{i}':>3}", target=worker, args=())

    gui.add_process(f"  Q", target=queue_worker, args=())

    gui.start()

    # END
    gui.join()
    print("END MAIN")

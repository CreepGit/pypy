import mp_gui
import mp_gui2
import multiprocessing
import time
import requests
import re
import os
import json
import random


if __name__ == "__main__":

    def worker(name: str):
        global gui
        msgs = gui.get_message_queue(name)
        while not gui.is_stopping():
            for x in range(random.randint(40, 100), 0, -1):
                msgs.put(f"{x:02}")
                time.sleep(0.03)
                        
            with lock:
                hits.value += 1

    with multiprocessing.Manager() as manager:
        gui = mp_gui2.GUI(manager, "Example Worker GUI")
        
        live_process_count = manager.Value("s", '0 processes')
        gui.easy_track(live_process_count)
        hits = manager.Value("i", 0)
        hits_formatted = manager.Value("s", "")
        gui.easy_track(hits_formatted)
        lock = manager.Lock()

        for i in range(10):
            gui.add_process(f"P{i}", target=worker, args=())

        gui.title_top_text.value = "^-^\n~xx"
        gui.footer_bottom_text.value = ""
        gui.start()
        while gui.is_running():
            live_process_count.value = f"{len(multiprocessing.active_children())} processes"
            hits_formatted.value = f"{hits.value:0.0f} ({hits.value/gui.get_runtime():0.1f}/s)"
            time.sleep(0.1)



# # example with with first mp_gui version
#
# with multiprocessing.Manager() as manager:
#     process_count = 10
#     msgs = manager.dict({i: 0 for i in range(process_count)})
#     displays = manager.list(["Test", None, None, None])
#     stop_event = manager.Event()

#     processes = []
#     for i in range(process_count):
#         process = multiprocessing.Process(target=worker, args=(i,))
#         process.start()
#         processes.append(process)

#     all_pids = [p.pid for p in multiprocessing.active_children()] + [os.getpid()]
#     gui_process = multiprocessing.Process(target=mp_gui.GUI, args=(msgs, stop_event, all_pids, displays))
#     gui_process.start()

#     # END
#     gui_process.join()
#     for process in processes:
#         process.join()
#     print("END")

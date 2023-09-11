import multiprocessing
import random
import time
import tkinter as tk
import psutil
import os


class GUI:
    def __init__(self, messages: dict, stop_event, all_pids) -> None:
        self.window = tk.Tk()
        self.messages = messages
        self.stop_event = stop_event
        self.start_time = time.time()
        self.all_pids = all_pids + [os.getpid()]

        self.python_process = psutil.Process()

        self.labels = {}
        self.top_label = tk.Label(text="~", anchor="w", width=82)
        self.top_label.grid(row=0, columnspan=2)
        for i, v in messages.items():
            row = i + 1
            tk.Label(text=f"P{i}").grid(row=row)
            label = tk.Label(text="~", anchor="w", width=80)
            label.grid(row=row, column=1)
            self.labels[i] = label

        self.window.after(100, self.draw_loop)
        self.window.mainloop()
        print("Gui terminating")
        self.stop_event.set()

    def draw_loop(self):
        if self.stop_event.is_set():
            self.window.destroy()
            return

        self.top_label.configure(
            text=f"{self.get_runtime_pretty()} {self.get_memory_usage()/1024/1024:0.0f}MB"
        )
        for i, msg in self.messages.items():
            label = self.labels.get(i)
            if label:
                label.configure(text=f"{msg}")
            else:
                time.sleep(0.5)
        self.window.after(100, self.draw_loop)

    def get_runtime(self):
        return time.time() - self.start_time

    def get_runtime_pretty(self):
        rt = self.get_runtime()
        minutes = rt // 60
        seconds = rt % 60
        return f"{minutes:02.0f}:{seconds:02.0f}"

    def get_memory_usage(self):
        """In bytes"""
        counter = 0
        for pid in self.all_pids:
            counter += self._get_memory_usage(pid)
        return counter

    def _get_memory_usage(self, pid):
        process = psutil.Process(pid)
        return process.memory_info().rss


def worker(i: int):
    while not stop_event.is_set():
        r_num = random.uniform(0, 100)
        shared_list.append(r_num)
        with lock:
            hit_count.value += 1
        my_work[i] += 1
        time.sleep(random.uniform(0, 0.3))
    print("Done", i)


with multiprocessing.Manager() as manager:
    processes = []
    process_count = 10
    shared_list = manager.list()
    my_work = manager.dict({i: 0 for i in range(process_count)})
    hit_count = manager.Value("i", 0)
    lock = manager.Lock()
    stop_event = manager.Event()

    for i in range(process_count):
        process = multiprocessing.Process(target=worker, args=(i,))
        process.start()
        processes.append(process)

    all_pids = [p.pid for p in multiprocessing.active_children()] + [os.getpid()]
    gui_process = multiprocessing.Process(
        target=GUI, args=(my_work, stop_event, all_pids)
    )
    gui_process.start()

    # END
    time.sleep(5)
    print("Stopping")
    stop_event.set()

    gui_process.join()
    for process in processes:
        process.join()
    print("Done main")
    print("Hit Count", hit_count.value)
    print("List", len(shared_list))

    for i, v in my_work.items():
        print(f"Work {i}", v)
    print("Total", sum(my_work.values()))

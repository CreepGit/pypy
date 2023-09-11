import multiprocessing
import random
import time
import tkinter as tk
import tkinter.font as tkfont
import psutil
import os


class GUI:
    def __init__(self, messages: dict, stop_event, all_pids, display_list: list) -> None:
        self.window = tk.Tk()
        self.messages = messages
        self.stop_event = stop_event
        self.start_time = time.time()
        self.all_pids = all_pids + [os.getpid()]
        self.display_list = display_list
        
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Ubuntu mono", size=12)

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
        self.stop_event.set()
        print("END GUI")

    def draw_loop(self):
        if self.stop_event.is_set():
            self.window.destroy()
            return

        self.top_label.configure(
            text=f"{self.get_runtime_pretty()} {self.get_memory_usage()/1024/1024:0.0f}MB " + " ".join(f"{d}" for d in self.display_list if d is not None)
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

import multiprocessing
import threading
import multiprocessing.managers
import random
import time
import tkinter as tk
import tkinter.font as tkfont
import psutil
import os
import queue
import dataclasses
from typing import List, Any, Union


class GUI:
    def __init__(
        self, manager: multiprocessing.managers.SyncManager, title: str
    ) -> None:
        self.stop_event = manager.Event()
        self._main_pid = os.getpid()
        self._manager = manager
        self._sub_processes: dict[Any, GUI.SubProcesses] = {}
        self.title_top_text = self._manager.Value("s", "~x")
        self.footer_bottom_text = self._manager.Value("s", "")
        self.start_time = time.time()
        self._title = title
        self._tracking = []
        self._process = None
        self.is_gui_process = False

    def start(self):
        """Main process function"""
        self._process = multiprocessing.Process(target=self._start, args=())
        self._process.start()

    def _start(self):
        """GUI process function"""
        # Init
        self.is_gui_process = True
        self._window = tk.Tk()
        self._window.title(self._title)
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Ubuntu mono", size=12)
        # Gui
        self._window.protocol("WM_DELETE_WINDOW", self.stop)

        self._top_label = tk.Label(text="~", anchor="w", width=82, justify="left")
        self._top_label.grid(row=0, columnspan=2)
        self._footer_label = tk.Label(text="~", anchor="w", width=82, justify="left")
        self._footer_label.grid(row=100, columnspan=2)
        self._labels = {}

        for i, (name, sub) in enumerate(self._sub_processes.items()):
            row = i + 1
            tk.Label(text=f"{name:>3}").grid(row=row)
            label = tk.Label(text="~", anchor="w", width=80, justify="left")
            label.grid(row=row, column=1)
            self._labels[name] = label

        # End
        self.framerate = 30
        self._window.after(int(1000 / self.framerate), self._main_loop)
        self._window.mainloop()

        self.stop_event.set()
        while self.running_sub_count():
            time.sleep(0.05)

    def _main_loop(self):
        if self.is_stopping():
            self._exiting_title()
            if not self.running_sub_count():
                self._window.destroy()
                print("No process is running, safe to exit, exiting...")
                return

        tracked = "".join(f"{v.value} " for v in self._tracking)
        self._top_label.configure(
            text=f"{self.get_runtime_pretty()} {self.get_memory_usage()/1024/1024:0.0f}MB "
            + tracked
            + self.title_top_text.value
        )

        footer_text = self.footer_bottom_text.value
        if footer_text:
            self._footer_label.configure(
                text=f"{footer_text}",
            )
            if not self._footer_label.grid_info():
                self._footer_label.grid(row=100, columnspan=2)
        else:
            self._footer_label.grid_forget()

        for process_name, sub in self._sub_processes.items():
            while not sub.message_queue.empty():
                msg = sub.message_queue.get_nowait()
                self._labels[process_name].configure(text=f"{msg}")

        self._window.after(int(1000 / self.framerate), self._main_loop)

    @dataclasses.dataclass
    class SubProcesses:
        process: multiprocessing.Process
        name: Union[str, int]
        stopper: threading.Event
        message_queue: "queue.Queue[str]"

        def is_running(self):
            return not self.stopper.is_set()

    def running_sub_count(self):
        return sum(sp.is_running() for sp in self._sub_processes.values())

    def add_process(self, name, *, target, args=(), kwargs={}):
        """Similar to multiprocessing.Process, but gui tracks it.
        Use get_message_queue(name).put(msg) to send messages to the gui application.

        Can't add more processes once started."""
        assert name not in self._sub_processes
        assert not self.is_running(), "Can't add more processes once started."

        stopper = self._manager.Event()

        def wrapper(f):
            def wrapped(*args, **kwargs):
                nonlocal stopper
                try:
                    f(*args, **kwargs)
                except Exception as e:
                    stopper.set()
                    self._sub_processes[name].message_queue.put(f"~~ Error: {e}")
                    raise e
                stopper.set()
                self._sub_processes[name].message_queue.put("~~ Done")

            return wrapped

        new_target = wrapper(target)

        msg_q = self._manager.Queue()

        process = multiprocessing.Process(
            target=new_target, args=(name, *args), kwargs=kwargs
        )
        self._sub_processes[name] = self.SubProcesses(
            process=process,
            name=name,
            stopper=stopper,
            message_queue=msg_q,
        )
        process.start()

    def get_message_queue(self, name):
        """Get a message queue for a sub process that's listed next to it's name. Only latest message is shown."""
        return self._sub_processes[name].message_queue

    def _exiting_title(self):
        if not hasattr(self, "exiting_start"):
            self.exiting_start = time.time()
        self._window.title(f"🔥 Exiting... ({time.time() - self.exiting_start:0.2f}s)")

    def stop(self):
        """Does the same as pressing the x button, callable outside too"""
        self.stop_event.set()
        if not self.is_gui_process:
            if self._process:
                self._process.join()
            return
        
        self._exiting_title()
        self._top_label.configure(bg="pink")

        if self.running_sub_count() == 0:
            self._window.destroy()
            return

    def join(self, timeout=None):
        assert self._process is not None
        self._process.join(timeout=timeout)

    def easy_track(self, shared_value: multiprocessing.managers.ValueProxy):
        """Add a shared value to the top bar for easy viewing"""
        self._tracking.append(shared_value)

    # Getters
    def is_stopping(self):
        """Checks if desiring to stop, use is_running() to check if gui process is still active"""
        return self.stop_event.is_set()

    def is_running(self):
        """Runs until all other processes are done, use is_stopping() to check if desiring to stop"""
        if self._process is None:
            return False
        return self.running_sub_count() > 0 and self._process.is_alive()

    def get_runtime(self):
        return time.time() - self.start_time

    def get_runtime_pretty(self):
        rt = int(self.get_runtime())
        minutes = rt // 60
        seconds = rt % 60
        return f"{minutes:02.0f}:{seconds:02.0f}"

    def get_memory_usage(self):
        """In bytes, for all processes"""
        counter = self._get_memory_usage(os.getpid())  # <- Gui process
        counter += self._get_memory_usage(self._main_pid)  # <- Main process
        for sub in self._sub_processes.values():
            try:
                counter += self._get_memory_usage(sub.process.pid)
            except psutil.NoSuchProcess:
                pass
        return counter

    def _get_memory_usage(self, pid):
        process = psutil.Process(pid)
        return process.memory_info().rss


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
        gui = GUI(manager, "Example Worker GUI")

        live_process_count = manager.Value("s", "0 processes")
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
            live_process_count.value = (
                f"{len(multiprocessing.active_children())} processes"
            )
            hits_formatted.value = (
                f"{hits.value:0.0f} ({hits.value/gui.get_runtime():0.1f}/s)"
            )
            time.sleep(0.1)

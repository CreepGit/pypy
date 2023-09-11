import mp_gui2
import multiprocessing
import time


def worker(name):
    msgs = gui.get_message_queue(name)
    maxi = 10_000_000
    
    last_msg = time.time()
    a = 0
    
    for i in range(maxi):
        if kill_flag.is_set():
            break
        # if i % 100 == 0:
        #     if time.time() - last_msg > 0.1:
        #         last_msg = time.time()
        #         msgs.put(f"{100*i/maxi:1.0f}%")
                
        #         if gui.is_stopping():
        #             break
        a += 2


with multiprocessing.Manager() as manager:
    gui = mp_gui2.GUI(manager, "Speed example GUI")
    
    kill_flag = manager.Event()
    
    for i in range(5):
        gui.add_process(f"Worker {i}", target=worker, args=())

    start_time = time.time()
    gui.start()
    while gui.is_running():
        time.sleep(0.1)
    
    print(f"Time: {time.time() - start_time:0.3f}")
    
    gui.stop()
    gui.join()

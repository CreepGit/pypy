import multiprocessing
import time
import random


def f(x):
    time.sleep(random.uniform(0,1) ** 2)
    print(x)
    return

with multiprocessing.Pool(9) as pool:
    time.sleep(1)
    start_time = time.time()
    res = pool.map(f, range(100))
    print(len(res))
    print(time.time() - start_time, "s")


import numpy as np
from multiprocessing import shared_memory


class Strategy:
    def __init__(self, data_queue, port_queue,
                 sec_mem_name='', sec_mem_shape=(), sec_mem_dtype=None,
                 min_mem_name='', min_mem_shape=(), min_mem_dtype=None):
        # Signal Event를 port_queue로 push해준다.
        self.data_queue = data_queue
        self.port_queue = port_queue

        self.sec_mem_shape = sec_mem_shape
        self.sec_mem = shared_memory.SharedMemory(name=sec_mem_name)
        self.sec_mem_array = np.ndarray(shape=sec_mem_shape, dtype=sec_mem_dtype, buffer=self.sec_mem.buf)

        self.min_mem_shape = min_mem_shape
        self.min_mem = shared_memory.SharedMemory(name=min_mem_name)
        self.min_mem_array = np.ndarray(shape=min_mem_shape, dtype=min_mem_dtype, buffer=self.min_mem.buf)
        print(f'Strategy에서 shared_memory로 연결하였습니다.')

    def calc_signals(self):
        pass
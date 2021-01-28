import numpy as np
from multiprocessing import shared_memory
from bar import Bar


class Strategy(Bar):
    def __init__(self, data_queue, port_queue, order_queue, strategy_universe,
                 tick_mem_name='', tick_mem_shape=(), tick_mem_dtype=None,
                 hoga_mem_name='', hoga_mem_shape=(), hoga_mem_dtype=None,
                 min_mem_name='', min_mem_shape=(), min_mem_dtype=None):
        # Signal Event를 port_queue로 push해준다.
        self.data_queue = data_queue
        self.port_queue = port_queue
        self.order_queue = order_queue

        self.tick_mem_shape = tick_mem_shape
        self.tick_mem = shared_memory.SharedMemory(name=tick_mem_name)
        self.tick_mem_array = np.ndarray(shape=tick_mem_shape, dtype=tick_mem_dtype, buffer=self.tick_mem.buf)

        self.hoga_mem_shape = hoga_mem_shape
        self.hoga_mem = shared_memory.SharedMemory(name=hoga_mem_name)
        self.hoga_mem_array = np.ndarray(shape=hoga_mem_shape, dtype=hoga_mem_dtype, buffer=self.hoga_mem.buf)

        self.min_mem_shape = min_mem_shape
        self.min_mem = shared_memory.SharedMemory(name=min_mem_name)
        self.min_mem_array = np.ndarray(shape=min_mem_shape, dtype=min_mem_dtype, buffer=self.min_mem.buf)
        print(f'Strategy에서 shared_memory로 연결하였습니다.')

        self.symbol_list = strategy_universe
        print("Symbol_Table 잘업데이트 됐나 확인용으로 프린트 찍음!!!!!!!!!!!!!!!!!", self.SYMBOL_TABLE)

    def calc_signals(self):
        """
        calc signal
        """
        raise NotImplementedError("Should implement calc_signals()")

import numpy as np
from multiprocessing import shared_memory


class Strategy:
    def __init__(self, data_queue, port_queue,
                 tick_mem_name='', tick_mem_shape=(), tick_mem_dtype=None,
                 hoga_mem_name='', hoga_mem_shape=(), hoga_mem_dtype=None,
                 min_mem_name='', min_mem_shape=(), min_mem_dtype=None):
        # Signal Event를 port_queue로 push해준다.
        self.data_queue = data_queue
        self.port_queue = port_queue

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

    def calc_signals(self):
        """
        calc signal
        """
        raise NotImplementedError("Should implement calc_signals()")

    def get_latest_bar(self, symbol):
        """
        returns latest bar updated
        """
        raise NotImplementedError("Should implement get_latest_bar()")

    def get_latest_n_bars(self, symbol, N=1):
        """
        :param N: Number of wanted bars
        :return: the last N bars updated
        """
        raise NotImplementedError("Should implement get_latest_n_bars()")

    def get_latest_bar_datetime(self, symbol):
        """
        :return: a Python datetime object for the last bar
        """
        raise NotImplementedError("Should implement get_latest_bar_datetime()")

    def get_latest_bar_value(self, symbol, val_type):
        """
        :param val_type: one of OHLCV, Quotes, Open Interest(OI)
        :return: returns one of values designated by val_type
        """
        raise NotImplementedError("Should implement get_latest_bar_value()")

    def get_latest_n_bars_value(self, symbol, val_type, N=1):
        """
        :param symbol:
        :param val_type: one of OHLCV, Quotes, Open Interest(OI)
        :param N: Number of bars considered
        :return: returns one of N-bars values designated by val_type
        """
        raise NotImplementedError("Should implement get_latest_n_bars_value()")
import numpy as np
from multiprocessing import shared_memory
from roboticks.staticbar import StaticBar


class Strategy(StaticBar):
    def __init__(self, data_queue, port_queue, order_queue, strategy_universe, monitor_stocks,
                 sec_mem_name, sec_mem_shape, sec_mem_dtype, source):
        self.source = source

        # Signal Event를 port_queue로 push해준다.
        self.data_queue = data_queue
        self.port_queue = port_queue
        self.order_queue = order_queue

        self.symbol_list = strategy_universe # 전략에서 필요한 종목

        self.sec_mem_shape = sec_mem_shape
        self.sec_mem = shared_memory.SharedMemory(name=sec_mem_name)
        self.sec_mem_array = np.ndarray(shape=self.sec_mem_shape, dtype=sec_mem_dtype,
                                        buffer=self.sec_mem.buf)

        self.SYMBOL_TABLE = {symbol: i for i, symbol in enumerate(sorted(monitor_stocks))} # data handler에서 트래킹하고 있는
                                                                                           # 유니버스 전체

        # 상속하는 Bar 클래스의 SYMBOL_TABLE 바꿔주기!
        # self.bar.set_symbol_table({symbol: i for i, symbol in enumerate(sorted(monitor_stocks))})
        # print("Strategy SYMBOL TABLE 잘들어왔나? : ", self.bar.SYMBOL_TABLE)

    def calc_signals(self):
        """
        calc signal
        """
        raise NotImplementedError("Should implement calc_signals()")

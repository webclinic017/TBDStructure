import numpy as np
from multiprocessing import shared_memory
from bar import Bar, BarClient


class Strategy(BarClient):
    def __init__(self, data_queue, port_queue, order_queue, strategy_universe, monitor_stocks, bar):
        # Signal Event를 port_queue로 push해준다.
        super().__init__(bar)
        self.data_queue = data_queue
        self.port_queue = port_queue
        self.order_queue = order_queue

        self.symbol_list = strategy_universe # 잘들어옴

        # 상속하는 Bar 클래스의 SYMBOL_TABLE 바꿔주기!
        self.bar.set_symbol_table({symbol: i for i, symbol in enumerate(sorted(monitor_stocks))})
        print("Strategy SYMBOL TABLE 잘들어왔나? : ", self.bar.SYMBOL_TABLE)

    def calc_signals(self):
        """
        calc signal
        """
        raise NotImplementedError("Should implement calc_signals()")

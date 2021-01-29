import numpy as np
from multiprocessing import shared_memory
from bar import Bar


class Strategy(Bar):
    def __init__(self, data_queue, port_queue, order_queue, strategy_universe, monitor_stocks, SYMBOL_TABLE):
        # Signal Event를 port_queue로 push해준다.
        # super().__init__(Bar.SYMBOL_TABLE)
        super().__init__(SYMBOL_TABLE)
        self.data_queue = data_queue
        self.port_queue = port_queue
        self.order_queue = order_queue

        self.symbol_list = strategy_universe
        print("strategy_universe 잘업데이트 됐나 확인용으로 프린트 찍음!!!!!!!!!!!!!!!!!", self.symbol_list)

        # 상속하는 Bar 클래스의 SYMBOL_TABLE 바꿔주기!
        Bar.SYMBOL_TABLE = {symbol: i for i, symbol in enumerate(sorted(monitor_stocks))}
        print("Strategy SYMBOL TABLE 잘들어왔나? : ", self.SYMBOL_TABLE)

    def calc_signals(self):
        """
        calc signal
        """
        raise NotImplementedError("Should implement calc_signals()")

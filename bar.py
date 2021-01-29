from multiprocessing import shared_memory
import numpy as np
import datetime

class Bar:
    FIELD_TABLE = {
        'current_price': None,
        'cum_volume': None,
        'sell_hoga1': None,
        'sell_hoga2': None,
        'sell_hoga3': None,
        'sell_hoga4': None,
        'sell_hoga5': None,
        'sell_hoga6': None,
        'sell_hoga7': None,
        'sell_hoga8': None,
        'sell_hoga9': None,
        'sell_hoga10': None,
        'buy_hoga1': None,
        'buy_hoga2': None,
        'buy_hoga3': None,
        'buy_hoga4': None,
        'buy_hoga5': None,
        'buy_hoga6': None,
        'buy_hoga7': None,
        'buy_hoga8': None,
        'buy_hoga9': None,
        'buy_hoga10': None,
        'sell_hoga1_stack': None,
        'sell_hoga2_stack': None,
        'sell_hoga3_stack': None,
        'sell_hoga4_stack': None,
        'sell_hoga5_stack': None,
        'sell_hoga6_stack': None,
        'sell_hoga7_stack': None,
        'sell_hoga8_stack': None,
        'sell_hoga9_stack': None,
        'sell_hoga10_stack': None,
        'buy_hoga1_stack': None,
        'buy_hoga2_stack': None,
        'buy_hoga3_stack': None,
        'buy_hoga4_stack': None,
        'buy_hoga5_stack': None,
        'buy_hoga6_stack': None,
        'buy_hoga7_stack': None,
        'buy_hoga8_stack': None,
        'buy_hoga9_stack': None,
        'buy_hoga10_stack': None
        # 'total_buy_hoga_stack': None,
        # 'total_sell_hoga_stack': None,
        # 'net_buy_hoga_stack': None,
        # 'net_sell_hoga_stack': None,
        # 'ratio_buy_hoga_stack': None,
        # 'ratio_sell_hoga_stack': None
    }
    FIELD_TABLE = {field: i for i, field in enumerate(list(FIELD_TABLE.keys()))}

    def __init__(self, SYMBOL_TABLE, tick_mem_name='', tick_mem_shape=(), tick_mem_dtype=None,
                 hoga_mem_name='', hoga_mem_shape=(), hoga_mem_dtype=None,
                 min_mem_name='', min_mem_shape=(), min_mem_dtype=None):

        self.tick_mem_shape = tick_mem_shape
        self.tick_mem = shared_memory.SharedMemory(name=tick_mem_name)
        self.tick_mem_array = np.ndarray(shape=tick_mem_shape, dtype=tick_mem_dtype, buffer=self.tick_mem.buf)

        self.hoga_mem_shape = hoga_mem_shape
        self.hoga_mem = shared_memory.SharedMemory(name=hoga_mem_name)
        self.hoga_mem_array = np.ndarray(shape=hoga_mem_shape, dtype=hoga_mem_dtype, buffer=self.hoga_mem.buf)

        self.min_mem_shape = min_mem_shape
        self.min_mem = shared_memory.SharedMemory(name=min_mem_name)
        self.min_mem_array = np.ndarray(shape=min_mem_shape, dtype=min_mem_dtype, buffer=self.min_mem.buf)

        self.SYMBOL_TABLE = None

        self.latest_symbol_data = np.dstack([self.tick_mem_array, self.hoga_mem_array])

    def get_latest_bar(self, symbol):
        """
        :return: the last bar from the latest_symbol list.
        """
        try:
            bars_list = self.latest_symbol_data[self.SYMBOL_TABLE[symbol]]
        except KeyError:
            print("Symbol is not available!!")
            raise
        else:
            return bars_list[-1]

    def get_latest_n_bars(self, symbol, N=1):
        """
        :return: latest n bars or n-k if less available
        """
        try:
            bars_list = self.latest_symbol_data[self.SYMBOL_TABLE[symbol]]
        except KeyError:
            print("Symbol is not available!!")
            raise
        else:
            return bars_list[-N:]
        # update bar에서 latest_symbol_data에 넣어주는건 bar 하나인데 어떻게 -N개 만큼 가져올수 있는거지?

    def get_latest_bar_datetime(self, symbol):
        """
        :return: Python datetime object for the last bar
        """

        #추후 보완하기, 체결시간과 호가시간을 모두 반영해줘야 할 것 같다.
        # try:
        #     bars_list = list(self.latest_symbol_data[symbol])
        # except KeyError:
        #     print("Symbol is not available!!")
        #     raise
        # else:
        return datetime.datetime.now()

    def get_latest_bar_value(self, symbol, val_type):
        """
        :param val_type: one of OHLCV, Quotes, Open Interest(OI)
        :return: returns one of values designated by val_type
        """
        try:
            bars_list = self.latest_symbol_data[self.SYMBOL_TABLE[symbol]]
        except KeyError:
            print("Symbol is not available!!")
            raise
        else:
            return bars_list[-1][self.FIELD_TABLE[val_type]]

    def get_latest_n_bars_value(self, symbol, val_type, N=1):
        """
        :param val_type: one of OHLCV, Quotes, Open Interest(OI)
        :param N: Number of bars considered
        :return: returns one of N-bars values designated by val_type
        """
        try:
            bars_list = self.latest_symbol_data[self.SYMBOL_TABLE[symbol]]
        except KeyError:
            print("Symbol is not available!!")
            raise
        else:
            col_idx = self.FIELD_TABLE[val_type]
            print(bars_list[-1])
            print(self.FIELD_TABLE)
            return bars_list[:, col_idx]

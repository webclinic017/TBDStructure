import datetime
import numpy as np
from multiprocessing import shared_memory, current_process
import pandas as pd


class BarClient:
    """
    Bar 클래스를 사용하는 클래스가 상속받을 parent 클래스
    """

    def __init__(self, bar):
        """
        Bar 클래스에서 정의된 함수들로 override해주기
        """
        self.bar = bar

        self.get_latest_bar = bar.get_latest_bar
        self.get_latest_n_bars = bar.get_latest_n_bars
        self.get_latest_bar_datetime = bar.get_latest_bar_datetime
        self.get_latest_bar_value = bar.get_latest_bar_value
        self.get_latest_n_bars_value = bar.get_latest_n_bars_value


class Bar:
    FIELD_TABLE = {
        'current_price': None,
        'open': None,
        'high': None,
        'low': None,
        'volume': None,
        'sell_hoga1': None,
        'sell_hoga2': None,
        'sell_hoga3': None,
        'sell_hoga4': None,
        'sell_hoga5': None,
        # 'sell_hoga6': None,
        # 'sell_hoga7': None,
        # 'sell_hoga8': None,
        # 'sell_hoga9': None,
        # 'sell_hoga10': None,
        'buy_hoga1': None,
        'buy_hoga2': None,
        'buy_hoga3': None,
        'buy_hoga4': None,
        'buy_hoga5': None,
        # 'buy_hoga6': None,
        # 'buy_hoga7': None,
        # 'buy_hoga8': None,
        # 'buy_hoga9': None,
        # 'buy_hoga10': None,
        'sell_hoga1_stack': None,
        'sell_hoga2_stack': None,
        'sell_hoga3_stack': None,
        'sell_hoga4_stack': None,
        'sell_hoga5_stack': None,
        # 'sell_hoga6_stack': None,
        # 'sell_hoga7_stack': None,
        # 'sell_hoga8_stack': None,
        # 'sell_hoga9_stack': None,
        # 'sell_hoga10_stack': None,
        'buy_hoga1_stack': None,
        'buy_hoga2_stack': None,
        'buy_hoga3_stack': None,
        'buy_hoga4_stack': None,
        'buy_hoga5_stack': None,
        # 'buy_hoga6_stack': None,
        # 'buy_hoga7_stack': None,
        # 'buy_hoga8_stack': None,
        # 'buy_hoga9_stack': None,
        # 'buy_hoga10_stack': None
        # 'total_buy_hoga_stack': None,
        # 'total_sell_hoga_stack': None,
        # 'net_buy_hoga_stack': None,
        # 'net_sell_hoga_stack': None,
        # 'ratio_buy_hoga_stack': None,
        # 'ratio_sell_hoga_stack': None
    }
    FIELD_TABLE = {field: i for i, field in enumerate(list(FIELD_TABLE.keys()))}

    minute_table = {
        date: i for i, date in
        enumerate([d.strftime('%H%M%S') for d in pd.date_range('08:30', '15:30', freq='T')])
    }

    def __init__(self, sec_mem_name='', sec_mem_shape=(), sec_mem_dtype=None):

        self.sec_mem_shape = sec_mem_shape
        self.sec_mem = shared_memory.SharedMemory(name=sec_mem_name)
        self.sec_mem_array = np.ndarray(shape=sec_mem_shape, dtype=sec_mem_dtype, buffer=self.sec_mem.buf)

        self.SYMBOL_TABLE = None

    def set_symbol_table(self, symbol_table):
        self.SYMBOL_TABLE = symbol_table

    def get_latest_bar(self, symbol, freq):
        """
        :return: the last bar from the latest_symbol list.
        """
        try:
            if freq == "second":
                latest_symbol_data = self.sec_mem_array
                bars_list = latest_symbol_data[self.SYMBOL_TABLE[symbol]]
                return bars_list[-1]
            elif freq == "minute":
                pass
        except KeyError:
            print("Symbol is not available!!")
            raise


    def get_latest_n_bars(self, symbol, N=1):
        """
        :return: latest n bars or n-k if less available
        """
        try:
            latest_symbol_data = self.sec_mem_array
            bars_list = latest_symbol_data[self.SYMBOL_TABLE[symbol]]
        except KeyError:
            print("Symbol is not available!!")
            raise
        else:
            return bars_list[-N:]

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
            latest_symbol_data = self.sec_mem_array
            bars_list = latest_symbol_data[self.SYMBOL_TABLE[symbol]]
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
            latest_symbol_data = self.sec_mem_array
            print(latest_symbol_data, current_process().name)
            bars_list = latest_symbol_data[self.SYMBOL_TABLE[symbol]]
        except KeyError:
            print("Symbol is not available!!")
            raise
        else:
            col_idx = self.FIELD_TABLE[val_type]
            print(bars_list[-1], current_process().name)
            return bars_list[-N:, col_idx]

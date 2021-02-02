import datetime
import numpy as np
from multiprocessing import shared_memory, current_process
import pandas as pd


class StaticBar:

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

    @staticmethod
    def get_latest_bar(data, symbol, symbol_table, freq="second"):
        """
        :return: the last bar from the latest_symbol list.
        """
        try:
            if freq == "second":
                bars_list = data[symbol_table[symbol]]
                return bars_list[-1]
            elif freq == "minute":
                pass
        except KeyError:
            print("Symbol is not available!!")
            raise

    @staticmethod
    def get_latest_n_bars(data, symbol, symbol_table, N=1):
        """
        :return: latest n bars or n-k if less available
        """
        try:
            bars_list = data[symbol_table[symbol]]
        except KeyError:
            print("Symbol is not available!!")
            raise
        else:
            return bars_list[-N:]

    @staticmethod
    def get_latest_bar_datetime(data, symbol, symbol_table):
        """
        :return: Python datetime object for the last bar
        """

        # 추후 보완하기, 체결시간과 호가시간을 모두 반영해줘야 할 것 같다.
        # try:
        #     bars_list = list(self.latest_symbol_data[symbol])
        # except KeyError:
        #     print("Symbol is not available!!")
        #     raise
        # else:
        return datetime.datetime.now()

    @staticmethod
    def get_latest_bar_value(data, symbol, symbol_table, val_type):
        """
        :param val_type: one of OHLCV, Quotes, Open Interest(OI)
        :return: returns one of values designated by val_type
        """
        try:
            bars_list = data[symbol_table[symbol]]
        except KeyError:
            print("Symbol is not available!!")
            raise
        else:
            print(bars_list[-1], current_process().name)
            return bars_list[-1][StaticBar.FIELD_TABLE[val_type]]

    @staticmethod
    def get_latest_n_bars_value(data, symbol, symbol_table, val_type, N=1):
        """
        :param val_type: one of OHLCV, Quotes, Open Interest(OI)
        :param N: Number of bars considered
        :return: returns one of N-bars values designated by val_type
        """
        try:
            print(data, current_process().name)
            bars_list = data[symbol_table[symbol]]
        except KeyError:
            print("Symbol is not available!!")
            raise
        else:
            col_idx = StaticBar.FIELD_TABLE[val_type]
            # print(bars_list[-1], current_process().name)
            return bars_list[-N:, col_idx]

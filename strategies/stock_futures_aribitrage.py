import datetime
import numpy as np
import pandas as pd

from strategy import Strategy
from event import PairSignalEvent
from backtest import Backtest
from execution import SimulatedExecutionHandler

class StockFuturesArbitrage(Strategy):

    """
    Carries out Arbitrage trading on korean stock futures
    """

    def __init__(self, data_queue, port_queue, order_queue, strategy_universe, monitor_stocks,
                 sec_mem_name, sec_mem_shape, sec_mem_dtype):
        print('Strategy 1 started')
        super().__init__(data_queue, port_queue, order_queue, strategy_universe, monitor_stocks,
                         sec_mem_name, sec_mem_shape, sec_mem_dtype)

        self.stock_futures_dict = pd.read_pickle("./strategies/stock_futures_basecode_idx.pickle")
        self.bought = self._initial_bought_dict()
        self.expiration_datetime = "매주 둘째주 목요일 3시?"
        self.pair_dict = self._init_pairs_dict()


    def _initial_bought_dict(self):
        """
        Adds keys to the bought dict for all symbols and initially set them to "OUT"
        :return:
        """
        bought = {}
        for s in self.strategy_universe:
            bought[s] = "OUT"
        return bought

    def _init_pairs_dict(self):
        pair_dict = {}
        for i in self.strategy_universe:
            if len(i) == 8:
                pair_dict[i] = self.stock_futures_dict[i[1:3]]
        return pair_dict

    # 만기일 수동 DB 관리가 제일 나을듯 (대체휴무일 지정시 만기일 밀림)
    def calc_expiration_dateime(self):
        if self.bars.get_latest_bar_datetime(sf_code)


    def calc_signal_for_pairs(self):
        """
        generates signal based on pct_basis of stock futures
        :return:
        """
        for k, v in self.pair_dict.items():
            s_code = v
            sf_code = k
            bar_date = self.get_latest_bar_datetime(self.sec_mem_array, s_code, self.SYMBOL_TABLE)

            if self.bought[s_code] == "OUT" and self.bought[sf_code] == "OUT":
                s_ask = self.get_latest_bar_value(self.sec_mem_array, s_code, self.SYMBOL_TABLE, "sell_hoga1") # 주식
                sf_bid = self.get_latest_bar_value(self.sec_mem_array, sf_code, self.SYMBOL_TABLE, "buy_hoga1") # 주식선물
                entry_spread = (sf_bid/s_ask)-1

                if entry_spread >= 0.00:
                    print("ENTRY LONG: %s and SHORT: %s at %2f at %s" % (s_code, sf_code, entry_spread, bar_date))
                    signal = PairSignalEvent("sf_arbit", s_code, sf_code, bar_date, "ENTRY", 1.0, s_ask, sf_bid)
                    self.port_queue.put(signal)
                    self.bought[s_code] = "LONG"
                    self.bought[sf_code] = "SHORT"
                else:
                    pass

            elif self.bought[s_code] != "OUT" and self.bought[sf_code] != "OUT":
                s_bid = self.get_latest_bar_value(self.sec_mem_array, s_code, self.SYMBOL_TABLE, "buy_hoga1")  # 주식
                sf_ask = self.get_latest_bar_value(self.sec_mem_array, sf_code, self.SYMBOL_TABLE, "sell_hoga1")  # 주식선물
                exit_spread = (sf_ask / s_bid) - 1
                dt = datetime.datetime.utcnow()

                if bar_date == self.expiration_datetime: #만기일 3시까지 Backwardation 미발생시 강제청산/ 실제 트레이딩시에는 그냥 놔두면 현금정산 될듯.
                    print("FORCE EXIT SHORT: %s and LONG: %s at %2f at %s" % (s_code, sf_code, exit_spread, bar_date))
                    signal = PairSignalEvent("sf_arbit", sf_code, s_code, bar_date, "EXIT", 1.0, sf_ask, s_bid)
                    self.port_queue.put(signal)
                    self.bought[s_code] = "OUT"
                    self.bought[sf_code] = "OUT"

                else:
                    if exit_spread <= -0.01:
                        print("EXIT SHORT: %s and LONG: %s at %2f at %s" % (s_code, sf_code, exit_spread, bar_date))
                        signal = PairSignalEvent("sf_arbit", sf_code, s_code, bar_date, "EXIT", 1.0, sf_ask, s_bid)
                        self.port_queue.put(signal)
                        self.bought[s_code] = "OUT"
                        self.bought[sf_code] = "OUT"

            else:
                print("Bought dict LONG/SHORT status error: Both pairs should have same Bought position")




    def calc_signals(self):
        """
        generates signal based on pct_basis of stock futures
        """
        while True:
            market = self.data_queue.get()
            print("Stock_Fut_Aribit: ", market)
            self.calc_signal_for_pairs()

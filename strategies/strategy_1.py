from strategy import Strategy
from event import SignalEvent
from multiprocessing import Queue
import datetime
import numpy as np


class Strategy_1(Strategy):
    def __init__(self, data_queue, port_queue, order_queue, strategy_universe, monitor_stocks,
                 sec_mem_name, sec_mem_shape, sec_mem_dtype):
        print('Strategy 1 started')
        super().__init__(data_queue, port_queue, order_queue, strategy_universe, monitor_stocks,
                         sec_mem_name, sec_mem_shape, sec_mem_dtype)

        self.long_window = 400
        self.short_window = 100

    def calc_signals(self):
        print('calculating signal...')
        cnt = 0

        bought = {}
        for s in self.symbol_list:
            bought[s] = "OUT" # 나중엔 기존 포트 매입 종목 반영해야한다.

        while True:
            market = self.data_queue.get()
            # print("Strat:", market)
            cnt += 1

            for s in self.symbol_list:
                bars = self.get_latest_n_bars_value(self.sec_mem_array, s, self.SYMBOL_TABLE, 'current_price', N=self.long_window)
                bar_date = self.get_latest_bar_datetime(self.sec_mem_array, s, self.SYMBOL_TABLE)
                if (bars is not None) and (bars.size > 0):
                    short_sma = np.mean(bars[-self.short_window:])
                    long_sma = np.mean(bars[-self.long_window:])
                    symbol = s
                    dt = datetime.datetime.utcnow()
                    sig_dir = ""

                    if short_sma > long_sma and bought[s]=="OUT":
                        print("LONG: %s" % bar_date)
                        sig_dir = "LONG"
                        cur_price = self.get_latest_bar_value(self.sec_mem_array, s, self.SYMBOL_TABLE, 'current_price')
                        signal = SignalEvent(1, symbol, dt, sig_dir, 1.0, cur_price)
                        bought[s] = 'LONG'
                        self.port_queue.put(signal)

                    elif bought[s]=="OUT" and cnt==10:
                        print("LONG: %s" % bar_date)
                        sig_dir = "LONG"
                        cur_price = self.get_latest_bar_value(self.sec_mem_array, s, self.SYMBOL_TABLE, 'current_price')
                        signal = SignalEvent(1, symbol, dt, sig_dir, 1.0, cur_price)
                        bought[s] = 'LONG'
                        self.port_queue.put(signal)

                    elif bought[s]=="LONG" and cnt==30:
                        print("SHORT: %s" % bar_date)
                        sig_dir = "EXIT"
                        cur_price = self.get_latest_bar_value(self.sec_mem_array, s, self.SYMBOL_TABLE, 'current_price')
                        signal = SignalEvent(1, symbol, dt, sig_dir, 1.0, cur_price)
                        bought[s] = 'OUT'
                        self.port_queue.put(signal)

                    elif short_sma < long_sma and bought[s]=="LONG":
                        print("SHORT: %s" % bar_date)
                        sig_dir = "EXIT"
                        cur_price = self.get_latest_bar_value(self.sec_mem_array, s, self.SYMBOL_TABLE, 'current_price')
                        signal = SignalEvent(1, symbol, dt, sig_dir, 1.0, cur_price)
                        bought[s] = 'OUT'
                        self.port_queue.put(signal)
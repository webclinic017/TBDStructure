from strategy import Strategy
from event import SignalEvent
from multiprocessing import Queue

import datetime
import numpy as np


class Strategy_1(Strategy):
    def __init__(self, data_queue, port_queue):
        print('Strategy 1 started')
        super().__init__(data_queue, port_queue)

        self.symbol_list = ["005930", "096530"]
        self.long_window = 400
        self.short_window = 100

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


    def calc_signals(self):
        print('calculating signal')
        cnt = 0

        bought = {}
        for s in self.symbol_list:
            bought[s] = "OUT"

        while True:
            try:
                market = self.data_queue.get()
                cnt += 1

                for s in self.symbol_list:
                    bars = self.get_latest_n_bars_value(s, 'current_price', N=self.long_window)
                    bar_date = self.get_latest_bar_datetime(s)
                    if (bars is not None) and (bars.size > 0):
                        short_sma = np.mean(bars[-self.short_window:])
                        long_sma = np.mean(bars[-self.long_window:])

                        symbol = s
                        dt = datetime.datetime.utcnow()
                        sig_dir = ""

                        if short_sma > long_sma and bought[s]=="OUT":
                            print("LONG: %s" % bar_date)
                            sig_dir = "LONG"
                            cur_price = self.get_latest_bar_value(s, 'current_price')
                            signal = SignalEvent(1, symbol, dt, sig_dir, 1.0, cur_price)
                            bought[s] = 'LONG'
                            self.port_queue.put(signal)

                        elif bought[s]=="OUT" and cnt==10:
                            print("LONG: %s" % bar_date)
                            sig_dir = "LONG"
                            cur_price = self.get_latest_bar_value(s, 'current_price')
                            signal = SignalEvent(1, symbol, dt, sig_dir, 1.0, cur_price)
                            bought[s] = 'LONG'
                            self.port_queue.put(signal)

                        elif bought[s]=="LONG" and cnt==20:
                            print("SHORT: %s" % bar_date)
                            sig_dir = "EXIT"
                            cur_price = self.get_latest_bar_value(s, 'current_price')
                            signal = SignalEvent(1, symbol, dt, sig_dir, 1.0, cur_price)
                            bought[s] = 'OUT'
                            self.port_queue.put(signal)

                        elif short_sma < long_sma and bought[s]=="LONG":
                            print("SHORT: %s" % bar_date)
                            sig_dir = "EXIT"
                            cur_price = self.get_latest_bar_value(s, 'current_price')
                            signal = SignalEvent(1, symbol, dt, sig_dir, 1.0, cur_price)
                            bought[s] = 'OUT'
                            self.port_queue.put(signal)

            except Queue.empty:
                continue

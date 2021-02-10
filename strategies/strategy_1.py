import datetime
import numpy as np
from functools import partial

from roboticks.strategy import Strategy
from roboticks.event import SignalEvent, SecondEvent


class Strategy_1(Strategy):

    def __init__(self, data_queue, port_queue, order_queue, strategy_name, strategy_universe, monitor_stocks,
                 sec_mem_name, sec_mem_shape, sec_mem_dtype, source):

        self.strategy_name = strategy_name

        print('Strategy 1 started')
        super().__init__(data_queue, port_queue, order_queue, strategy_universe, monitor_stocks,
                         sec_mem_name, sec_mem_shape, sec_mem_dtype, source)

        self.long_window = 400
        self.short_window = 100

        # BarStatic partial 함수
        self.latest_bar_value = partial(self.get_latest_bar_value, data=self.sec_mem_array, symbol_table=self.SYMBOL_TABLE,
                                        val_type='current_price')
        self.latest_n_bars_value = partial(self.get_latest_n_bars_value, data=self.sec_mem_array, symbol_table=self.SYMBOL_TABLE,
                                           val_type='current_price', N=self.long_window)
        self.latest_bar_datetime = partial(self.get_latest_bar_datetime, data=self.sec_mem_array, symbol_table=self.SYMBOL_TABLE)

    def calc_signals(self):
        print('calculating signal...')
        cnt = 0

        bought = {}
        for s in self.strategy_universe:
            bought[s] = "OUT" # 나중엔 기존 포트 매입 종목 반영해야한다.

        while True:
            market = self.data_queue.get()
            if self.source == 'virtual':
                self.port_queue.put(SecondEvent())
            # print("Strat:", market)
            cnt += 1

            for s in self.strategy_universe:
                bars = self.latest_n_bars_value(symbol=s)
                bar_date = self.latest_bar_datetime(symbol=s)

                if (bars is not None) and (bars.size > 0):
                    short_sma = np.mean(bars[-self.short_window:])
                    long_sma = np.mean(bars[-self.long_window:])
                    symbol = s
                    dt = datetime.datetime.utcnow()

                    if short_sma > long_sma and bought[s] == "OUT":
                        print("LONG: %s" % bar_date)
                        sig_dir = "LONG"
                        cur_price = self.latest_bar_value(symbol=s)
                        signal = SignalEvent(self.strategy_name, symbol, dt, sig_dir, 1.0, cur_price)
                        bought[s] = 'LONG'
                        self.port_queue.put(signal)

                    elif bought[s]=="OUT" and cnt==50:
                        print("LONG: %s" % bar_date)
                        sig_dir = "LONG"
                        cur_price = self.latest_bar_value(symbol=s)
                        signal = SignalEvent(self.strategy_name, symbol, dt, sig_dir, 1.0, cur_price)
                        bought[s] = 'LONG'
                        self.port_queue.put(signal)

                    elif bought[s]=="LONG" and cnt==60:
                        print("SHORT: %s" % bar_date)
                        sig_dir = "EXIT"
                        cur_price = self.latest_bar_value(symbol=s)
                        signal = SignalEvent(self.strategy_name, symbol, dt, sig_dir, 1.0, cur_price)
                        bought[s] = 'OUT'
                        self.port_queue.put(signal)

                    elif short_sma < long_sma and bought[s]=="LONG":
                        print("SHORT: %s" % bar_date)
                        sig_dir = "EXIT"
                        cur_price = self.latest_bar_value(symbol=s)
                        signal = SignalEvent(self.strategy_name, symbol, dt, sig_dir, 1.0, cur_price)
                        bought[s] = 'OUT'
                        self.port_queue.put(signal)
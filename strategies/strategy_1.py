from strategy import Strategy
from event import SignalEvent


class Strategy_1(Strategy):
    def __init__(self, data_queue, port_queue):
        print('Strategy 1 started')
        super().__init__(data_queue, port_queue)

    def calc_signals(self):
        print('calculating signal')
        while True:
            market = self.data_queue.get()

            s_e = SignalEvent(
                strategy_id='',
                symbol='',
                datetime='',
                signal_type='',
                strength='',
                cur_price=''
            )
            self.port_queue.put(s_e)
from strategy import Strategy
from event import SignalEvent


class Strategy_2(Strategy):
    def __init__(self, data_queue, port_queue, order_queue,
                 tick_mem_name='', tick_mem_shape=(), tick_mem_dtype=None,
                 hoga_mem_name='', hoga_mem_shape=(), hoga_mem_dtype=None,
                 min_mem_name='', min_mem_shape=(), min_mem_dtype=None):
        print('Strategy 2 started')
        super().__init__(data_queue, port_queue, order_queue,
                         tick_mem_name, tick_mem_shape, tick_mem_dtype,
                         hoga_mem_name, hoga_mem_shape, hoga_mem_dtype,
                         min_mem_name, min_mem_shape, min_mem_dtype)

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
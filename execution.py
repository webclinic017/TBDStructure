from event import FillEvent


class ExecutionHandler:
    def __init__(self, port_queue, source='backtest'):
        """
        source: backtest, kiwoom, ebest, binance etc.
        """
        print('Execution Handler started')
        self.port_queue = port_queue
        self.source = source

    def execute_order(self, event):
        if self.source == 'backtest':
            pass

        if self.source == 'kiwoom':
            pass

        if self.source == 'ebest':
            pass

        if self.source == 'binance':
            pass

        f_e = FillEvent(
            timeindex='',
            symbol='',
            exchange='',
            quantity='',
            direction='',
            fill_cost='',
            est_fill_cost=''
        )
        self.port_queue.put(f_e)
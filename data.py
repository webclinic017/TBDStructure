from event import MarketEvent


class DataHandler:
    def __init__(self, data_queues, port_queue, source: str = 'csv'):
        """
        source: csv, kiwoom, ebest, binance etc.
        """
        print('Data Handler started')
        self.queues = data_queues + [port_queue]

    def update_bars(self):
        m_e = MarketEvent(
            symbol='',
            current_price=0,
            open_price=0,
            high_price=0,
            low_price=0,
            cum_volume=0
        )

        for q in self.queues:
            q.put(m_e)
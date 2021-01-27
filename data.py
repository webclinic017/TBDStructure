from event import MarketEvent


class DataHandler:
    def __init__(self, data_queues, port_queue, api_queue, source: str = 'csv'):
        """
        source: csv, kiwoom, ebest, binance etc.
        """
        print('Data Handler started')

        # source마다 들어오는 데이터가 다를 수 있기 때문에 소스 구분을 확실히 한다.
        self.source = source

        self.queues = data_queues + [port_queue]
        self.api_queue = api_queue

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

    def start_event_loop(self):
        while True:
            data = self.api_queue.get()

            # data handle
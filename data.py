import zmq

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

        # API 데이터를 소켓으로 받아올 수도 있다.
        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        self.socket.connect("tcp://localhost:5555")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')

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

    def kiwoom_event_loop(self):
        """
        키움증권 API는 32비트 프로그램으로 실행되기 때문에 메모리 사용이 효율적이지 않다.
        ZeroMQ로 실시간 데이터를 받아서 shared memory를 만들도록 한다.
        """
        while True:
            pass

    def start_event_loop(self):
        if self.source == 'kiwoom':
            self.kiwoom_event_loop()
        else:
            while True:
                data = self.api_queue.get()

                # data handle
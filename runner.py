import sys
from PyQt5.QtWidgets import QApplication
from multiprocessing import Queue, Process

from db import UserDB, PriceDB
from roboticks.data import DataHandler
from roboticks.portfolio import Portfolio
from roboticks.execution import ExecutionHandler

from ebest import ebest_data
from virtual.virtual_data import VirtualAPI
from kiwoom.realtime import KiwoomRealtimeAPI


class Runner:

    def __init__(self,
                 username: str,
                 strategy: str = None,
                 server_type: str = None):
        """
        아직 실행된 적 없는 전략 같은 경우 initial_cap을 설정해줘야 하지만
        이미 실행되고 있는 전략 같은 경우 DB에 저장하여 불러오는 방식으로 실행할 수 있다.

        strategy name, initial cap, monitor stocks 등 전략과 관련된 모든 정보는 DB에서 관리한다.
        """
        print('Starting Runner instance')

        self.db = UserDB(username)

        self.api_queue = Queue()
        self.port_queue = Queue()
        self.order_queue = Queue()
        self.tmp_queue = Queue()

        self.strategies = []

    def init_strategy(self):
        pass

    def add_strategy(self):
        pass

    def start_trading(self, source: str):
        """
        source: virtual, kiwoom, ebest, crypto
        """
        monitor_stocks = None

        # Process Setup

        ###############
        ### STEP #1 ###
        ###############
        dp = Process(target=self._data_handler_process, args=(source, monitor_stocks, self.data_queues,
                                                              self.port_queue, self.api_queue, self.tmp_queue), name='DataHandler')
        dp.start()

        shm_info = self.tmp_queue.get()
        sec_mem_name = shm_info['sec_mem_name']
        sec_mem_shape = shm_info['sec_mem_shape']
        sec_mem_dtype = shm_info['sec_mem_dtype']

        ###############
        ### STEP #2 ###
        ###############
        pp = Process(target=self._portfolio_process, args=(self.port_queue, self.order_queue, initial_cap, monitor_stocks,
                                                           sec_mem_name, sec_mem_shape, sec_mem_dtype), name="Portfolio")
        pp.start()

        ###############
        ### STEP #3 ###
        ###############
        self._start_strategies()

        ###############
        ### STEP #4 ###
        ###############
        ep = Process(target=self._execution_process, args=(self.port_queue, self.order_queue, server, source), name="ExecutionHandler")
        ep.start()

        if source == 'virtual':
            self._init_virtual_setup()
        elif source == 'kiwoom':
            self._init_kiwoom_setup(monitor_stocks)
        elif source == 'ebest':
            self._init_ebest_setup(monitor_stocks)
        elif source == 'crypto':
            self._init_crypto_setup()

    ## Processes
    def _data_handler_process(self, source, monitor_stocks, data_queues, port_queue, api_queue, tmp_queue):
        d = DataHandler(data_queues=data_queues, port_queue=port_queue, api_queue=api_queue,
                        monitor_stocks=monitor_stocks, source=source)
        tmp_queue.put({
            'sec_mem_name': d.sec_mem.name,
            'sec_mem_shape': d.sec_mem_shape,
            'sec_mem_dtype': d.sec_mem_dtype,
        })
        d.start_event_loop()

    def _portfolio_process(self, port_queue, order_queue, initial_cap, monitor_stocks, sec_mem_name, sec_mem_shape, sec_mem_dtype):
        e = Portfolio(port_queue, order_queue, initial_cap, monitor_stocks, sec_mem_name, sec_mem_shape, sec_mem_dtype)
        e.start_event_loop()

    def _execution_process(self, port_queue, order_queue, server, source):
        ex = ExecutionHandler(port_queue, order_queue, server, source)
        ex.start_execution_loop()

    # 전략 관련 메소드
    def _start_strategies(self):
        pass

    # API setup
    def _init_virtual_setup(self, date_from, date_to=None, monitor_stocks=[]):
        self.api = VirtualAPI()
        self.api.stream_data(date_from)

    def _init_kiwoom_setup(self, monitor_stocks):
        app = QApplication(sys.argv)
        _ = KiwoomRealtimeAPI(self.api_queue, self.port_queue, self.order_queue, monitor_stocks)
        sys.exit(app.exec_())

    def _init_ebest_setup(self, monitor_stocks):
        ebest_data.Main(self.api_queue, self.port_queue, self.order_queue, monitor_stocks)

    def _init_crypto_setup(self):
        """
        crypto setup은 binance, upbit, bithumb 등 다양한 거래소를 동시에 사용할 수 있도록 한다.
        국내 거래소를 통하여 btc를 구매한 다음 binance로 전송하여 트레이딩 하는 등 다양한 전략 구사가
        가능하게 하기 위함이다.
        """
        pass
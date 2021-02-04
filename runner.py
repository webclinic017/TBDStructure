import sys
import traceback
from PyQt5.QtWidgets import QApplication
from multiprocessing import Queue, Process

from roboticks.data import DataHandler
from roboticks.portfolio import Portfolio
from roboticks.execution import ExecutionHandler

from db import UserDB, PriceDB
from strategies import STRATEGY

# from ebest import ebest_data
from virtual.virtual_data import VirtualAPI
from kiwoom.realtime import KiwoomRealtimeAPI


class Runner:

    def __init__(self, username: str):
        """
        아직 실행된 적 없는 전략 같은 경우 initial_cap을 설정해줘야 하지만
        이미 실행되고 있는 전략 같은 경우 DB에 저장하여 불러오는 방식으로 실행할 수 있다.

        strategy name, initial cap, monitor stocks 등 전략과 관련된 모든 정보는 DB에서 관리한다.
        """
        print('Starting Runner instance')

        # 유저 이름이 DB에 없다면, 장고 인터페이스를 통하여 유저 등록을 하여야 한다.
        # >> python manage.py createsuperuser
        self.db = UserDB(username)

        self.api_queue = Queue()
        self.port_queue = Queue()
        self.order_queue = Queue()
        self.tmp_queue = Queue()
        self.data_queues = []

        self.source = None       # 같은 소스를 공유하는 여러 전략 실행할 수 있음 (반대 x)
        self.initial_cap = {}    # 전략별 initial_cap
        self.strategies = {}
        self.monitor_stocks = [] # 모든 전략들이 함께 공유하는 monitor stocks

    def init_strategy(self, strategy_name: str):
        """
        DB에 저장되어 있지 않은 전략을 실행하려면 초기 세팅을 설정해줘야 한다.
        """
        self.db.set_strategy(strategy_name)
        self.db.get_strategy() # get_strategy를 호출하면 데이터를 생성하여 리턴하거나 필터하여 리턴한다.

    def add_strategy(self, strategy_name: str or list):
        try:
            if type(strategy_name) == str:
                strategy_name = [strategy_name]

            for strategy in strategy_name:
                self.db.set_strategy(strategy)
                st = self.db.get_strategy()

                self.strategies[strategy] = STRATEGY[st['using_strategy']]

                # adding universe
                self.monitor_stocks = list(set(self.monitor_stocks + self.db.universe()))

                # adding initial cap
                self.initial_cap[strategy] = st['capital']

                self.data_queues.append(Queue())
        except:
            print(f'{strategy_name}은 존재하지 않습니다. STRATEGY 상수를 확인해주시기 바랍니다.')
            print(traceback.format_exc())

    def update_strategy(self, strategy_name, using_strategy=None, source=None, server_type=None, capital=None, currency=None, monitor_stocks=[]):
        self.db.set_strategy(strategy_name)
        self.db.save_strategy(using_strategy=using_strategy, source=source, server_type=server_type, capital=capital, currency=currency)
        self.db.add_to_universe(symbol=monitor_stocks)

    def start_trading(self, source: str, date_from: str = None, date_to: str = None, exclude: list = []):
        """
        source: virtual, kiwoom, ebest, crypto

        if source == virtual: date_from은 required, date_to가 없다면 date_to = date_from

        test를 진행하기 위해서 exclude를 인자로 추가하였다.
        exclude에는 data, portfolio, execution, strategy를 포함할 수 있으며,
        exclude된 프로세스는 실행되지 않는다.
        """
        if len(self.strategies) == 0:
            raise Exception('전략 설정을 먼저 하고 실행해주세요. (add_strategy를 실행하여야 합니다.)')

        if source == 'virtual' and date_from is None:
            raise Exception('Virtual API를 사용하려면 date_from을 yyyy-mm-dd 형식으로 설정하여야 합니다.')
        elif source == 'virtual' and date_to is None:
            date_to = date_from

        # Process Setup

        ###############
        ### STEP #1 ###
        ###############
        if 'data' not in exclude:
            dp = Process(target=self._data_handler_process, args=(source,), name='DataHandler')
            dp.start()

            shm_info = self.tmp_queue.get()
            sec_mem_name = shm_info['sec_mem_name']
            sec_mem_shape = shm_info['sec_mem_shape']
            sec_mem_dtype = shm_info['sec_mem_dtype']

        ###############
        ### STEP #2 ###
        ###############
        if 'portfolio' not in exclude:
            pp = Process(target=self._portfolio_process, args=(self.port_queue, self.order_queue, initial_cap, monitor_stocks,
                                                               sec_mem_name, sec_mem_shape, sec_mem_dtype), name="Portfolio")
            pp.start()

        ###############
        ### STEP #3 ###
        ###############
        if 'strategy' not in exclude:
            self._start_strategies()

        ###############
        ### STEP #4 ###
        ###############
        if 'execution' not in exclude:
            ep = Process(target=self._execution_process, args=(self.port_queue, self.order_queue, server, source), name="ExecutionHandler")
            ep.start()

        if source == 'virtual':
            self._init_virtual_setup(date_from, date_to)
        elif source == 'kiwoom':
            self._init_kiwoom_setup()
        elif source == 'ebest':
            self._init_ebest_setup()
        elif source == 'crypto':
            self._init_crypto_setup()

    ## Processes
    def _data_handler_process(self, source):
        """
        source는 Data Handler에서 데이터를 처리하는 방식이 소스별로 다를 수 있기 때문에 추가하였지만, 추후 제외하여도 됨
        """
        d = DataHandler(data_queues=self.data_queues, port_queue=self.port_queue, api_queue=self.api_queue,
                        monitor_stocks=self.monitor_stocks, source=source)
        self.tmp_queue.put({
            'sec_mem_name': d.sec_mem.name,
            'sec_mem_shape': d.sec_mem_shape,
            'sec_mem_dtype': d.sec_mem_dtype,
        })
        d.start_event_loop()

    def _portfolio_process(self, port_queue, order_queue, initial_cap, monitor_stocks, sec_mem_name, sec_mem_shape, sec_mem_dtype):
        """
        여러 전략별 포트 정보를 관리할 수 있도록 Portfolio 객체 수정하기
        """
        e = Portfolio(port_queue, order_queue, initial_cap, monitor_stocks, sec_mem_name, sec_mem_shape, sec_mem_dtype)
        e.start_event_loop()

    def _execution_process(self, port_queue, order_queue, server, source):
        """
        이베스트 객체 분리시켜서 주문은 무조건 order_queue로 넣기
        """
        ex = ExecutionHandler(port_queue, order_queue, server, source)
        ex.start_execution_loop()

    # 전략 관련 메소드
    def _start_strategies(self):
        """
        각 전략별로 프로세스를 분리하여 실행시키기
        """
        pass

    # API setup
    def _init_virtual_setup(self, date_from, date_to):
        self.api = VirtualAPI(self.api_queue)
        self.api.stream_data(date_from, date_to, monitor_stocks=self.monitor_stocks)

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


if __name__ == '__main__':
    r = Runner(username='ppark9553@gmail.com')

    # # 전략이 없다면 생성한 다음 add_strategy를 한다.
    # r.update_strategy(
    #     strategy_name='strategy_2_first',
    #     using_strategy='strategy_2',
    #     capital=1000000,
    #     monitor_stocks=['005930', '000020', '000030']
    # )
    # r.update_strategy(
    #     strategy_name='strategy_2_second',
    #     using_strategy='strategy_2',
    #     capital=10000000,
    #     monitor_stocks=['005930', '000270']
    # )

    r.add_strategy(['strategy_2_first', 'strategy_2_second'])

    r.start_trading(source='virtual', date_from='2021-02-03', exclude=['portfolio', 'execution', 'strategy'])

    print('r')

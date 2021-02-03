import sys
from PyQt5.QtWidgets import QApplication
from multiprocessing import Process, Queue

from strategies import Strategy_1, Strategy_2
from roboticks.data import DataHandler
from roboticks.portfolio import Portfolio
from roboticks.execution import ExecutionHandler
import pandas as pd

# from kiwoom.realtime import KiwoomRealtimeAPI
from virtual.virtual_data import VirtualAPI

from ebest import ebest_data


def strategy_process(strategy_cls, data_queue, port_queue, order_queue, strategy_universe, monitor_stocks,
                     sec_mem_name, sec_mem_shape, sec_mem_dtype):
    s = strategy_cls(data_queue, port_queue, order_queue, strategy_universe, monitor_stocks,
                     sec_mem_name, sec_mem_shape, sec_mem_dtype)
    s.calc_signals()


def data_handler_process(source, monitor_stocks, data_queues, port_queue, api_queue, tmp_queue):
    d = DataHandler(
        data_queues=data_queues,
        port_queue=port_queue,
        api_queue=api_queue,
        monitor_stocks=monitor_stocks,
        source=source)
    tmp_queue.put({
        'sec_mem_name': d.sec_mem.name,
        'sec_mem_shape': d.sec_mem_shape,
        'sec_mem_dtype': d.sec_mem_dtype,
    })

    d.start_event_loop()


def portfolio_process(port_queue, order_queue, initial_cap, monitor_stocks, sec_mem_name, sec_mem_shape, sec_mem_dtype):
    e = Portfolio(port_queue, order_queue, initial_cap, monitor_stocks, sec_mem_name, sec_mem_shape, sec_mem_dtype)
    e.start_event_loop()


def execution_process(port_queue, order_queue, server, source):
    ex = ExecutionHandler(port_queue, order_queue, server, source)
    ex.start_execution_loop()


# DataHandler에 shm 뿌려주는 역할함
def main_process(source, api_queue, port_queue, order_queue, monitor_stocks):
    if source == 'kiwoom':
        app = QApplication(sys.argv)
        _ = KiwoomRealtimeAPI(api_queue, port_queue, order_queue, monitor_stocks)
        sys.exit(app.exec_())

    elif source == 'ebest':
        ebest_data.Main(api_queue, port_queue, order_queue, monitor_stocks) # Myobject가 불러와지나?..

    elif source == 'virtual':
        v = VirtualAPI(api_queue)
        v.stream_data('2021-01-29')


if __name__ == '__main__':
    # Initialization
    source = 'ebest'
    server = 'demo' # ebest 서버: demo or hts
    initial_cap = 1000000



    # 주식선물 Universe
    stock_futures_univ = ['111R2000', '1CLR2000'] # 거래할 stock_futures의 유니버스만 정해주면 된다.
    stock_futures_dict = pd.read_pickle("./strategies/stock_futures_basecode_idx.pickle")
    strategy1_universe = [stock_futures_dict[code[1:3]] for code in stock_futures_univ] + stock_futures_univ # ['005930', '096530', "111R2000", "1CLR2000"]
    strategy2_universe = []  # '005930', '096530'

    monitor_stocks = list(set(strategy1_universe + strategy2_universe)) # ["111R2000", "1CLR2000"] 삼전, 씨젠 , set 써서 정렬됨

    st = [Strategy_1, Strategy_2]

    # market event를 push받기 위한 data_queue
    d_q = [Queue() for _ in range(1)] # len(st) 로 바꿔주기
    p_q = Queue()  # port_queue
    a_q = Queue()  # api_queue
    o_q = Queue()  # order_queue

    tmp_q = Queue()  # shared_memory 정보 받아오기 위한 큐

    # [Process #1]
    # Data Handler를 프로세스 실행
    dp = Process(target=data_handler_process, args=(source, monitor_stocks, d_q, p_q, a_q, tmp_q), name="DataHandler")
    dp.start()

    shm_info = tmp_q.get()
    sec_mem_name = shm_info['sec_mem_name']
    sec_mem_shape = shm_info['sec_mem_shape']
    sec_mem_dtype = shm_info['sec_mem_dtype']

    # # shared_memory를 가지고 있는 Bar 객체를 생성
    # bar = Bar(sec_mem_name, sec_mem_shape, sec_mem_dtype)

    # [Process #2]
    # Portfolio 프로세스 실행
    pp = Process(target=portfolio_process, args=(p_q, o_q, initial_cap, monitor_stocks,
                                                 sec_mem_name, sec_mem_shape, sec_mem_dtype), name="Portfolio")
    pp.start()

    # [Process #3+]
    # Strategy 프로세스 실행
    s1 = Process(target=strategy_process, args=(st[0], d_q[0], p_q, o_q, strategy1_universe, monitor_stocks,
                                                sec_mem_name, sec_mem_shape, sec_mem_dtype), name="Startegy_1")
    s1.start()

    # s2 = Process(target=strategy_process, args=(st[i], d_q[i], p_q, o_q, strategy2_universe,
    #                                             tick_mem_name, tick_mem_shape, tick_mem_dtype,
    #                                             hoga_mem_name, hoga_mem_shape, hoga_mem_dtype,
    #                                             min_mem_name, min_mem_shape, min_mem_dtype))
    # s2.start()


    # [Process #4]
    # Execution 프로세스 키움/이베스트/바이낸스 API 실행
    ex = Process(target=execution_process, args=(p_q, o_q, server, source), name="ExecutionHandler")
    ex.start()

    # [Process #5]
    # Main 프로세스(Data Vendor) 키움/이베스트/바이낸스 API 실행
    main_process(source=source, api_queue=a_q, port_queue=p_q, order_queue=o_q, monitor_stocks=monitor_stocks)

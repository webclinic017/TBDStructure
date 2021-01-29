import sys
from PyQt5.QtWidgets import QApplication
from multiprocessing import Process, Queue

from strategies import Strategy_1, Strategy_2
from data import DataHandler
from portfolio import Portfolio
from execution import ExecutionHandler

from kiwoom.realtime import KiwoomRealtimeAPI

from ebest import ebest_data, ebest_execution
from bar import Bar


def strategy_process(strategy_cls, data_queue, port_queue, order_queue, strategy_universe, monitor_stocks, SYMBOL_TABLE):
    s = strategy_cls(data_queue, port_queue, order_queue, strategy_universe, monitor_stocks, SYMBOL_TABLE)
    s.calc_signals()


def data_handler_process(source, monitor_stocks, data_queues, port_queue, api_queue, tmp_queue):
    d = DataHandler(
        data_queues=data_queues,
        port_queue=port_queue,
        api_queue=api_queue,
        monitor_stocks=monitor_stocks,
        source=source)
    tmp_queue.put({
        'tick_mem_name': d.tick_mem.name,
        'tick_mem_shape': d.tick_mem_shape,
        'tick_mem_dtype': d.tick_mem_dtype,
        'hoga_mem_name': d.hoga_mem.name,
        'hoga_mem_shape': d.hoga_mem_shape,
        'hoga_mem_dtype': d.hoga_mem_dtype,
        'min_mem_name': d.min_mem.name,
        'min_mem_shape': d.min_mem_shape,
        'min_mem_dtype': d.min_mem_dtype
    })
    d.start_event_loop()


def portfolio_process(port_queue, order_queue, initial_cap, monitor_stocks, bar):
    e = Portfolio(port_queue, order_queue, initial_cap, monitor_stocks, bar)
    e.start_event_loop()


def execution_process(port_queue, order_queue, source):
    ex = ExecutionHandler(port_queue, order_queue, source)
    ex.start_execution_loop()


# DataHandler에 shm 뿌려주는 역할함
def main_process(source, api_queue, port_queue, order_queue, monitor_stocks):
    if source == 'kiwoom':
        app = QApplication(sys.argv)
        _ = KiwoomRealtimeAPI(api_queue, port_queue, order_queue, monitor_stocks)
        sys.exit(app.exec_())

    elif source == 'ebest':
        ebest_data.Main(api_queue, port_queue, order_queue, monitor_stocks) # Myobject가 불러와지나?..


if __name__ == '__main__':
    # Initialization
    source = 'ebest'
    initial_cap = 1000000
    strategy1_universe = ['005930'] #, '096530']
    # strategy2_universe = ['004770']
    strategy2_universe = []
    monitor_stocks = list(set(strategy1_universe + strategy2_universe)) # ["111R2000", "1CLR2000"] 삼전, 씨젠 , set 써서 정렬됨

    st = [Strategy_1, Strategy_2]

    # market event를 push받기 위한 data_queue
    d_q = [Queue() for _ in range(len(st))]
    p_q = Queue()  # port_queue
    a_q = Queue()  # api_queue
    o_q = Queue()  # order_queue

    tmp_q = Queue()  # shared_memory 정보 받아오기 위한 큐

    # [Process #1]
    # Data Handler를 프로세스 실행
    dp = Process(target=data_handler_process, args=(source, monitor_stocks, d_q, p_q, a_q, tmp_q))
    dp.start()

    shm_info = tmp_q.get()
    tick_mem_name = shm_info['tick_mem_name']
    tick_mem_shape = shm_info['tick_mem_shape']
    tick_mem_dtype = shm_info['tick_mem_dtype']
    hoga_mem_name = shm_info['hoga_mem_name']
    hoga_mem_shape = shm_info['hoga_mem_shape']
    hoga_mem_dtype = shm_info['hoga_mem_dtype']
    min_mem_name = shm_info['min_mem_name']
    min_mem_shape = shm_info['min_mem_shape']
    min_mem_dtype = shm_info['min_mem_dtype']

    SYMBOL_TABLE = {symbol: i for i, symbol in enumerate(sorted(monitor_stocks))}

    # shared_memory를 가지고 있는 Bar 객체를 생성
    bar = Bar(None, tick_mem_name, tick_mem_shape, tick_mem_dtype,
              hoga_mem_name, hoga_mem_shape, hoga_mem_dtype,
              min_mem_name, min_mem_shape, min_mem_dtype)

    # [Process #2]
    # Portfolio 프로세스 실행
    pp = Process(target=portfolio_process, args=(p_q, o_q, initial_cap, monitor_stocks, bar))
    pp.start()

    # [Process #3+]
    # Strategy 프로세스 실행
    s1 = Process(target=strategy_process, args=(st[0], d_q[0], p_q, o_q, strategy1_universe, monitor_stocks, bar))
    s1.start()

    # s2 = Process(target=strategy_process, args=(st[i], d_q[i], p_q, o_q, strategy2_universe,
    #                                             tick_mem_name, tick_mem_shape, tick_mem_dtype,
    #                                             hoga_mem_name, hoga_mem_shape, hoga_mem_dtype,
    #                                             min_mem_name, min_mem_shape, min_mem_dtype))
    # s2.start()


    # [Process #4]
    # Execution 프로세스 키움/이베스트/바이낸스 API 실행
    ex = Process(target=execution_process, args=(p_q, o_q, source))
    ex.start()

    # [Process #5]
    # Main 프로세스 키움/이베스트/바이낸스 API 실행
    main_process(source=source, api_queue=a_q, port_queue=p_q, order_queue=o_q, monitor_stocks=monitor_stocks)

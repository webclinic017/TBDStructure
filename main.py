import sys
from PyQt5.QtWidgets import QApplication
from multiprocessing import Process, Queue

from strategies import Strategy_1, Strategy_2
from data import DataHandler
from portfolio import Portfolio

from kiwoom.realtime import KiwoomRealtimeAPI

def strategy_process(strategy_cls, data_queue, port_queue,
                     sec_mem_name, sec_mem_shape, sec_mem_dtype,
                     min_mem_name, min_mem_shape, min_mem_dtype):
    s = strategy_cls(data_queue, port_queue,
                     sec_mem_name, sec_mem_shape, sec_mem_dtype,
                     min_mem_name, min_mem_shape, min_mem_dtype)
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
        'min_mem_name': d.min_mem.name,
        'min_mem_shape': d.min_mem_shape,
        'min_mem_dtype': d.min_mem_dtype
    })
    d.start_event_loop()

def portfolio_process(port_queue):
    # Portfolio + Execution
    e = Portfolio(port_queue)
    e.start_event_loop()

def main(source, api_queue, port_queue, monitor_stocks):
    if source == 'kiwoom':
        app = QApplication(sys.argv)
        _ = KiwoomRealtimeAPI(api_queue, port_queue, monitor_stocks)
        sys.exit(app.exec_())


if __name__ == '__main__':
    # Initialization
    source = 'kiwoom'
    monitor_stocks = ['005930', '000020', '000030']
    st = [Strategy_1, Strategy_2]

    # market event를 push받기 위한 data_queue
    d_q = [Queue() for _ in range(len(st))]
    p_q = Queue() # port_queue
    a_q = Queue() # api_queue
    o_q = Queue() # order_queue

    tmp_q = Queue() # shared_memory 정보 받아오기 위한 큐

    # [Process #1]
    # Data Handler를 프로세스 실행
    dp = Process(target=data_handler_process, args=(source, monitor_stocks, d_q, p_q, a_q, tmp_q))
    dp.start()

    # [Process #2]
    # Portfolio 프로세스 실행
    pp = Process(target=portfolio_process, args=(p_q,))
    pp.start()

    shm_info = tmp_q.get()
    sec_mem_name = shm_info['sec_mem_name']
    sec_mem_shape = shm_info['sec_mem_shape']
    sec_mem_dtype = shm_info['sec_mem_dtype']
    min_mem_name = shm_info['min_mem_name']
    min_mem_shape = shm_info['min_mem_shape']
    min_mem_dtype = shm_info['min_mem_dtype']

    # [Process #3+]
    # Strategy 프로세스 실행
    pr = []
    for i in range(len(st)):
        p = Process(target=strategy_process, args=(st[i], d_q[i], p_q,
                                                   sec_mem_name, sec_mem_shape, sec_mem_dtype,
                                                   min_mem_name, min_mem_shape, min_mem_dtype))
        pr.append(p)
    
    _ = [p.start() for p in pr] # 프로세스 모두 실행

    # [Process #4]
    # Main 프로세스 키움/이베스트/바이낸스 API 실행
    main(source=source, api_queue=a_q, port_queue=p_q, monitor_stocks=monitor_stocks)

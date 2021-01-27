import sys
from PyQt5.QtWidgets import QApplication
from multiprocessing import Process, Queue

from strategies import Strategy_1, Strategy_2
from data import DataHandler
from portfolio import Portfolio

from kiwoom.realtime import KiwoomRealtimeAPI

def strategy_process(strategy_cls, data_queue, port_queue):
    s = strategy_cls(data_queue, port_queue)
    s.calc_signals()

def data_handler_process(data_queues, port_queue):
    dh = DataHandler(data_queues=data_queues, port_queue=port_queue)

def portfolio_process(port_queue):
    # Portfolio + Execution
    e = Portfolio(port_queue)
    e.start_event_loop()

def main(source, api_queue, port_queue):
    if source == 'kiwoom':
        app = QApplication(sys.argv)
        _ = KiwoomRealtimeAPI(api_queue, port_queue)
        sys.exit(app.exec_())


if __name__ == '__main__':
    st = [Strategy_1, Strategy_2]

    # market event를 push받기 위한 data_queue
    d_q = [Queue() for _ in range(len(st))]
    p_q = Queue() # port_queue
    a_q = Queue() # api_queue
    
    pr = []
    for i in range(len(st)):
        p = Process(target=strategy_process, args=(st[i], d_q[i], p_q))
        pr.append(p)
    
    _ = [p.start() for p in pr] # 프로세스 모두 실행

    # Data Handler를 프로세스 실행
    dp = Process(target=data_handler_process, args=(d_q, p_q))
    dp.start()
    
    # Portfolio 프로세스 실행
    pp = Process(target=portfolio_process, args=(p_q,))
    pp.start()
    
    # Main 프로세스 키움/이베스트/바이낸스 API 실행
    main(source='kiwoom', api_queue=a_q, port_queue=p_q)

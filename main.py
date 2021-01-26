from multiprocessing import Process, Queue

from strategies import Strategy_1, Strategy_2
from data import DataHandler
from portfolio import Portfolio

def strategy_process(strategy_cls, data_queue, port_queue):
    s = strategy_cls(data_queue, port_queue)
    s.calc_signals()

def portfolio_process(port_queue):
    # Portfolio + Execution
    e = Portfolio(port_queue)
    e.start_event_loop()


if __name__ == '__main__':
    st = [Strategy_1, Strategy_2]

    # market event를 push받기 위한 data_queue
    d_q = [Queue() for _ in range(len(st))]
    p_q = Queue() # port_queue
    
    pr = []
    for i in range(len(st)):
        p = Process(target=strategy_process, args=(st[i], d_q[i], p_q))
        pr.append(p)
    
    _ = [p.start() for p in pr] # 프로세스 모두 실행

    # Data Handler를 메인 프로세스에서 실행
    dh = DataHandler(data_queues=d_q, port_queue=p_q)
    
    # Portfolio 프로세스 실행
    p = Process(target=portfolio_process, args=(p_q,))
    p.start()

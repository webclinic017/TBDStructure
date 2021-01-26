class Strategy:
    def __init__(self, data_queue, port_queue):
        # Signal Event를 port_queue로 push해준다.
        self.data_queue = data_queue
        self.port_queue = port_queue

    def calc_signals(self):
        pass
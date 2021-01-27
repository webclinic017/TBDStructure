from bar import Bar


class Strategy(Bar):
    def __init__(self, data_queue, port_queue):
        # Signal Event를 port_queue로 push해준다.
        self.data_queue = data_queue
        self.port_queue = port_queue

    def calc_signals(self):
        """
        calc signal
        """
        raise NotImplementedError("Should implement calc_signals()")

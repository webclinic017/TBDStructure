class Strategy:
    def __init__(self, data_queue, port_queue):
        # Signal Event를 port_queue로 push해준다.
        self.data_queue = data_queue
        self.port_queue = port_queue

    def calc_signals(self):
        """
        calc signal
        """
        raise NotImplementedError("Should implement calc_signals()")

    def get_latest_bar(self, symbol):
        """
        returns latest bar updated
        """
        raise NotImplementedError("Should implement get_latest_bar()")

    def get_latest_n_bars(self, symbol, N=1):
        """
        :param N: Number of wanted bars
        :return: the last N bars updated
        """
        raise NotImplementedError("Should implement get_latest_n_bars()")

    def get_latest_bar_datetime(self, symbol):
        """
        :return: a Python datetime object for the last bar
        """
        raise NotImplementedError("Should implement get_latest_bar_datetime()")

    def get_latest_bar_value(self, symbol, val_type):
        """
        :param val_type: one of OHLCV, Quotes, Open Interest(OI)
        :return: returns one of values designated by val_type
        """
        raise NotImplementedError("Should implement get_latest_bar_value()")

    def get_latest_n_bars_value(self, symbol, val_type, N=1):
        """
        :param symbol:
        :param val_type: one of OHLCV, Quotes, Open Interest(OI)
        :param N: Number of bars considered
        :return: returns one of N-bars values designated by val_type
        """
        raise NotImplementedError("Should implement get_latest_n_bars_value()")
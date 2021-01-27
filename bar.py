class Bar:
    @staticmethod
    def get_latest_bar(symbol):
        """
        returns latest bar updated
        """
        pass

    @staticmethod
    def get_latest_n_bars(symbol, n=1):
        """
        :param n: Number of wanted bars
        :return: the last N bars updated
        """
        pass

    @staticmethod
    def get_latest_bar_datetime(symbol):
        """
        :return: a Python datetime object for the last bar
        """
        pass

    @staticmethod
    def get_latest_bar_value(symbol, val_type):
        """
        :param val_type: one of OHLCV, Quotes, Open Interest(OI)
        :return: returns one of values designated by val_type
        """
        pass

    @staticmethod
    def get_latest_n_bars_value(symbol, val_type, N=1):
        """
        :param symbol:
        :param val_type: one of OHLCV, Quotes, Open Interest(OI)
        :param N: Number of bars considered
        :return: returns one of N-bars values designated by val_type
        """
        pass

        # raise NotImplementedError("Should implement get_latest_n_bars_value()")
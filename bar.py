class Bar:

    FIELD_TABLE = {
        'current_price': None,
        'cum_volume': None,
        'sell_hoga1': None,
        'sell_hoga2': None,
        'sell_hoga3': None,
        'sell_hoga4': None,
        'sell_hoga5': None,
        'sell_hoga6': None,
        'sell_hoga7': None,
        'sell_hoga8': None,
        'sell_hoga9': None,
        'sell_hoga10': None,
        'buy_hoga1': None,
        'buy_hoga2': None,
        'buy_hoga3': None,
        'buy_hoga4': None,
        'buy_hoga5': None,
        'buy_hoga6': None,
        'buy_hoga7': None,
        'buy_hoga8': None,
        'buy_hoga9': None,
        'buy_hoga10': None,
        'sell_hoga1_stack': None,
        'sell_hoga2_stack': None,
        'sell_hoga3_stack': None,
        'sell_hoga4_stack': None,
        'sell_hoga5_stack': None,
        'sell_hoga6_stack': None,
        'sell_hoga7_stack': None,
        'sell_hoga8_stack': None,
        'sell_hoga9_stack': None,
        'sell_hoga10_stack': None,
        'buy_hoga1_stack': None,
        'buy_hoga2_stack': None,
        'buy_hoga3_stack': None,
        'buy_hoga4_stack': None,
        'buy_hoga5_stack': None,
        'buy_hoga6_stack': None,
        'buy_hoga7_stack': None,
        'buy_hoga8_stack': None,
        'buy_hoga9_stack': None,
        'buy_hoga10_stack': None,
        'total_buy_hoga_stack': None,
        'total_sell_hoga_stack': None,
        'net_buy_hoga_stack': None,
        'net_sell_hoga_stack': None,
        'ratio_buy_hoga_stack': None,
        'ratio_sell_hoga_stack': None
    }
    FIELD_TABLE = {field: i for i, field in enumerate(list(FIELD_TABLE.keys()))}

    SYMBOL_TABLE = None

    @staticmethod
    def get_latest_bar(self, symbol):
        """
        returns latest bar updated
        """
        pass

    @staticmethod
    def get_latest_n_bars(self, symbol, N=1):
        """
        :param N: Number of wanted bars
        :return: the last N bars updated
        """
        pass

    @staticmethod
    def get_latest_bar_datetime(self, symbol):
        """
        :return: a Python datetime object for the last bar
        """
        pass

    @staticmethod
    def get_latest_bar_value(self, symbol, val_type):
        """
        :param val_type: one of OHLCV, Quotes, Open Interest(OI)
        :return: returns one of values designated by val_type
        """
        pass

    @staticmethod
    def get_latest_n_bars_value(self, symbol, val_type, N=1):
        """
        :param symbol:
        :param val_type: one of OHLCV, Quotes, Open Interest(OI)
        :param N: Number of bars considered
        :return: returns one of N-bars values designated by val_type
        """
        pass
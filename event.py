class Event(object):
    pass

class MinuteEvent(Event):
    def __init__(self, symbol, date, current_price, open_price, high_price, low_price, cum_volume):
        self.type = 'MINUTE'
        self.symbol = symbol
        self.date = date
        self.current_price = current_price
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.cum_volume = cum_volume

class SecondEvent(Event):
    def __init__(self):
        self.type = 'SECOND'
        # self.symbol = symbol
        # self.date = date
        # self.current_price = current_price
        # self.cum_volume = cum_volume

class SignalEvent(Event):
    def __init__(self, strategy_id, symbol, datetime, signal_type, strength, cur_price):
        self.type = "SIGNAL"
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength
        self.cur_price = cur_price

class OrderEvent(Event):
    def __init__(self, symbol, order_type, quantity, direction, est_fill_cost):
        self.type = "ORDER"
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction
        self.est_fill_cost = est_fill_cost

    def print_order(self):
        print("Order: Symbols=%s, Type=%s, Quantity=%s, Direction=%s, est_Fill_Cost=%s" %
              (self.symbol, self.order_type, self.quantity, self.direction, self.est_fill_cost))

class FillEvent(Event):
    def __init__(self, timeindex, symbol, exchange, quantity, direction, fill_cost, est_fill_cost, commission=None):
        self.type = "FILL"
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost
        self.est_fill_cost = est_fill_cost

        if commission is None:
            self.commission = self.calc_commission()
        else:
            self.commission = commission

    def calc_commission(self, mkt="Stocks"):
        if self.exchange == "BT":
            fill_cost = self.est_fill_cost
        else:
            fill_cost = self.fill_cost

        transaction_cost = 0
        if mkt == "Stocks" and self.direction == "SELL":
            transaction_cost = 0.003 * fill_cost
        elif mkt == "Futures":
            transaction_cost = "need calculation"

        return transaction_cost
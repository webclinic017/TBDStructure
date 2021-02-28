# Event의 strategy_id == strategy_name ex) ma, arbit

class Event(object):
    pass

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


class PairSignalEvent(Event):
    def __init__(self, strategy_id, long_symbol, short_symbol, datetime, signal_type, ratio, long_cur_price, short_cur_price):
        self.type = "SIGNAL"
        self.strategy_id = strategy_id
        self.long_symbol = long_symbol
        self.short_symbol = short_symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.ratio = ratio
        self.long_cur_price = long_cur_price
        self.short_cur_price = short_cur_price


class OrderEvent(Event):
    def __init__(self, symbol, order_type, quantity, direction, est_fill_cost, exchange):
        self.type = "ORDER"
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction
        self.est_fill_cost = est_fill_cost
        self.exchange = exchange

    def print_order(self):
        print("Order: Symbols=%s, Type=%s, Quantity=%s, Direction=%s, est_Fill_Cost=%s, exchange=%s" %
              (self.symbol, self.order_type, self.quantity, self.direction, self.est_fill_cost, self.exchange))


class FillEvent(Event):
    def __init__(self, strategy_id, timeindex, accno, symbol, exchange, quantity, direction, fill_cost, est_fill_cost,
                 commission=None):
        self.type = "FILL"
        self.strategy_id = strategy_id
        self.timeindex = timeindex
        self.accno = accno
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


class JangoEvent(Event):

    def __init__(self, strategy_id=None, symbol=None, quantity=None, market_value=None, est_cash=None, fut_est_cash=None):
        self.type = "JANGO"
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.market_value = market_value
        self.quantity = quantity
        self.est_cash = est_cash
        self.fut_est_cash = fut_est_cash

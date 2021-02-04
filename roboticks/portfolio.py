from roboticks.event import OrderEvent
from roboticks.staticbar import StaticBar
import datetime
from multiprocessing import shared_memory
import numpy as np


class Portfolio(StaticBar):
    def __init__(self, port_queue, order_queue, initial_cap, monitor_stocks,
                 sec_mem_name, sec_mem_shape, sec_mem_dtype):
        print('Portfolio started')
        self.port_queue = port_queue
        self.order_queue = order_queue

        self.symbol_list = monitor_stocks
        self.initial_cap = initial_cap

        self.sec_mem_shape = sec_mem_shape
        self.sec_mem = shared_memory.SharedMemory(name=sec_mem_name)
        self.sec_mem_array = np.ndarray(shape=self.sec_mem_shape, dtype=sec_mem_dtype,
                                        buffer=self.sec_mem.buf)

        self.SYMBOL_TABLE = {symbol: i for i, symbol in enumerate(sorted(monitor_stocks))}

        # # 상속하는 Bar 클래스의 SYMBOL_TABLE 바꿔주기!
        # self.bar.set_symbol_table({symbol: i for i, symbol in enumerate(sorted(monitor_stocks))})
        # print("Portfolio SYMBOL TABLE 잘들어왔나? : ", self.bar.SYMBOL_TABLE)

        self.all_positions = self.construct_all_positions()
        self.current_positions = self.construct_current_positions()
        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

    def construct_all_positions(self):
        """
        Constructs the positions list using the start_date to determine when the time index will begin
        종목별 보유수량
        """
        # print(self.symbol_list)
        all_pos_dict = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        all_pos_dict["datetime"] = datetime.datetime.now()
        return [all_pos_dict]

    def construct_all_holdings(self):
        """
        Constructs the holding list using the start_date to determine when the time index will begin
        종목별 평가금액, 현금, 수수료
        """
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['cash'] = self.initial_cap
        d['commission'] = 0.0
        d['total_value'] = self.initial_cap
        return [d]

    def construct_current_positions(self):
        """
        This constructs the dictionary which will hold the instantaneous position of the portfolio
        across all symbols.
        """
        d = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        return d

    def construct_current_holdings(self):
        """
        This constructs the dictionary which will hold th instantaneous value of the portfolio
        across all symbols.
        """
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['cash'] = self.initial_cap
        d['commission'] = 0.0
        d['total_value'] = self.initial_cap
        return d  # bracket 없는 것만 construct_all_holdings() 와 다름

        # live trading에서는 Brokerage에서 바로 요청 후 반영가능! backtesting은 계산 필요.

    def update_timeindex(self, event):
        """
        Adds a new record to the positions matrix for the current market date bar.
        This reflects the PREVIOUS bar, i.e. all current market data at this stage is known(OHLCV).

        Makes use of a MarketEvent from the events queue.
        :param event:
        """
        # Move timeindex by updating current positions
        # If position of stock change -> Make adjustment to current positions
        # Updated by update_timeindex() right after..
        # 결국 current_position을 주축으로 계속 Fill과 current_price가격에 변화에 따른 Holding의 변화를 모니터링 하고
        # 이후 update_timeindex() 함수를 통해 반영하는 구조.
        latest_datetime = self.get_latest_bar_datetime(self.sec_mem_array, self.symbol_list[0], self.SYMBOL_TABLE)

        # Update positions
        pos_dict = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        pos_dict["datetime"] = latest_datetime

        for s in self.symbol_list:
            pos_dict[s] = self.current_positions[s]

        # Append the current positions
        self.all_positions.append(pos_dict)

        # Update holdings
        hold_dict = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        hold_dict["datetime"] = latest_datetime
        hold_dict['cash'] = self.current_holdings['cash']
        hold_dict['commission'] = self.current_holdings['commission']
        hold_dict['total_value'] = self.current_holdings['cash']
        # Commission 다시 0으로, 누적합이 되지않도록.
        self.current_holdings['commission'] = 0.0

        for s in self.symbol_list:
            # Approximation by current_price price
            cur_price = self.get_latest_bar_value(self.sec_mem_array, s, self.SYMBOL_TABLE, 'current_price')
            if cur_price == np.nan:  # 장시작후 초반에 가격이 업뎃 안돼면 0으로 들어옴, 전일 Holding Value로 대체해서 찍기.
                market_value = self.current_holdings[s]
            else:
                market_value = self.current_positions[s] * cur_price

            hold_dict[s] = market_value
            hold_dict['total_value'] += market_value

        # Append the current holdings
        self.all_holdings.append(hold_dict)
        # pd.DataFrame(self.all_holdings).to_csv("all_holdings.csv")

    def generate_naive_order(self, signal):
        """
        Simply files an Order object as a constant quantity sizing of the signal object,
        without risk management or position sizing considerations.
        :param signal: The tuple containing Signal information
        """
        order = None

        symbol = signal.symbol
        direction = signal.signal_type
        strength = signal.strength
        cur_price = signal.cur_price

        # 주식선물 8자리
        if len(symbol) == 8:
            mkt_quantity = 1000000 / (cur_price * 10) # 거래승수 10
        # 주식 6자리
        elif len(symbol) == 6:
            mkt_quantity = 1000000 / cur_price
        else:
            print("Portfolio: Wrong Symbol")
            mkt_quantity = 0

        est_fill_cost = cur_price * mkt_quantity  # for Backtest & Slippage calc / slippage cost = fill_cost(HTS) - est_fill_cost
        cur_quantity = self.current_positions[symbol]
        order_type = 'MKT'  # 추후 지정가 주문도 고려필요

        if direction == 'LONG' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY', est_fill_cost)
        if direction == 'SHORT' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL', est_fill_cost)

        if direction == 'EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL', est_fill_cost)
        if direction == 'EXIT' and cur_quantity < 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY', est_fill_cost)
        return order

    def generate_sf_arbit_order(self, signal):
        order1 = None
        order2 = None
        long_symbol = signal.long_symbol
        short_symbol = signal.short_symbol
        direction = signal.signal_type
        long_cur_price = signal.long_cur_price
        short_cur_price = signal.short_cur_price

        long_cur_quantity = self.current_positions[long_symbol]
        short_cur_quantity = self.current_positions[short_symbol]
        order_type = 'MKT'  # 추후 지정가 주문도 고려필요

        # 주식선물 8자리
        if len(short_symbol) == 8:
            short_mkt_quantity = 1000000 / (short_cur_price * 10)  # 거래승수 10
        else:
            short_mkt_quantity = 0
        # 주식 6자리
        if len(long_symbol) == 6:
            long_mkt_quantity = short_mkt_quantity * 10
        else:
            print("Portfolio: Wrong Symbol")
            long_mkt_quantity = 0
            short_mkt_quantity = 0

        # 예상 체결금액
        long_est_fill_cost = long_cur_price * long_mkt_quantity
        short_est_fill_cost = short_cur_price * short_mkt_quantity


        if direction == 'ENTRY' and long_cur_quantity == 0 and short_cur_quantity == 0:
            order1 = OrderEvent(long_symbol, order_type, long_mkt_quantity, 'BUY', long_est_fill_cost)
            order2 = OrderEvent(short_symbol, order_type, short_mkt_quantity, 'SELL', short_est_fill_cost)

        if direction == 'EXIT':
            if long_cur_quantity < 0:
                long_est_fill_cost = long_cur_price * long_cur_quantity
                order1 = OrderEvent(long_symbol, order_type, abs(long_cur_quantity), 'BUY', long_est_fill_cost)
            if short_cur_quantity > 0:
                short_est_fill_cost = short_cur_price * short_cur_quantity
                order2 = OrderEvent(short_symbol, order_type, abs(short_cur_quantity), 'SELL', short_est_fill_cost)

        return order1, order2

    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new orders based on the portfolio logic.
        Portfolio에서 전체 포트폴리오의 잔액, 균형을 보면서 주문을 내야함으로 Port Class에 들어와 있음.
        """
        if event.type == 'SIGNAL':
            if event.strategy_id == "sf_arbit":
                order1, order2 = self.generate_sf_arbit_order(event)
                self.port_queue.put(order1)
                self.port_queue.put(order2)
            else:
                order_event = self.generate_naive_order(event)
                self.port_queue.put(order_event)


    def update_positions_from_fill(self, fill):
        """
        Takes a Fill object and updates the position matrix to reflect the new position.
        :param fill: The Fill object to update the position with
        """

        # Check whether the fill is a buy or sell
        fill_dir = 0
        if fill.direction == "BUY":
            fill_dir = 1
        elif fill.direction == "SELL":
            fill_dir = -1
        else:
            print("Fill direction error at position")

        # Update position list with new quantity
        self.current_positions[fill.symbol] += fill_dir * fill.quantity

    def update_holdings_from_fill(self, fill):
        """
        Takes a Fill object and updates the holding matrix to reflect the holdings value.
        :param fill: The Fill object to update the holdings with
        """

        # Check whether the fill is a buy or sell
        fill_dir = 0
        if fill.direction == "BUY":
            fill_dir = 1
        elif fill.direction == "SELL":
            fill_dir = -1
        else:
            print("Fill direction error at holdings")

        # Update holdings list with new quantity
        # Live Trading에서는 hts의 매입금액 사용하면 될듯, 결국 Slippage 비용도 여기에 반영해야함.
        if fill.exchange == 'ebest':
            fill_cost = fill.fill_cost
        else:
            fill_price = self.get_latest_bar_value(self.sec_mem_array, fill.symbol, self.SYMBOL_TABLE, 'current_price')
            fill_cost = fill_dir * fill_price * fill.quantity

        self.current_holdings[fill.symbol] += fill_cost
        self.current_holdings['commission'] += fill.commission  # 수수료
        self.current_holdings["cash"] -= fill_cost + fill.commission
        # update_timeindex에서 q * current_price 된 평가금액 얹어줌. # 필요없는 부분인것 같기도..일부러 cash랑 맞춰줌
        self.current_holdings['total_value'] -= fill_cost + fill.commission

    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings from FillEvent.
        :param event:
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def update_jango(self, event):
        """
        Updates Current Positions according to JangoEvent from HTS.
        :param event:
        :return:
        """
        if event.type == "JANGO":
            if event.quantity is not None:
                self.current_positions[event.symbol] = event.quantity
                self.current_holdings[event.symbol] = event.market_value
                self.current_holdings["total_value"] = sum(keys for keys in self.current_holdings.values()) - \
                                                       self.current_holdings['total_value']
            else:
                self.current_holdings["cash"] = event.est_cash

            print(self.current_holdings)

    def start_event_loop(self):
        """
        Portfolio 클래스의 이벤트 루프를 실행하여,
        DataHandler의 MarketEvent, Strategy의 OrderEvent, Execution의 FillEvent를 기다린다.
        Event가 도달하면 바로 처리하는 방식으로 작동한다.
        """
        while True:
            event = self.port_queue.get()

            if event.type == 'SECOND':
                print(event)
                self.update_timeindex(event)

            elif event.type == 'SIGNAL':
                print(event)
                self.update_signal(event)

            elif event.type == 'ORDER':
                print(event)
                self.order_queue.put(event)

            elif event.type == 'FILL':
                print(event)
                self.update_fill(event)

            # 현재는 장시작할때 한번 업데이트, 1분에 한번 정도로 지속적으로 HTS와 맞춰줘도 좋을듯
            elif event.type == 'JANGO':
                print(event)
                self.update_jango(event)
            else:
                print(f'Unknown Event type: {event.type}')

from execution import ExecutionHandler
from event import OrderEvent
from bar import Bar
import datetime
import pandas as pd


class Portfolio(Bar):
    def __init__(self, port_queue, order_queue, initial_cap, monitor_stocks, SYMBOL_TABLE):
        # super().__init__(Bar.SYMBOL_TABLE)
        super().__init__(SYMBOL_TABLE)
        print('Portfolio started')
        self.port_queue = port_queue
        self.order_queue = order_queue
        # self.execution_handler = ExecutionHandler(port_queue=port_queue)

        self.all_positions = self.construct_all_positions()
        self.current_positions = self.construct_current_positions()
        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()
        self.symbol_list = monitor_stocks
        self.initial_cap = initial_cap
        # 상속하는 Bar 클래스의 SYMBOL_TABLE 바꿔주기!
        Bar.SYMBOL_TABLE = {symbol: i for i, symbol in enumerate(sorted(monitor_stocks))}
        print("Portfolio SYMBOL TABLE 잘들어왔나? : ", Bar.SYMBOL_TABLE)

    def construct_all_positions(self):
        """
        Constructs the positions list using the start_date to determine when the time index will begin
        종목별 보유수량
        """
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
        #Move timeindex by updating current positions
        #If position of stock change -> Make adjustment to current positions
        #Updated by update_timeindex() right after..
        #결국 current_position을 주축으로 계속 Fill과 current_price가격에 변화에 따른 Holding의 변화를 모니터링 하고
        #이후 update_timeindex() 함수를 통해 반영하는 구조.
        latest_datetime = self.get_latest_bar_datetime(self.symbol_list[0])

        #Update positions
        pos_dict = dict((k, v) for k, v in [(s,0) for s in self.symbol_list])
        pos_dict["datetime"] = latest_datetime

        for s in self.symbol_list:
            pos_dict[s] = self.current_positions[s]

        #Append the current positions
        self.all_positions.append(pos_dict)

        #Update holdings
        hold_dict = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        hold_dict["datetime"] = latest_datetime
        hold_dict['cash'] = self.current_holdings['cash']
        hold_dict['commission'] = self.current_holdings['commission']
        hold_dict['total_value'] = self.current_holdings['cash']

        for s in self.symbol_list:
            #Approximation by current_price price
            market_value = self.current_positions[s] * self.get_latest_bar_value(s, 'current_price')
            hold_dict[s] = market_value
            hold_dict['total_value'] += market_value

        #Append the current holdings
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

        mkt_quantity = 1
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

    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new orders based on the portfolio logic.
        Portfolio에서 전체 포트폴리오의 잔액, 균형을 보면서 주문을 내야함으로 Port Class에 들어와 있음.
        """
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.port_queue.put(order_event)

    def update_positions_from_fill(self, fill):
        """
        Takes a Fill object and updates the position matrix to reflect the new position.
        :param fill: The Fill object to update the position with
        """

        #Check whether the fill is a buy or sell
        fill_dir = 0
        if fill.direction == "BUY":
            fill_dir = 1
        elif fill.direction == "SELL":
            fill_dir = -1
        else:
            print("Fill direction error at position")

        #Update position list with new quantity
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
        fill_cost = self.get_latest_bar_value(fill.symbol, 'current_price') #Live Trading에서는 hts의 매입금액 사용하면 될듯, 결국 Slippage 비용도 여기에 반영해야함.
        cost = fill_dir * fill_cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission #수수료
        self.current_holdings["cash"] -= cost + fill.commission
        self.current_holdings['total_value'] -= cost + fill.commission #update_timeindex에서 q * current_price 된 평가금액 얹어줌. # 필요없는 부분인것 같기도..일부러 cash랑 맞춰줌

    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings from FillEvent.
        :param event:
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)


    def start_event_loop(self):
            """
            Portfolio 클래스의 이벤트 루프를 실행하여,
            DataHandler의 MarketEvent, Strategy의 OrderEvent, Execution의 FillEvent를 기다린다.
            Event가 도달하면 바로 처리하는 방식으로 작동한다.
            """
            while True:
                event = self.port_queue.get()

                if event.type == 'MARKET':
                    self.update_timeindex(event)

                elif event.type == 'SIGNAL':
                    self.update_signal(event)

                elif event.type == 'ORDER':
                    self.order_queue.put(event)

                elif event.type == 'FILL':
                    self.update_fill(event)

                else:
                    print(f'Unknown Event type: {event.type}')

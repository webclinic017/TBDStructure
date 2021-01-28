# import zmq
# import datetime
import numpy as np
import pandas as pd
from multiprocessing import shared_memory

from event import MarketEvent

from bar import Bar

second_table = {
    date: i for i, date in
    enumerate([d.strftime('%H%M%S') for d in pd.date_range('08:30', '15:30', freq='S')])
}

minute_table = {
    date: i for i, date in
    enumerate([d.strftime('%H%M%S') for d in pd.date_range('08:30', '15:30', freq='T')])
}

FIELD_TABLE = Bar.FIELD_TABLE

class DataHandler:
    def __init__(self, data_queues, port_queue, api_queue, monitor_stocks, source: str = 'csv'):
        """
        source: csv, kiwoom, ebest, binance etc.
        """
        print('Data Handler started')

        # source마다 들어오는 데이터가 다를 수 있기 때문에 소스 구분을 확실히 한다.
        self.source = source
        
        self.queues = data_queues + [port_queue]
        self.api_queue = api_queue
        
        # monitor stock list 받아서 symbol table 만들기
        self.symbol_list = monitor_stocks
        self.symbol_cnt = len(self.symbol_list)
        self.symbol_table = {symbol: i for i, symbol in enumerate(sorted(self.symbol_list))}
        # symbol_time_table: 최근 shared_memory에 업데이트된 시간
        self.symbol_time_table = {symbol: {'시': '08', '분': '29'} for symbol in self.symbol_list}

        # [초봉 array 생성] --> 가격/호가 array를 따로 생성한다.
        sec_field_cnt = len(FIELD_TABLE.keys())  # 컬럼수 (FIELD_TABLE 참고)
        # second_cnt가 너무 커지기 때문에 dequeue하는 방식을 취하도록 한다.
        # 추후 RAM이 좋아지거나 전략을 수정할 경우 다른 방식을 고려해본다.
        # second_cnt = len(second_table.keys())
        second_cnt = 1000 # 1000초까지만 데이터를 홀딩한다 (임의로 정한 timeframe)

        # [초봉 #1] tick array
        # current_price, cum_volume
        self.tick_mem_shape = (int(self.symbol_cnt), int(second_cnt), 2)

        tick_array = np.zeros(self.tick_mem_shape)
        self.tick_mem_dtype = tick_array.dtype
        self.tick_mem_size = tick_array.nbytes

        self.tick_mem = shared_memory.SharedMemory(create=True, size=self.tick_mem_size)
        self.tick_mem_array = np.ndarray(shape=self.tick_mem_shape, dtype=self.tick_mem_dtype, buffer=self.tick_mem.buf)
        self.tick_mem_array[:] = tick_array[:]
        del tick_array

        # [초봉 #2] hoga array
        self.hoga_mem_shape = (int(self.symbol_cnt), int(second_cnt), int(sec_field_cnt) - 2)

        hoga_array = np.zeros(self.hoga_mem_shape)
        self.hoga_mem_dtype = hoga_array.dtype
        self.hoga_mem_size = hoga_array.nbytes

        self.hoga_mem = shared_memory.SharedMemory(create=True, size=self.hoga_mem_size)
        self.hoga_mem_array = np.ndarray(shape=self.hoga_mem_shape, dtype=self.hoga_mem_dtype, buffer=self.hoga_mem.buf)
        self.hoga_mem_array[:] = hoga_array[:]
        del hoga_array

        # [분봉 array 생성]
        # current_price, open_price, high, low, cum_volume, trade_sell_hoga1, trade_buy_hoga1
        min_field_cnt = 7
        minute_cnt = len(minute_table.keys())
        self.min_mem_shape = (int(self.symbol_cnt), int(minute_cnt), int(min_field_cnt))

        min_array = np.zeros(self.min_mem_shape)
        self.min_mem_dtype = min_array.dtype
        self.min_mem_size = min_array.nbytes

        self.min_mem = shared_memory.SharedMemory(create=True, size=self.min_mem_size)
        self.min_mem_array = np.ndarray(shape=self.min_mem_shape, dtype=self.min_mem_dtype, buffer=self.min_mem.buf)
        self.min_mem_array[:] = min_array[:]
        del min_array

        print('Shared Memory array를 생성하였습니다.')
        print(f'[Second Tick Array] Memory: {self.tick_mem.name} / Shape: {self.tick_mem_shape} / Size: {self.tick_mem_size/1e6} MBs')
        print(f'[Second Hoga Array] Memory: {self.hoga_mem.name} / Shape: {self.hoga_mem_shape} / Size: {self.hoga_mem_size / 1e6} MBs')
        print(f'[Minute Array] Memory: {self.min_mem.name} / Shape: {self.min_mem_shape} / Size: {self.min_mem_size / 1e6} MBs')

        # # API 데이터를 소켓으로 받아올 수도 있다.
        # context = zmq.Context()
        # self.socket = context.socket(zmq.SUB)
        # self.socket.connect("tcp://localhost:5555")
        # self.socket.setsockopt_string(zmq.SUBSCRIBE, '')

    def update_bars(self, symbol, date, current_price, open_price, high, low,
                    cum_volume, trade_sell_hoga1, trade_buy_hoga1):
        # 분봉 데이터가 업데이트되면 자동으로 연결된 모든 프로세스로 분봉 데이터 보내주기
        m_e = MarketEvent(
            symbol=symbol,
            date=date,
            current_price=current_price,
            open_price=open_price,
            high_price=high,
            low_price=low,
            cum_volume=cum_volume
        )

        for q in self.queues:
            q.put(m_e)

    def start_event_loop(self):
        while True:
            data = self.api_queue.get()

            if data['code'] in self.symbol_list:
                # backtest할때는 전종목 데이터를 보내는 경우도 있기 때문에 필터하여 업데이트하기
                self.update_shared_memory(data)

    def update_shared_memory(self, data):
        code = data['code']
        code_idx = self.symbol_table[code]

        # 초봉 업데이트(초봉이 아닌 틱봉인듯)
        # tick/hoga 모두 업데이트해준다 (dequeue하는 방식!!)
        if data['type'] == 'tick':
            trade_date = data['trade_date']
            # date_idx = second_table[trade_date] --> 이제 date_idx는 없다
            # self.sec_mem_array[code_idx, date_idx, :2] = [data['current_price'], data['cum_volume']]
            prev_upper = self.tick_mem_array[code_idx, 1:, :]
            self.tick_mem_array[code_idx, 0:-1, :] = prev_upper # 위의 한줄을 제외하고 위로 올린다
            self.tick_mem_array[code_idx, -1, :] = [data['current_price'], data['cum_volume']] # 마지막줄에 새로 들어온 데이터를 넣는다
        elif data['type'] == 'hoga':
            trade_date = data['hoga_date']
            prev_upper = self.hoga_mem_array[code_idx, 1:, :]
            self.hoga_mem_array[code_idx, 0:-1, :] = prev_upper
            self.hoga_mem_array[code_idx, -1, :] = [data.get(field) if data.get(field) is not None else 0
                                                    for field in FIELD_TABLE.keys()
                                                    if field not in ['current_price', 'cum_volume']]

        if data['type'] == 'tick':
            # 분봉 업데이트
            # 틱데이터를 초단위로 업데이트하였다면 분단위로 업데이트도 따로 진행한다.
            # 분봉 업데이트는 완료후 소켓 연결로 업데이트 내용을 publish해준다.
            # 모든 subscriber들은 변경된 데이터를 받을 수 있다.
            hour = trade_date[:2]
            minute = trade_date[2:4]
            second = '00'
            min_date = f'{hour}{minute}{second}'
            date_idx = minute_table[min_date]

            update_hour = self.symbol_time_table[code]['시']
            updated_minute = self.symbol_time_table[code]['분']
            updated_min_date = f'{update_hour}{updated_minute}00'

            if (int(updated_min_date) != int(min_date)) and (int(min_date) > int(updated_min_date)):
                """
                Issue: 데이터가 순차적으로 들어오지 않으면 분봉 데이터가 꼬일 수 있다
                       키움에서 제공하는 데이터는 초단위까지밖에 데이터를 제공하지 않기 때문에
                       로컬에서 찍은 데이터를 기반으로 데이터를 만들 수밖에 없다.
                """

                # 분이 바뀌었기 때문에 새로운 row를 추가해주는 작업
                self.symbol_time_table[code]['시'] = hour
                self.symbol_time_table[code]['분'] = minute

                # current_price, open_price, high, low, cum_volume, trade_sell_hoga1, trade_buy_hoga1
                self.min_mem_array[code_idx, date_idx, :] = [
                    data['current_price'],
                    data['current_price'], # 시가는 종가로 설정하기
                    data['current_price'], # 고가도 종가로 설정하기
                    data['current_price'], # 저가도 종가로 설정하기 --> 다음 데이터부터 수정하기 시작
                    data['cum_volume'],
                    data['trade_sell_hoga1'],
                    data['trade_buy_hoga1']
                ]

                # 1분이 지나면 무조건 시그널을 보내지만, 이후에 데이터가 살짝 변할 수 있다. (시가 데이터는 전분 종가로 가져와서 사용하는게 더 깔끔할 수 있다)
                # 저가, 고가는 항상 같지만, 시가/종가가 조금씩 변한다.
                # RabbitMQ에서 받아오는 데이터가 무조건 순차적이라면 데이터는 완벽하다고 할 수 있다.
                last_data = self.min_mem_array[code_idx, date_idx - 1, :].reshape((7,))
                self.update_bars(
                    symbol=code,
                    date=min_date,
                    current_price=last_data[0],
                    open_price=last_data[1],
                    high=last_data[2],
                    low=last_data[3],
                    cum_volume=last_data[4],
                    trade_sell_hoga1=last_data[5],
                    trade_buy_hoga1=last_data[6]
                )
            else:
                self.min_mem_array[code_idx, date_idx, 0] = data['current_price']  # 종가는 실시간으로 업데이트
                self.min_mem_array[code_idx, date_idx, 4] = data['cum_volume']  # 거래량은 실시간으로 업데이트
                self.min_mem_array[code_idx, date_idx, 5] = data['trade_sell_hoga1']  # 호가 정보 실시간으로 업데이트
                self.min_mem_array[code_idx, date_idx, 6] = data['trade_buy_hoga1']

            if self.min_mem_array[code_idx, date_idx, 2] < data['current_price']:
                # 고가 업데이트
                self.min_mem_array[code_idx, date_idx, 2] = data['current_price']

            if self.min_mem_array[code_idx, date_idx, 3] > data['current_price']:
                # 저가 업데이트
                self.min_mem_array[code_idx, date_idx, 3] = data['current_price']
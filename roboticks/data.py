# import zmq
# import datetime
import numpy as np
import pandas as pd
from multiprocessing import shared_memory
from roboticks.event import SecondEvent
from roboticks.bar import Bar
import time

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
        print(f'Source: {source}')
        print(f'Monitoring Stocks: {monitor_stocks}\n')

        # source마다 들어오는 데이터가 다를 수 있기 때문에 소스 구분을 확실히 한다.
        self.source = source

        self.data_queues = data_queues
        self.port_queue = port_queue
        self.api_queue = api_queue

        # monitor stock list 받아서 symbol table 만들기
        self.symbol_list = monitor_stocks
        self.symbol_cnt = len(self.symbol_list)
        self.SYMBOL_TABLE = {symbol: i for i, symbol in enumerate(sorted(self.symbol_list))}
        # symbol_time_table: 최근 shared_memory에 업데이트된 시간
        self.symbol_time_table = {symbol: {'시': '08', '분': '29'} for symbol in self.symbol_list}

        # [초봉 + 호가 array 생성]
        # current_price, open_price, high, low, volume, hoga들
        second_cnt = 100
        sec_field_cnt = len(FIELD_TABLE.keys())
        self.sec_mem_shape = (int(self.symbol_cnt), int(second_cnt), int(sec_field_cnt))

        sec_array = np.zeros(self.sec_mem_shape)
        # sec_array의 초기값은 NaN이여야 한다. 그래야 연산시(ex. np.mean) 결과치가 NaN으로 나와 시그널이 무조건 나가는걸 막을수 있음
        sec_array.fill(np.nan)
        self.sec_mem_dtype = sec_array.dtype
        self.sec_mem_size = sec_array.nbytes

        self.sec_mem = shared_memory.SharedMemory(create=True, size=self.sec_mem_size)
        self.sec_mem_array = np.ndarray(shape=self.sec_mem_shape, dtype=self.sec_mem_dtype, buffer=self.sec_mem.buf)
        self.sec_mem_array[:] = sec_array[:]
        del sec_array

        print('Shared Memory array를 생성하였습니다.')
        print(f'[Second Bar Array] Memory: {self.sec_mem.name} / Shape: {self.sec_mem_shape} / Size: {self.sec_mem_size / 1e6} MBs\n')

        # ohlcv & 호가 5단계
        self.current_bar_array = np.zeros([self.symbol_cnt, len(FIELD_TABLE.keys())])
        # 들어오지않은 데이터는 NaN 값으로 처리해야함
        self.current_bar_array.fill(np.nan)
        self.start_time = None
        self.hoga_keys = list(FIELD_TABLE.keys())[FIELD_TABLE["sell_hoga1"]:]

        # # API 데이터를 소켓으로 받아올 수도 있다.
        # context = zmq.Context()
        # self.socket = context.socket(zmq.SUB)
        # self.socket.connect("tcp://localhost:5555")
        # self.socket.setsockopt_string(zmq.SUBSCRIBE, '')

    def update_second_bars(self, data, code_idx):
        # tick_data를 받아 current_bar_array 업데이트 함
        if data['type'] == 'tick':
            self.current_bar_array[code_idx][FIELD_TABLE['current_price']] = data['current_price']
            self.current_bar_array[code_idx][FIELD_TABLE['volume']] += data['volume']

            # 고가
            if self.current_bar_array[code_idx][FIELD_TABLE['high']] < data['current_price']:
                self.current_bar_array[code_idx][FIELD_TABLE['high']] = data['current_price']
            # 저가
            if self.current_bar_array[code_idx][FIELD_TABLE['low']] > data['current_price']:
                self.current_bar_array[code_idx][FIELD_TABLE['low']] = data['current_price']

        elif data['type'] == 'hoga':
            hoga_arr = np.array([data[keys] for keys in self.hoga_keys])
            self.current_bar_array[code_idx][FIELD_TABLE['sell_hoga1']:] = hoga_arr

    def initialize_second_bar(self):
        # 1초가 지나면 current_bar_array 초기화 진행
        # print("Update_second_bars: ", self.sec_mem_array)

        prev_upper = self.sec_mem_array[:, 1:, :]
        self.sec_mem_array[:, 0:-1, :] = prev_upper  # 위의 한줄을 제외하고 위로 올린다
        self.sec_mem_array[:, -1, :] = self.current_bar_array
        m_e = SecondEvent()
        self.port_queue.put(m_e)
        [q.put(m_e) for q in self.data_queues]

        cur_price_arr = self.current_bar_array[:, FIELD_TABLE['current_price']]
        cur_price_arr = cur_price_arr.reshape(self.symbol_cnt, 1)

        # shape 맞춰서 current_price로 open, high, low 초기화 해주기
        self.current_bar_array[:, :FIELD_TABLE['low'] + 1] = np.tile(cur_price_arr, (1, FIELD_TABLE['low'] + 1))

    def update_shared_memory(self, data):
        code = data['code']
        code_idx = self.SYMBOL_TABLE[code]

        if time.time() < self.start_time + 1:
            self.update_second_bars(data, code_idx)
        else:
            self.initialize_second_bar()
            # 1초지나서 들어온 tick_data는 initialize 후 업데이트
            self.update_second_bars(data, code_idx)
            # reset_time
            self.start_time = self.start_time + 1

    def start_event_loop(self):
        market_open = False
        self.start_time = time.time()
        while True:
            data = self.api_queue.get()
            # 장 중간에 시작할때는 어떻게 해야 할까?
            # if data['type'] == "Market_Open":
            #     market_open = True
            #     self.start_time = time.time()
            #     print("장시작!! : ", datetime.datetime.now())
            # elif data['type'] == "Market_Close":
            #     print("DataHandler: 장 종료")
            #     break
            market_open = True
            if market_open:
                if data['code'] in self.symbol_list:
                    # backtest할때는 전종목 데이터를 보내는 경우도 있기 때문에 필터하여 업데이트하기
                    self.update_shared_memory(data)
                else:
                    continue

        # # 초봉 업데이트(초봉이 아닌 틱봉인듯)
        # # tick/hoga 모두 업데이트해준다 (dequeue하는 방식!!)
        # if data['type'] == 'tick':
        #     # trade_date = data['trade_date']
        #     # date_idx = second_table[trade_date] --> 이제 date_idx는 없다
        #     # self.sec_mem_array[code_idx, date_idx, :2] = [data['current_price'], data['cum_volume']]
        #     prev_upper = self.tick_mem_array[code_idx, 1:, :]
        #     self.tick_mem_array[code_idx, 0:-1, :] = prev_upper # 위의 한줄을 제외하고 위로 올린다
        #     self.tick_mem_array[code_idx, -1, :] = [data['current_price'], data['cum_volume']] # 마지막줄에 새로 들어온 데이터를 넣는다
        #     print("tick")
        #     print(self.tick_mem_array)
        #     print("####################")
        # elif data['type'] == 'hoga':
        #     # trade_date = data['hoga_date']
        #     prev_upper = self.hoga_mem_array[code_idx, 1:, :]
        #     self.hoga_mem_array[code_idx, 0:-1, :] = prev_upper
        #     self.hoga_mem_array[code_idx, -1, :] = [data.get(field) if data.get(field) is not None else 0
        #                                             for field in FIELD_TABLE.keys()
        #                                             if field not in ['current_price', 'cum_volume']] # 여기 나중에 속도 Optimize 하기, 동산 Dict 페이지 참조.
        #     print("hoga")
        #     print(self.hoga_mem_array)
        #     print("####################")
        # if data['type'] == 'tick':
        #     # 분봉 업데이트
        #     # 틱데이터를 초단위로 업데이트하였다면 분단위로 업데이트도 따로 진행한다.
        #     # 분봉 업데이트는 완료후 소켓 연결로 업데이트 내용을 publish해준다.
        #     # 모든 subscriber들은 변경된 데이터를 받을 수 있다.
        #     trade_date = datetime.datetime.now() # 추가 수정 필요
        #     hour = trade_date.hour
        #     minute = trade_date.minute
        #     second = '00'
        #     min_date = f'{hour}{minute}{second}'
        #     date_idx = minute_table[min_date]
        #
        #     update_hour = self.symbol_time_table[code]['시']
        #     updated_minute = self.symbol_time_table[code]['분']
        #     updated_min_date = f'{update_hour}{updated_minute}00'
        #
        #     if (int(updated_min_date) != int(min_date)) and (int(min_date) > int(updated_min_date)):
        #         """
        #         Issue: 데이터가 순차적으로 들어오지 않으면 분봉 데이터가 꼬일 수 있다
        #                키움에서 제공하는 데이터는 초단위까지밖에 데이터를 제공하지 않기 때문에
        #                로컬에서 찍은 데이터를 기반으로 데이터를 만들 수밖에 없다.
        #         """
        #
        #         # 분이 바뀌었기 때문에 새로운 row를 추가해주는 작업
        #         self.symbol_time_table[code]['시'] = hour
        #         self.symbol_time_table[code]['분'] = minute
        #
        #         # current_price, open_price, high, low, cum_volume, trade_sell_hoga1, trade_buy_hoga1
        #         self.min_mem_array[code_idx, date_idx, :] = [
        #             data['current_price'],
        #             data['current_price'], # 시가는 종가로 설정하기
        #             data['current_price'], # 고가도 종가로 설정하기
        #             data['current_price'], # 저가도 종가로 설정하기 --> 다음 데이터부터 수정하기 시작
        #             data['cum_volume'],
        #             data['trade_sell_hoga1'],
        #             data['trade_buy_hoga1']
        #         ]
        #
        #         # 1분이 지나면 무조건 시그널을 보내지만, 이후에 데이터가 살짝 변할 수 있다. (시가 데이터는 전분 종가로 가져와서 사용하는게 더 깔끔할 수 있다)
        #         # 저가, 고가는 항상 같지만, 시가/종가가 조금씩 변한다.
        #         # RabbitMQ에서 받아오는 데이터가 무조건 순차적이라면 데이터는 완벽하다고 할 수 있다.
        #         last_data = self.min_mem_array[code_idx, date_idx - 1, :].reshape((7,))
        #         self.update_minute_bars(
        #             symbol=code,
        #             date=min_date,
        #             current_price=last_data[0],
        #             open_price=last_data[1],
        #             high=last_data[2],
        #             low=last_data[3],
        #             cum_volume=last_data[4],
        #             trade_sell_hoga1=last_data[5],
        #             trade_buy_hoga1=last_data[6]
        #         )
        #     else:
        #         self.min_mem_array[code_idx, date_idx, 0] = data['current_price']  # 종가는 실시간으로 업데이트
        #         self.min_mem_array[code_idx, date_idx, 4] = data['cum_volume']  # 거래량은 실시간으로 업데이트
        #         self.min_mem_array[code_idx, date_idx, 5] = data['trade_sell_hoga1']  # 호가 정보 실시간으로 업데이트
        #         self.min_mem_array[code_idx, date_idx, 6] = data['trade_buy_hoga1']
        #
        #     if self.min_mem_array[code_idx, date_idx, 2] < data['current_price']:
        #         # 고가 업데이트
        #         self.min_mem_array[code_idx, date_idx, 2] = data['current_price']
        #
        #     if self.min_mem_array[code_idx, date_idx, 3] > data['current_price']:
        #         # 저가 업데이트
        #         self.min_mem_array[code_idx, date_idx, 3] = data['current_price']
